"""
runtime_paths.py - Caminhos persistentes do COLETOR.
"""

from pathlib import Path
import shutil
import sys


def app_dir() -> Path:
    """Diretorio persistente do app: pasta do exe ou raiz do COLETOR."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def bundle_dir() -> Path:
    """Diretorio de recursos empacotados pelo PyInstaller."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return app_dir()


def resolve_runtime_path(value: str | Path, base: Path | None = None) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return (base or app_dir()) / path


def config_dir() -> Path:
    return app_dir() / "config"


def default_config_path() -> Path:
    return config_dir() / "config.ini"


def resource_path(*parts: str) -> Path:
    """Resolve recurso lido de dentro do bundle ou da raiz do projeto."""
    bundled = bundle_dir().joinpath(*parts)
    if bundled.exists():
        return bundled
    return app_dir().joinpath(*parts)


def ensure_default_config(path: Path | None = None) -> Path:
    config_path = path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if not config_path.exists():
        legacy_config = app_dir() / "config.ini"
        template_candidates = [
            legacy_config,
            resource_path("config.ini.template"),
            resource_path("config", "config.ini.template"),
        ]
        for template in template_candidates:
            if template.exists():
                shutil.copy2(template, config_path)
                break
    return config_path
