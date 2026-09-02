"""
utils.py - Funções utilitárias comuns
"""

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def get_project_root():
    """Obter diretório raiz do projeto."""
    return Path(__file__).parent.parent.parent


def run_command(cmd, capture_output=True, timeout=None):
    """Executar comando e retornar output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture_output,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return -1, "", str(e)


def ensure_dir(path):
    """Garantir que diretório existe."""
    Path(path).mkdir(parents=True, exist_ok=True)


def is_windows():
    """Verificar se sistema é Windows."""
    return sys.platform == 'win32'


def is_linux():
    """Verificar se sistema é Linux."""
    return sys.platform == 'linux'


def get_store_scan_targets(ip_b12, cidr=None):
    """
    Gera lista de IPs alvo para scan da loja com base na matriz de ocupacao por CIDR.

    CIDR /24:
      B12:        .12
      PDV:        .1-.10, .110-.120
      TC:         .11, .13-.19, .30, .60, .70
      IMPRESSORA: .61, .62, .63

    CIDR /25:
      B12:        .12
      PDV:        .1-.10, .110-.120
      TC:         .129-.146
      IMPRESSORA: .161-.165

    Parametros:
        ip_b12 (str): IP do Banco 12 da loja, ex: '192.168.10.12'
        cidr (str | None): CIDR coletado do B12, ex: '192.168.10.12/24'.
                           Se None ou prefixo invalido, assume /24.

    Retorna:
        list[dict]: [{'ip': str, 'expected_type': str, 'last_octet': int}, ...]
                    Ordenado por last_octet. Inclui o proprio B12 com tipo 'B12'.
    """
    prefix = 24
    if cidr:
        try:
            prefix = int(str(cidr).split('/')[-1])
        except (ValueError, IndexError):
            prefix = 24

    parts = str(ip_b12).strip().split('.')
    if len(parts) != 4:
        return []
    base = '.'.join(parts[:3])  # ex: '192.168.10'

    if prefix == 25:
        matrix = {
            'B12':        [12],
            'PDV':        list(range(1, 11)) + list(range(110, 121)),
            'TC':         list(range(129, 147)),
            'IMPRESSORA': list(range(161, 166)),
        }
    else:  # /24 (default)
        matrix = {
            'B12':        [12],
            'PDV':        list(range(1, 11)) + list(range(110, 121)),
            'TC':         [11] + list(range(13, 20)) + [30, 60, 70],
            'IMPRESSORA': [61, 62, 63],
        }

    targets = []
    seen = set()
    for tipo, octets in matrix.items():
        for octet in octets:
            ip = f"{base}.{octet}"
            if ip not in seen:
                seen.add(ip)
                targets.append({'ip': ip, 'expected_type': tipo, 'last_octet': octet})

    return sorted(targets, key=lambda x: x['last_octet'])
