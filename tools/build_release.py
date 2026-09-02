#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build centralizado do RD Devices.

A versao de QUALQUER compilacao vem de version_info.txt (raiz). --bump none
compila exatamente essa versao; --bump {build|patch|minor|major} incrementa a
partir dela e reescreve version_info.txt. COLETOR/version.py e
INTEGRADOR/version.py sao sempre alinhados a version_info.txt no inicio do build.

Exemplos:
  python tools/build_release.py --component all --bump none --build-type onefile
  python tools/build_release.py --component all --bump build --build-type onefile --sign
  python tools/build_release.py --component coletor --bump none
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROJECT_NAME = "RD_DEVICES"
PROJECT_RELEASE_DIR = Path(os.environ.get("PROJECT_RELEASE", "C:/DESENV/PROJECT_RELEASE"))
PROJECT_BACKUP_DIR = Path(os.environ.get("PROJECT_BACKUP", "C:/DESENV/PROJECT_BACKUP"))
VENV_DIR = ROOT / ".venv"
VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe" if os.name == "nt" else VENV_DIR / "bin" / "python"
TEMPLATE = ROOT / "tools" / "version_template.py.in"
RUNTIME_DIRS = ("config", "database", "logs")
SIGN_CERT = ROOT / "tools" / "certs" / "quallit_codesign.pfx"
# Config de publicacao (--publish): papeis [deploy_server]/[storage_server]/
# [download_server] + perfis de servidor fisico. Credenciais so aqui, nunca no script.
DOWNLOAD_SERVER_CONFIG = ROOT / "config" / "config.ini"
# Nome fixo do pacote no download server (URL de download estavel).
COLETOR_DOWNLOAD_ZIP_NAME = "RD-COLETOR.zip"
TIMESTAMP_URL = "http://timestamp.digicert.com"
REQUIREMENTS_FILES = (
    ROOT / "COLETOR" / "requirements.txt",
    ROOT / "INTEGRADOR" / "requirements.txt",
)
BUILD_IMPORT_CHECKS = (
    ("PyInstaller", "PyInstaller"),
    ("paramiko", "paramiko"),
    ("cryptography", "cryptography"),
    ("xlrd", "xlrd"),
    ("mysql.connector", "mysql-connector-python"),
    ("pysnmp", "pysnmp"),
)
WINDOWS_IMPORT_CHECKS = (
    ("win32api", "pywin32"),
    ("wmi", "WMI"),
)
EXE_METADATA = {
    "coletor": {
        "company_name": "Quallit",
        "product_name": "Preventiva Coletor",
        "file_description": "Preventiva Coletor",
        "original_filename": "Coletor.exe",
        "legal_copyright": "(c) Quallit - Todos os direitos reservados",
    },
    "integrador": {
        "company_name": "Quallit",
        "product_name": "Preventiva Integrador",
        "file_description": "Preventiva Integrador",
        "original_filename": "Integrador.exe",
        "legal_copyright": "(c) Quallit - Todos os direitos reservados",
    },
}


@dataclass
class Component:
    key: str
    name: str
    root: Path
    entrypoint: Path
    version_file: Path
    windowed: bool


COMPONENTS = {
    "coletor": Component(
        key="coletor",
        name="COLETOR",
        root=ROOT / "COLETOR",
        entrypoint=ROOT / "COLETOR" / "main.py",
        version_file=ROOT / "COLETOR" / "version.py",
        windowed=True,
    ),
    "integrador": Component(
        key="integrador",
        name="INTEGRADOR",
        root=ROOT / "INTEGRADOR",
        entrypoint=ROOT / "INTEGRADOR" / "main.py",
        version_file=ROOT / "INTEGRADOR" / "version.py",
        windowed=True,
    ),
}


VERSION_RE = re.compile(r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?"')
BUILD_RE = re.compile(r"__build__\s*=\s*(\d+)")
DEFAULT_SIGN_PASSWORD = "QuallitRDAssist_Password"

# Fonte unica da versao para QUALQUER compilacao: version_info.txt na raiz.
# COLETOR/version.py e INTEGRADOR/version.py sao derivados dela a cada build.
PROJECT_VERSION_FILE = ROOT / "version_info.txt"
PROJECT_VERSION_RE = re.compile(
    r"(?im)^\s*vers[aã]o\s*[:=]\s*v?(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?\s*$"
)


def read_version(path: Path):
    text = path.read_text(encoding="utf-8")
    version_match = VERSION_RE.search(text)
    if not version_match:
        raise RuntimeError(f"Versão não encontrada em {path}")
    major, sequence, month = (int(part) for part in version_match.groups()[:3])
    year2 = int(version_match.group(4) or date.today().year % 100)
    return major, sequence, month, year2


def read_project_version():
    """Versao de referencia do projeto, lida de version_info.txt (raiz).

    Toda compilacao parte desta versao; um --bump incrementa a partir dela e
    reescreve o arquivo. Se o arquivo faltar ou nao tiver uma linha
    'Versao: X.Y.MM.AA', o build para (ela e a fonte unica)."""
    if not PROJECT_VERSION_FILE.exists():
        raise RuntimeError(
            f"version_info.txt nao encontrado em {PROJECT_VERSION_FILE} "
            "(fonte unica da versao para o build)."
        )
    match = PROJECT_VERSION_RE.search(PROJECT_VERSION_FILE.read_text(encoding="utf-8"))
    if not match:
        raise RuntimeError(
            f"Linha 'Versao: X.Y.MM.AA' nao encontrada em {PROJECT_VERSION_FILE}."
        )
    major, sequence, month = (int(part) for part in match.groups()[:3])
    year2 = int(match.group(4) or date.today().year % 100)
    return major, sequence, month, year2


def write_project_version(version):
    """Grava a versao de volta em version_info.txt (usado apos um --bump)."""
    PROJECT_VERSION_FILE.write_text(
        f"Versao: {format_version(version)}\n"
        f"Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n",
        encoding="utf-8",
    )


def bump_version(version, bump):
    major, sequence, _month, _year2 = version
    current_month = date.today().month
    current_year2 = date.today().year % 100
    if bump == "major":
        return major + 1, 1, current_month, current_year2
    if bump in ("minor", "patch", "build"):
        return major, sequence + 1, current_month, current_year2
    return version


def format_version(version):
    major, sequence, month, year2 = version
    return f"{major}.{sequence:02d}.{month:02d}.{year2:02d}"


def format_release_label(component_versions):
    if not component_versions:
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    if len(component_versions) == 1:
        _name, version = component_versions[0]
        return version
    return "_".join(f"{name}-{version}" for name, version in component_versions)


def write_version(component: Component, version):
    major, sequence, month, year2 = version
    version_text = format_version(version)
    rendered = TEMPLATE.read_text(encoding="utf-8").format(
        component=component.name,
        version=version_text,
        major=major,
        sequence=sequence,
        month=month,
        year2=year2,
        date=date.today().isoformat(),
    )
    component.version_file.write_text(rendered, encoding="utf-8")

    if component.key == "coletor":
        init_file = component.root / "src" / "__init__.py"
        init_file.write_text(
            '"""\nCOLETOR - RD Devices Collector\nPacote principal da aplicação.\n"""\n\n'
            f'__version__ = "{version_text}"\n',
            encoding="utf-8",
        )


def generate_version_file(component: Component, version) -> Path:
    """Gera VSVersionInfo usado pelo PyInstaller nos metadados do exe."""
    version_text = format_version(version)
    ver_parts = tuple(int(part) for part in version_text.split("."))
    build_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    output_path = ROOT / "tools" / f"file_version_info_{component.name}.txt"
    metadata = EXE_METADATA.get(component.key, {})
    company_name = metadata.get("company_name", "Quallit")
    description = metadata.get("file_description", component.name)
    internal_name = component.name
    original_filename = metadata.get("original_filename", f"{component.name}.exe")
    product_name = metadata.get("product_name", component.name)
    legal_copyright = metadata.get(
        "legal_copyright", "(c) Quallit - Todos os direitos reservados"
    )

    output_path.write_text(
        f'''# -*- coding: utf-8 -*-
VSVersionInfo(
  ffi=FixedFileInfo(
    mask=0x3f,
    filevers={ver_parts},
    prodvers={ver_parts},
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[StringFileInfo([
    StringTable(u'041604E4', [
      StringStruct(u'CompanyName', u'{company_name}'),
      StringStruct(u'FileDescription', u'{description}'),
      StringStruct(u'FileVersion', u'{version_text}'),
      StringStruct(u'InternalName', u'{internal_name}'),
      StringStruct(u'LegalCopyright', u'{legal_copyright}'),
      StringStruct(u'OriginalFilename', u'{original_filename}'),
      StringStruct(u'ProductName', u'{product_name}'),
      StringStruct(u'ProductVersion', u'{version_text}'),
      StringStruct(u'BuildDate', u'{build_date}'),
      StringStruct(u'BuildComponent', u'{component.key}')
    ])
  ]), VarFileInfo([VarStruct(u'Translation', [1046, 1252])])
  ]
)
''',
        encoding="utf-8",
    )
    return output_path


def component_list(selected):
    if selected == "all":
        return [COMPONENTS["coletor"], COMPONENTS["integrador"]]
    return [COMPONENTS[selected]]


def is_root_venv_python() -> bool:
    try:
        return Path(sys.executable).resolve() == VENV_PYTHON.resolve()
    except OSError:
        return False


def ensure_venv():
    created = False
    if not VENV_PYTHON.exists():
        print(f"[VENV] Criando ambiente virtual em {VENV_DIR}")
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        created = True

    if not VENV_PYTHON.exists():
        raise RuntimeError(f"Python do venv nao encontrado: {VENV_PYTHON}")

    if not is_root_venv_python():
        print(f"[VENV] Reiniciando build com {VENV_PYTHON}")
        env = os.environ.copy()
        env["RD_DEVICES_BUILD_VENV_READY"] = "1"
        result = subprocess.run([str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]], env=env)
        raise SystemExit(result.returncode)

    print(f"[VENV] Usando {VENV_PYTHON}")
    if created:
        sync_dependencies(force=True)


def missing_imports():
    checks = list(BUILD_IMPORT_CHECKS)
    if os.name == "nt":
        checks.extend(WINDOWS_IMPORT_CHECKS)
    missing = []
    for module_name, package_name in checks:
        result = subprocess.run(
            [sys.executable, "-c", f"import {module_name}"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            missing.append(package_name)
    return missing


def sync_dependencies(force: bool = False):
    missing = missing_imports()
    if not force and not missing:
        print("[VENV] Dependencias verificadas.")
        return

    if missing:
        print(f"[VENV] Dependencias ausentes: {', '.join(sorted(set(missing)))}")
    else:
        print("[VENV] Ambiente novo; sincronizando requirements.")

    cmd = [sys.executable, "-m", "pip", "install"]
    for req in REQUIREMENTS_FILES:
        if req.exists():
            cmd.extend(["-r", str(req)])
    print(f"[VENV] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT, text=True)
    if result.returncode != 0:
        raise RuntimeError("Falha ao instalar dependencias do build.")

    still_missing = missing_imports()
    if still_missing:
        raise RuntimeError(
            "Dependencias ainda ausentes apos instalacao: "
            + ", ".join(sorted(set(still_missing)))
        )
    print("[VENV] Dependencias prontas.")


def app_output_dir(component: Component, build_type: str) -> Path:
    if build_type == "onedir":
        return component.root / "dist" / component.name
    return component.root / "dist"


def snapshot_runtime(component: Component) -> Path | None:
    preserve_root = ROOT / "temp" / f"build_preserve_{component.key}"
    if preserve_root.exists():
        shutil.rmtree(preserve_root)

    candidates = [
        component.root / "dist" / component.name,
        component.root / "dist",
    ]
    copied = False
    preserve_root.mkdir(parents=True, exist_ok=True)

    for candidate in candidates:
        if not candidate.exists():
            continue
        for name in RUNTIME_DIRS:
            source = candidate / name
            target = preserve_root / name
            if source.exists() and not target.exists():
                if source.is_dir():
                    shutil.copytree(source, target)
                else:
                    shutil.copy2(source, target)
                copied = True

    if not copied:
        shutil.rmtree(preserve_root)
        return None
    return preserve_root


def restore_runtime(component: Component, build_type: str, preserve_root: Path | None):
    if preserve_root is None:
        return
    target_root = app_output_dir(component, build_type)
    target_root.mkdir(parents=True, exist_ok=True)
    for name in RUNTIME_DIRS:
        source = preserve_root / name
        target = target_root / name
        if source.exists() and not target.exists():
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)
        elif source.is_dir() and target.is_dir():
            for child in source.rglob("*"):
                rel = child.relative_to(source)
                if (
                    component.key == "coletor"
                    and name == "config"
                    and rel == Path("schema_sqlite_init.sql")
                ):
                    continue
                child_target = target / rel
                if child.is_dir():
                    child_target.mkdir(parents=True, exist_ok=True)
                elif not child_target.exists():
                    child_target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(child, child_target)
    shutil.rmtree(preserve_root)


def seed_runtime_layout(component: Component, build_type: str):
    target_root = app_output_dir(component, build_type)
    for name in RUNTIME_DIRS:
        (target_root / name).mkdir(parents=True, exist_ok=True)

    if component.key == "coletor":
        config_ini = target_root / "config" / "config.ini"
        source_schema = component.root / "config" / "schema_sqlite_init.sql"
        duplicate_schema = target_root / "config" / "schema_sqlite_init.sql"
        shutil.copy2(
            component.root / "config.ini.template",
            target_root / "config" / "config.ini.template",
        )
        if not config_ini.exists():
            shutil.copy2(component.root / "config.ini.template", config_ini)
        if (
            duplicate_schema.exists()
            and duplicate_schema.read_bytes() == source_schema.read_bytes()
        ):
            duplicate_schema.unlink()
    elif (component.root / "config.ini.template").exists():
        config_ini = target_root / "config" / "config.ini"
        shutil.copy2(
            component.root / "config.ini.template",
            target_root / "config" / "config.ini.template",
        )
        if not config_ini.exists():
            shutil.copy2(component.root / "config.ini.template", config_ini)


_PYCACHE_SKIP_DIRS = {".venv", ".venv-win7", "venv", ".git", ".specstory"}


def clean_pycache(root: Path):
    removed_dirs = 0
    removed_files = 0
    for cache_dir in root.rglob("__pycache__"):
        if cache_dir.is_dir():
            shutil.rmtree(cache_dir)
            removed_dirs += 1
    for pattern in ("*.pyc", "*.pyo"):
        for file_path in root.rglob(pattern):
            if file_path.is_file():
                file_path.unlink()
                removed_files += 1
    if removed_dirs or removed_files:
        print(f"[CLEAN] {root.name}: {removed_dirs} __pycache__, {removed_files} bytecode removidos")


def clean_pycache_project(label: str):
    """Varre TODO o repositorio (exceto .venv/.git/...) removendo __pycache__ e
    bytecode. Chamado no inicio e no fim de cada execucao do build."""
    removed_dirs = removed_files = 0
    for cache_dir in ROOT.rglob("__pycache__"):
        if not cache_dir.is_dir():
            continue
        if _PYCACHE_SKIP_DIRS & set(cache_dir.relative_to(ROOT).parts):
            continue
        shutil.rmtree(cache_dir, ignore_errors=True)
        removed_dirs += 1
    for pattern in ("*.pyc", "*.pyo"):
        for file_path in ROOT.rglob(pattern):
            if not file_path.is_file():
                continue
            if _PYCACHE_SKIP_DIRS & set(file_path.relative_to(ROOT).parts):
                continue
            try:
                file_path.unlink()
                removed_files += 1
            except OSError:
                pass
    print(f"[CLEAN] {label}: {removed_dirs} __pycache__ e {removed_files} bytecode "
          "removidos no repo (exceto .venv/.git).")


def clean(component: Component, build_type: str, phase: str = "pre"):
    print(f"[CLEAN] Limpando artefatos de build de {component.name} ({phase})")
    for item in (component.root / "build",):
        if item.exists():
            shutil.rmtree(item)
            print(f"[CLEAN] Removido {item}")
    for spec in component.root.glob("*.spec"):
        spec.unlink()
        print(f"[CLEAN] Removido {spec}")
    clean_pycache(component.root)

    if phase != "pre":
        return

    dist_root = component.root / "dist"
    exe_path = dist_root / f"{component.name}.exe"
    stale_onedir = dist_root / component.name
    if exe_path.exists():
        exe_path.unlink()
        print(f"[CLEAN] Removido {exe_path}")
    if build_type == "onedir" and stale_onedir.exists():
        shutil.rmtree(stale_onedir)
        print(f"[CLEAN] Removido {stale_onedir}")
    elif build_type == "onefile" and stale_onedir.exists():
        shutil.rmtree(stale_onedir)
        print(f"[CLEAN] Removido artefato onedir antigo {stale_onedir}")


def pyinstaller_cmd(component: Component, build_type: str, version_file: Path | None = None):
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        f"--{build_type}",
        "--name",
        component.name,
        "--clean",
        "--noconfirm",
    ]
    cmd.append("--windowed" if component.windowed else "--console")
    if version_file is not None:
        cmd.extend(["--version-file", str(version_file.resolve())])

    if component.key == "coletor":
        cmd.extend(
            [
                "--add-data",
                f"config.ini.template{os.pathsep}.",
                "--add-data",
                f"config/schema_sqlite_init.sql{os.pathsep}config",
                "--add-data",
                f"docs{os.pathsep}docs",
                "--paths",
                str(component.root / "src"),
                "--hidden-import=tabs.tab_0_database",
                "--hidden-import=tabs.tab_1_import_xls",
                "--hidden-import=tabs.tab_2_ssh",
                "--hidden-import=tabs.tab_3_devices",
                "--hidden-import=tabs.tab_4_hardware",
                "--hidden-import=tabs.tab_5_rescan",
                "--hidden-import=tabs.tab_6_credentials",
                "--hidden-import=common.secure_store",
                "--hidden-import=wmi",
                "--hidden-import=pysnmp.hlapi.asyncio",
            ]
        )
    else:
        cmd.extend(
            [
                "--add-data",
                f"config.ini.template{os.pathsep}.",
                "--add-data",
                f"docs{os.pathsep}docs",
                "--paths",
                str(component.root / "src"),
                "--hidden-import=secure_store",
                "--hidden-import=version",
                "--hidden-import=tabs.tab_0_config",
                "--hidden-import=tabs.tab_1_import",
                "--hidden-import=tabs.tab_2_count",
                "--hidden-import=tabs.tab_3_view_sqlite",
                "--hidden-import=tabs.tab_4_view_mariadb",
                "--hidden-import=tabs.tab_5_view_compare",
                "--hidden-import=common.config",
                "--hidden-import=common.console_logger",
                "--hidden-import=common.treeview_sort",
                "--hidden-import=common.runtime_paths",
            ]
        )

    cmd.append(str(component.entrypoint))
    return cmd


def build(component: Component, build_type: str, version, sign: bool = False):
    preserved = snapshot_runtime(component)
    clean(component, build_type, phase="pre")
    version_file = generate_version_file(component, version)
    print(f"[VERSION-FILE] {version_file}")
    cmd = pyinstaller_cmd(component, build_type, version_file)
    print(f"[BUILD] {component.name}: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=component.root, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Build falhou para {component.name}")
        seed_runtime_layout(component, build_type)
        restore_runtime(component, build_type, preserved)
        exe_path = app_output_dir(component, build_type) / f"{component.name}.exe"
        display_exe_metadata(exe_path)
        if sign:
            sign_executable(exe_path)
            display_signature_status(exe_path)
        else:
            print("[SIGN] Assinatura pulada (sem --sign)")
        clean(component, build_type, phase="post")
        return exe_path
    except Exception:
        restore_runtime(component, build_type, preserved)
        raise


def find_signtool() -> str | None:
    signtool_env = os.environ.get("SIGNTOOL_PATH", "").strip()
    if signtool_env and Path(signtool_env).exists():
        return signtool_env

    candidates = [
        Path(r"C:\Program Files (x86)\Windows Kits\10\bin"),
        Path(r"C:\Program Files\Windows Kits\10\bin"),
        Path(r"C:\Program Files (x86)\Windows Kits\8.1\bin"),
    ]
    found = []
    for root in candidates:
        if root.exists():
            found.extend(root.glob(r"*\x64\signtool.exe"))
            found.extend(root.glob(r"*\x86\signtool.exe"))
    if found:
        return str(sorted(found, key=lambda p: str(p), reverse=True)[0])

    where_res = subprocess.run(["where", "signtool"], capture_output=True, text=True)
    if where_res.returncode == 0:
        for line in where_res.stdout.splitlines():
            candidate = line.strip()
            if candidate and Path(candidate).exists():
                return candidate
    return None


def sign_password() -> str:
    for name in ("QUALLIT_SIGN_PASSWORD", "QUALLIT_CODESIGN_PASSWORD", "RD_DEVICES_SIGN_PASSWORD"):
        value = os.environ.get(name, "")
        if value:
            return value
    return DEFAULT_SIGN_PASSWORD


def sign_executable(exe_path: Path) -> bool:
    if not exe_path.exists():
        print(f"[SIGN] Executável não encontrado: {exe_path}")
        return False
    signtool = find_signtool()
    if not signtool:
        print("[SIGN] signtool.exe não encontrado; assinatura pulada")
        return False

    password = sign_password()
    if SIGN_CERT.exists() and password:
        cmd = [
            signtool,
            "sign",
            "/f",
            str(SIGN_CERT),
            "/p",
            password,
            "/fd",
            "SHA256",
            "/t",
            TIMESTAMP_URL,
            str(exe_path),
        ]
        print(f"[SIGN] Assinando com PFX: {SIGN_CERT}")
    else:
        cmd = [
            signtool,
            "sign",
            "/fd",
            "SHA256",
            "/a",
            "/t",
            TIMESTAMP_URL,
            str(exe_path),
        ]
        reason = "senha ausente" if SIGN_CERT.exists() else "PFX ausente"
        print(f"[SIGN] Assinando por store local (/a), motivo: {reason}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("[SIGN] Executável assinado com sucesso")
        return True
    print("[SIGN] Falha na assinatura")
    if result.stderr.strip():
        print(result.stderr.strip())
    elif result.stdout.strip():
        print(result.stdout.strip())
    return False


def read_exe_metadata(exe_path: Path) -> str | None:
    if not exe_path.exists():
        return None
    ps_cmd = (
        f"$v = (Get-Item '{exe_path}').VersionInfo; "
        "'CompanyName={0}; ProductName={1}; FileDescription={2}; ProductVersion={3}; FileVersion={4}; "
        "LegalCopyright={5}; OriginalFilename={6}' -f "
        "$v.CompanyName, $v.ProductName, $v.FileDescription, $v.ProductVersion, $v.FileVersion, "
        "$v.LegalCopyright, $v.OriginalFilename"
    )
    result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def display_exe_metadata(exe_path: Path):
    metadata = read_exe_metadata(exe_path)
    if metadata:
        print(f"[META] {metadata}")
    elif not exe_path.exists():
        print(f"[META] Executável não encontrado: {exe_path}")
    else:
        print("[META] Não foi possível ler metadados do executável")


def display_signature_status(exe_path: Path):
    ps_cmd = (
        f"$s = Get-AuthenticodeSignature -FilePath '{exe_path}'; "
        "'Status={0}; Subject={1}; Thumbprint={2}' -f $s.Status, $s.SignerCertificate.Subject, $s.SignerCertificate.Thumbprint"
    )
    result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip():
        print(f"[SIGN] {result.stdout.strip()}")
    else:
        print("[SIGN] Não foi possível ler status da assinatura")


def display_build_summary(exe_paths):
    if not exe_paths:
        return
    print("")
    print("[SUMMARY] Executaveis gerados")
    for exe_path in exe_paths:
        print(f"[SUMMARY] Arquivo: {exe_path}")
        metadata = read_exe_metadata(exe_path)
        if metadata:
            print(f"[SUMMARY] Metadata: {metadata}")
        else:
            print("[SUMMARY] Metadata: indisponivel")
        display_signature_status(exe_path)


def zip_size_mb(zip_path: Path) -> float:
    return zip_path.stat().st_size / (1024 * 1024)


# Segredos e dados locais que nunca devem entrar nos pacotes RELEASE/BACKUP.
# Espelha o bloco "Configuracoes locais e segredos" do .gitignore da raiz.
SECRET_FILE_SUFFIXES = (".db", ".sqlite", ".sqlite3", ".key")


def is_local_secret_file(file_path: Path) -> bool:
    name = file_path.name
    lower = name.lower()
    if lower.endswith(SECRET_FILE_SUFFIXES):
        return True
    if name == "config.ini" or re.match(r"^config\..+\.ini$", name):
        return True
    if name == "config.web.php":
        return True
    if ".OK_" in name or lower.endswith((".bak", ".orig")):
        return True
    return False


def create_release_zip(component_versions, components):
    PROJECT_RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    version_label = format_release_label(component_versions)
    zip_path = PROJECT_RELEASE_DIR / f"{PROJECT_NAME}_RELEASE-{version_label}-{date_str}.zip"
    if zip_path.exists():
        zip_path.unlink()

    file_count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for component in components:
            dist_dir = component.root / "dist"
            if not dist_dir.exists():
                print(f"[ZIP] AVISO: dist nao encontrado para {component.name}: {dist_dir}")
                continue
            for file_path in dist_dir.rglob("*"):
                if not file_path.is_file():
                    continue
                rel_in_dist = file_path.relative_to(dist_dir)
                # Nao empacotar segredos/dados locais nem runtime transitorio
                # (logs, banco). O pacote leva so o binario e os *.template.
                if is_local_secret_file(file_path):
                    print(f"[ZIP] Ignorado (segredo/dado local): {rel_in_dist}")
                    continue
                if file_path.suffix.lower() == ".log" or "logs" in {p.lower() for p in rel_in_dist.parts}:
                    continue
                # Achata "dist/" no ZIP: COLETOR/dist/COLETOR.exe -> COLETOR/COLETOR.exe
                arcname = Path(component.name) / rel_in_dist
                zf.write(file_path, arcname)
                file_count += 1

    print(f"[ZIP] RELEASE: {zip_path.name} ({file_count} arquivos, {zip_size_mb(zip_path):.1f} MB)")
    return zip_path


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except Exception:
        return False


def _backup_excluded_roots() -> tuple[Path, ...]:
    roots = []
    for candidate in (PROJECT_RELEASE_DIR, PROJECT_BACKUP_DIR):
        if _is_relative_to(candidate, ROOT):
            roots.append(candidate.resolve())
    return tuple(roots)


def should_exclude_backup_file(file_path: Path, output_zip: Path | None = None):
    rel = file_path.relative_to(ROOT)
    parts = {part.lower() for part in rel.parts}
    excluded_dirs = {
        ".git", ".venv", ".venv-win7", "venv",
        "__pycache__", ".specstory", ".vs", ".idea",
        "dist", "build", "temp", "logs",
        "build_win7_tmp", "build_win7_tmp_final",
    }
    if parts & excluded_dirs:
        return True

    excluded_exts = {".pyc", ".pyo", ".spec", ".log", ".tmp", ".pfx", ".p12", ".cer"}
    if file_path.suffix.lower() in excluded_exts:
        return True

    if is_local_secret_file(file_path):
        return True

    excluded_files = {
        Path("tools/git/github_sync.ini"),
    }

    if rel in excluded_files:
        return True

    resolved_file = file_path.resolve()
    for excluded_root in _backup_excluded_roots():
        if _is_relative_to(resolved_file, excluded_root):
            return True

    if output_zip is not None and resolved_file == output_zip.resolve():
        return True

    return False


def create_backup_zip(component_versions):
    PROJECT_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    version_label = format_release_label(component_versions)
    zip_path = PROJECT_BACKUP_DIR / f"{PROJECT_NAME}_BACKUP-{version_label}-{date_str}.zip"
    if zip_path.exists():
        zip_path.unlink()

    file_count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in ROOT.rglob("*"):
            if not file_path.is_file() or should_exclude_backup_file(file_path, output_zip=zip_path):
                continue
            arcname = Path(ROOT.name) / file_path.relative_to(ROOT)
            zf.write(file_path, arcname)
            file_count += 1

    print(f"[ZIP] BACKUP: {zip_path.name} ({file_count} arquivos, {zip_size_mb(zip_path):.1f} MB)")
    return zip_path


def display_zip_summary(zip_paths):
    if not zip_paths:
        return
    print("")
    print("[SUMMARY] Pacotes ZIP")
    for zip_path in zip_paths:
        print(f"[SUMMARY] ZIP: {zip_path} ({zip_size_mb(zip_path):.1f} MB)")


# ---------------------------------------------------------------------------
# Publicacao no download server (--publish)
# ---------------------------------------------------------------------------

def _decode_secret(value: str) -> str:
    """Senha do config.ini: prefixo 'b64:' (base64) ou texto puro."""
    value = (value or "").strip()
    if value.startswith("b64:"):
        import base64
        try:
            return base64.b64decode(value[4:]).decode("utf-8", "replace")
        except Exception:
            return ""
    return value


def read_download_server_config():
    """Le a config de publicacao de `config/config.ini` (raiz do repo).

    Estrutura por papel + perfil: a secao [download_server] tem `enabled`,
    `active_profile`, `protocol`, `remote_dir`, `file_name` e `public_base_url`;
    `active_profile` aponta para uma secao de servidor fisico ([dell]/[vmware1]/
    ...) com host/port/user/auth/password/key_file.

    Retorna dict resolvido, ou None se o arquivo/secao nao existir ou
    enabled for falso. As credenciais moram SO neste config.ini (fora do
    versionamento); o script nunca as carrega hardcoded.
    """
    import configparser

    if not DOWNLOAD_SERVER_CONFIG.exists():
        print(f"[PUBLISH] config nao encontrado: {DOWNLOAD_SERVER_CONFIG}")
        return None
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(DOWNLOAD_SERVER_CONFIG, encoding="utf-8")
    if not parser.has_section("download_server"):
        print(f"[PUBLISH] Secao [download_server] ausente em {DOWNLOAD_SERVER_CONFIG}")
        return None
    role = parser["download_server"]
    if not role.getboolean("enabled", fallback=False):
        print("[PUBLISH] [download_server] enabled=0 - publicacao ignorada")
        return None

    protocol = (role.get("protocol", "sftp") or "sftp").strip().lower()
    remote_dir = role.get("remote_dir", "").strip()
    file_name = (role.get("file_name", "") or "").strip() or COLETOR_DOWNLOAD_ZIP_NAME
    public_base_url = role.get("public_base_url", role.get("public_url_base", "")).strip()

    cfg = {
        "protocol": protocol,
        "remote_dir": remote_dir,
        "file_name": file_name,
        "public_base_url": public_base_url.rstrip("/"),
        "dest_dir": role.get("dest_dir", "").strip(),
        "host": "", "port": 22, "user": "", "password": "", "key_file": "",
    }

    if protocol == "local":
        return cfg

    profile_name = (role.get("active_profile", "") or "").strip()
    if not profile_name:
        print("[PUBLISH] [download_server] sem active_profile")
        return None
    if not parser.has_section(profile_name):
        print(f"[PUBLISH] perfil de servidor [{profile_name}] ausente em {DOWNLOAD_SERVER_CONFIG}")
        return None
    prof = parser[profile_name]
    cfg.update({
        "profile": profile_name,
        "host": prof.get("host", "").strip(),
        "port": prof.getint("port", fallback=22),
        "user": prof.get("user", "").strip(),
        "password": _decode_secret(prof.get("password", "")),
        "key_file": prof.get("key_file", "").strip(),
    })
    return cfg


def create_coletor_download_zip():
    """Pacote de nome fixo para o download server: sempre `RD-COLETOR.zip`,
    contendo APENAS `COLETOR.exe`.

    O executavel embute `config.ini.template` (com as credenciais padrao) e, na
    1a execucao, `ensure_default_config()` gera `config/config.ini` a partir
    dele. Empacotar um `config.ini` junto so atrapalharia: se ele ja existisse
    ao descompactar, o app nao recriaria o correto."""
    coletor = COMPONENTS["coletor"]
    exe = coletor.root / "dist" / ("COLETOR.exe" if os.name == "nt" else "COLETOR")
    if not exe.exists():
        print(f"[PUBLISH] AVISO: executavel do COLETOR nao encontrado: {exe}")
        return None
    PROJECT_RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = PROJECT_RELEASE_DIR / COLETOR_DOWNLOAD_ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(exe, "COLETOR.exe")
    print(f"[PUBLISH] Pacote: {zip_path.name} ({zip_size_mb(zip_path):.1f} MB) [somente COLETOR.exe]")
    return zip_path


def _sftp_makedirs(sftp, remote_dir: str):
    remote_dir = remote_dir.replace("\\", "/")
    absolute = remote_dir.startswith("/")
    parts, acc = [p for p in remote_dir.split("/") if p], ""
    for part in parts:
        acc = (acc + "/" + part) if acc or absolute else part
        try:
            sftp.stat(acc)
        except IOError:
            sftp.mkdir(acc)


def publish_to_download_server(zip_path: Path, cfg: dict) -> bool:
    """Envia o pacote com o nome fixo `cfg['file_name']` conforme [download_server].

    protocol: 'scp'/'sftp' (paramiko SFTP) ou 'local' (copia para dest_dir).
    """
    protocol = cfg["protocol"]
    remote_name = cfg["file_name"]
    if protocol == "local":
        dest_dir = Path(cfg["dest_dir"] or cfg["remote_dir"])
        if not str(dest_dir).strip():
            print("[PUBLISH] protocol=local exige dest_dir/remote_dir em [download_server]")
            return False
        dest_dir.mkdir(parents=True, exist_ok=True)
        target = dest_dir / remote_name
        shutil.copy2(zip_path, target)
        print(f"[PUBLISH] Copiado para {target}")
    elif protocol in ("sftp", "scp"):
        try:
            import paramiko
        except ImportError:
            print("[PUBLISH] paramiko ausente - instale para publicar via SFTP/SCP")
            return False
        if not (cfg["host"] and cfg["user"]):
            print("[PUBLISH] host/user ausentes (verifique active_profile em [download_server])")
            return False
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            connect_kwargs = dict(
                hostname=cfg["host"], port=cfg["port"], username=cfg["user"],
                timeout=20, allow_agent=False, look_for_keys=False,
            )
            key_file = cfg.get("key_file", "")
            if key_file and Path(key_file).exists():
                connect_kwargs["key_filename"] = key_file
            else:
                connect_kwargs["password"] = cfg["password"] or None
            client.connect(**connect_kwargs)
            sftp = client.open_sftp()
            remote_dir = cfg["remote_dir"] or "."
            if remote_dir not in (".", ""):
                _sftp_makedirs(sftp, remote_dir)
            remote_path = f"{remote_dir.rstrip('/')}/{remote_name}"
            sftp.put(str(zip_path), remote_path)
            sftp.close()
            print(f"[PUBLISH] Enviado ({protocol}): {cfg['user']}@{cfg['host']}:{remote_path}")
        except Exception as exc:
            print(f"[PUBLISH] Falha no envio: {exc}")
            return False
        finally:
            client.close()
    else:
        print(f"[PUBLISH] protocolo nao suportado: {protocol}")
        return False
    if cfg["public_base_url"]:
        print(f"[PUBLISH] URL: {cfg['public_base_url']}/{remote_name}")
    return True


def publish_coletor_package(target_versions):
    """Linha de publicacao do pipeline: monta o ZIP do COLETOR e envia ao
    download server (credenciais em COLETOR/config/config.ini [download_server])."""
    print("")
    print("[PUBLISH] Publicando pacote COLETOR no download server")
    if "coletor" not in target_versions:
        print("[PUBLISH] COLETOR fora do conjunto compilado (use --component all|coletor) - pulado")
        return False
    srv = read_download_server_config()
    if not srv:
        return False
    coletor_zip = create_coletor_download_zip()
    if not coletor_zip:
        return False
    ok = publish_to_download_server(coletor_zip, srv)
    print(f"[PUBLISH] Resultado: {'OK' if ok else 'FALHOU'}")
    return ok


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Build centralizado do COLETOR e INTEGRADOR")
    parser.add_argument("--component", choices=("coletor", "integrador", "all"), default="all")
    parser.add_argument("--bump", choices=("major", "minor", "patch", "build", "none"), default="build")
    parser.add_argument("--build-type", choices=("onefile", "onedir"), default="onefile")
    parser.add_argument("--skip-build", action="store_true", help="Atualiza versão sem executar PyInstaller")
    parser.add_argument("--sign", action="store_true", help="Assina o executável gerado com signtool")
    parser.add_argument("--no-venv", action="store_true", help="Nao cria/reusa .venv automaticamente")
    parser.add_argument("--sync-deps", action="store_true", help="Forca instalacao dos requirements antes do build")
    parser.add_argument("--skip-zip", action="store_true", help="Nao criar ZIPs de release/backup")
    parser.add_argument(
        "--publish", action="store_true",
        help="(compat.) Publicacao ja e automatica quando config/config.ini "
             "[download_server] enabled=1; esta flag e um no-op mantido por compatibilidade.",
    )
    parser.add_argument(
        "--no-publish", action="store_true",
        help="Nao publicar o RD-COLETOR.zip no download server, mesmo com [download_server] enabled=1.",
    )
    return parser.parse_args(argv)


def resolve_target_versions(args, selected_components):
    # Politica formal: bump de versao so e permitido em release conjunta.
    if args.component != "all" and args.bump != "none":
        raise RuntimeError(
            "Politica de versao unificada: use --component all para qualquer bump. "
            "Para compilar componente isolado, use --bump none."
        )

    currents = {component.key: read_version(component.version_file) for component in selected_components}

    # version_info.txt e a base de QUALQUER compilacao (--bump none => usa como esta;
    # --bump X => incrementa a partir dela). Os version.py sao alinhados no main().
    base = read_project_version()
    print(f"[VERSION] Base (version_info.txt): {format_version(base)}")
    target = bump_version(base, args.bump)
    return {component.key: target for component in selected_components}, currents


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    clean_pycache_project("inicio da compilacao")
    try:
        return _run_build(args)
    finally:
        clean_pycache_project("fim da compilacao")


def _run_build(args):
    if not args.no_venv and not args.skip_build:
        ensure_venv()
        sync_dependencies(force=args.sync_deps)

    exe_paths = []
    zip_paths = []
    component_versions = []
    selected_components = component_list(args.component)
    try:
        target_versions, current_versions = resolve_target_versions(args, selected_components)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        return 1

    # Um --bump reescreve version_info.txt (fonte unica) com a versao nova.
    if args.bump != "none":
        unified_target = next(iter(target_versions.values()))
        write_project_version(unified_target)
        print(f"[VERSION] version_info.txt -> {format_version(unified_target)}")

    for component in selected_components:
        current = current_versions[component.key]
        updated = target_versions[component.key]
        component_versions.append((component.name, format_version(updated)))
        if updated != current:
            write_version(component, updated)
            print(f"[VERSION] {component.name}: {format_version(current)} -> {format_version(updated)}")
        else:
            print(f"[VERSION] {component.name}: sem bump ({format_version(current)})")

        if args.skip_build:
            version_file = generate_version_file(component, updated)
            print(f"[VERSION-FILE] {version_file}")
        else:
            exe_paths.append(build(component, args.build_type, updated, sign=args.sign))

    if exe_paths and not args.skip_zip:
        print("")
        print("[ZIP] Gerando pacotes ZIP")
        zip_paths.append(create_release_zip(component_versions, selected_components))
        zip_paths.append(create_backup_zip(component_versions))
    elif exe_paths:
        print("[ZIP] Geracao de ZIPs pulada (--skip-zip)")

    # Publicacao automatica: roda sempre que houve build/skip-build e nao veio
    # --no-publish. publish_coletor_package() ja se auto-inibe se
    # [download_server] enabled != 1 (nada e enviado nesse caso).
    if not args.no_publish and (exe_paths or args.skip_build):
        publish_coletor_package(target_versions)
    elif not args.no_publish:
        print("[PUBLISH] Nada compilado nesta execucao - publicacao pulada")

    display_build_summary(exe_paths)
    display_zip_summary(zip_paths)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
