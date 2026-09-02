#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scan_core.py - Logica de scan "um item por vez" compartilhada entre as Abas 2/3/4
e a Aba Autopilot.

Extraido das Abas 2 (B12), 3 (Scan Loja) e 4 (Hardware) para que o Autopilot possa
consumir a mesma logica de coleta a partir de pools de workers persistentes, sem
depender de instancias de Tab (Tkinter). As Abas 2/3/4 continuam com sua propria UI
e delegam a este modulo para o trabalho de item unico.

Nenhuma funcao aqui depende de self/Tkinter; credenciais e timeouts sao sempre
recebidos como parametros ja resolvidos. `on_log(mensagem, nivel)` e um callback
opcional para logging (evita depender de um ConsoleLogger especifico).
"""

import base64
import json
import re
import socket
from datetime import datetime

from src.common.linux_hardware import (
    collect_cpu_cores,
    collect_disk_info,
    collect_mac_address,
    collect_memory_info,
    collect_motherboard_info,
    collect_os_info,
)

try:
    import paramiko
except ImportError:
    paramiko = None

try:
    import pythoncom
    import wmi as wmi_module
except ImportError:
    pythoncom = None
    wmi_module = None

_PYSNMP_ASYNC = False
try:
    from pysnmp.hlapi.asyncio import (
        getCmd, SnmpEngine, CommunityData, UdpTransportTarget,
        ContextData, ObjectType, ObjectIdentity,
    )
    _PYSNMP_OK = True
    _PYSNMP_ASYNC = True
except ImportError:
    try:
        from pysnmp.hlapi import (
            getCmd, SnmpEngine, CommunityData, UdpTransportTarget,
            ContextData, ObjectType, ObjectIdentity,
        )
        _PYSNMP_OK = True
    except ImportError:
        _PYSNMP_OK = False


def _emit(on_log, msg, level="INFO"):
    if on_log:
        try:
            on_log(msg, level)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Helpers genericos de rede
# ---------------------------------------------------------------------------

def test_tcp_port(ip, port, timeout=2):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((ip, port))
            return True
    except Exception:
        return False


def try_ssh_auth(ip, user, password, timeout, port=22):
    """Tenta autenticacao SSH; retorna True se bem-sucedido."""
    if paramiko is None:
        return False
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            ip, port=port, username=user, password=password,
            timeout=timeout, banner_timeout=timeout, auth_timeout=timeout,
            look_for_keys=False, allow_agent=False,
        )
        client.close()
        return True
    except paramiko.AuthenticationException:
        return False
    except Exception:
        return False


def get_hostname_ssh(ip, timeout, user, password, port=22):
    if not paramiko:
        return "N/A"
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, port=port, username=user, password=password, timeout=timeout)
        _stdin, stdout, _stderr = client.exec_command("hostname")
        hostname = stdout.read().decode(errors="ignore").strip()
        client.close()
        return hostname if hostname else "N/A"
    except Exception:
        return "N/A"


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(str(value).replace(",", ".")))
        except (TypeError, ValueError):
            return default


# ---------------------------------------------------------------------------
# B12 (Aba 2)
# ---------------------------------------------------------------------------

def make_b12_status_data(java, filial, nome, ip, status, error):
    now = datetime.now()
    return {
        'java': java, 'ip': ip, 'filial': filial, 'nome_filial': nome,
        'collection_status': status,
        'collection_start': now, 'collection_end': now,
        'collection_date': now.strftime('%Y-%m-%d %H:%M:%S'),
        'tipo_equipamento': 'B12',
        'hostname': None, 'hostname_raw': None, 'os': None, 'os_version': None,
        'kernel': None, 'cidr': None, 'cores': None, 'memory': None, 'mac': None,
        'mb_manufacturer': None, 'mb_product': None, 'mb_version': None,
        'disk_type': None, 'disk_model': None, 'disk_size': None,
        'fields_collected': 0, 'ssh_error': error,
    }


def collect_b12_complete_data(ip, java, filial, nome, timeout, user, password, port=22, on_log=None):
    """Coleta dados COMPLETOS do B12 via SSH (identico ao antigo Tab2._collect_b12_complete_data)."""
    data = {
        'java': java, 'ip': ip, 'filial': filial, 'nome_filial': nome,
        'collection_status': 'IN_PROGRESS', 'collection_start': datetime.now(),
        'tipo_equipamento': 'B12',
        'hostname': None, 'hostname_raw': None, 'os': None, 'os_version': None,
        'kernel': None, 'cidr': None, 'cores': None, 'memory': None, 'mac': None,
        'mb_manufacturer': None, 'mb_product': None, 'mb_version': None,
        'disk_type': None, 'disk_model': None, 'disk_size': None,
        'fields_collected': 0, 'ssh_error': None,
    }

    if paramiko is None:
        data['collection_status'] = 'FAILED'
        data['ssh_error'] = 'paramiko_not_installed'
        data['collection_end'] = datetime.now()
        data['collection_date'] = data['collection_end'].strftime('%Y-%m-%d %H:%M:%S')
        return data

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, port=port, username=user, password=password, timeout=timeout, banner_timeout=timeout)

        try:
            _stdin, stdout, _stderr = client.exec_command("cat /etc/hostname", timeout=timeout)
            data['hostname_raw'] = stdout.read().decode(errors='ignore').strip()
            data['fields_collected'] += 1
        except Exception:
            data['hostname_raw'] = None

        try:
            _stdin, stdout, _stderr = client.exec_command("hostname && cat /etc/*release", timeout=timeout)
            output = stdout.read().decode(errors='ignore')
            lines = output.splitlines()
            if lines:
                data['hostname'] = lines[0].strip()
                data['fields_collected'] += 1
                for line in lines:
                    if line.startswith('PRETTY_NAME='):
                        data['os'] = line.split('=', 1)[1].strip().strip('"')
                        data['fields_collected'] += 1
                    elif line.startswith('VERSION_ID='):
                        data['os_version'] = line.split('=', 1)[1].strip().strip('"')
                        data['fields_collected'] += 1
        except Exception:
            pass

        os_info = collect_os_info(client, timeout=timeout)
        if os_info.get('os'):
            data['os'] = os_info['os']
        if os_info.get('os_version'):
            data['os_version'] = os_info['os_version']
        if os_info.get('kernel'):
            data['kernel'] = os_info['kernel']

        try:
            _stdin, stdout, _stderr = client.exec_command("uname -r", timeout=timeout)
            data['kernel'] = stdout.read().decode(errors='ignore').strip()
            if data['kernel']:
                data['fields_collected'] += 1
        except Exception:
            pass

        try:
            _stdin, stdout, _stderr = client.exec_command("ip a", timeout=timeout)
            output = stdout.read().decode(errors='ignore')
            cidr_matches = re.findall(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', output)
            for ip_addr, prefix in cidr_matches:
                last_octet = ip_addr.split('.')[-1]
                if last_octet == '12':
                    data['cidr'] = f"{ip_addr}/{prefix}"
                    data['fields_collected'] += 1
                    break
            if not data['cidr'] and cidr_matches:
                data['cidr'] = f"{cidr_matches[0][0]}/{cidr_matches[0][1]}"
                data['fields_collected'] += 1
        except Exception:
            pass

        try:
            cores = collect_cpu_cores(client, timeout=timeout)
            if cores:
                data['cores'] = str(cores)
                data['fields_collected'] += 1
        except Exception:
            try:
                _stdin, stdout, _stderr = client.exec_command("grep -c ^processor /proc/cpuinfo", timeout=timeout)
                cores = stdout.read().decode(errors='ignore').strip()
                data['cores'] = cores
                if cores:
                    data['fields_collected'] += 1
            except Exception:
                pass

        try:
            mem_info = collect_memory_info(client, timeout=timeout)
            if mem_info.get('memoria_total'):
                data['memory'] = mem_info['memoria_total']
                data['fields_collected'] += 1
        except Exception:
            pass

        try:
            mac = collect_mac_address(client, timeout=timeout)
            if mac:
                data['mac'] = mac
                data['fields_collected'] += 1
        except Exception:
            pass

        try:
            mb_info = collect_motherboard_info(client, password=password, timeout=timeout)
            data['mb_manufacturer'] = mb_info.get('mb_manufacturer') or None
            data['mb_product'] = mb_info.get('mb_product_name') or None
            data['mb_version'] = mb_info.get('mb_version') or None
            data['fields_collected'] += sum(
                1 for value in (data['mb_manufacturer'], data['mb_product'], data['mb_version']) if value
            )
        except Exception:
            pass

        try:
            disk_info = collect_disk_info(client, password=password, timeout=timeout)
            data['disk_type'] = disk_info.get('hdd_media_type') or None
            data['disk_model'] = disk_info.get('hdd_model') or None
            data['disk_size'] = disk_info.get('hdd_size')
            data['fields_collected'] += sum(
                1 for value in (data['disk_type'], data['disk_model'], data['disk_size']) if value
            )
        except Exception:
            pass

        client.close()
        data['collection_status'] = 'SUCCESS'
        data['ssh_error'] = None

    except paramiko.AuthenticationException as e:
        data['collection_status'] = 'AUTH_FAILED'
        data['ssh_error'] = str(e) or 'Authentication failed'
        _emit(on_log, f"Falha de autenticação SSH em {ip} com usuario='{user}' porta={port} senha_tamanho={len(password or '')}", "WARNING")
    except Exception as e:
        data['collection_status'] = 'FAILED'
        data['ssh_error'] = str(e)
        _emit(on_log, f"Erro ao coletar dados SSH de {ip}: {e}", "WARNING")

    data['collection_end'] = datetime.now()
    data['collection_date'] = data['collection_end'].strftime('%Y-%m-%d %H:%M:%S')
    return data


def run_b12_check(target, timeout, user, password, ssh_port, collect_detail, on_log=None):
    """Executa a checagem B12 para um alvo. Retorna (result_dict, status_text, level)."""
    ip = target["ip"]
    java = target["java"]
    filial = target["filial"]
    nome = target["nome"]
    # NB: assinatura e test_tcp_port(ip, port, timeout) — nao inverter a ordem.
    ssh_open = test_tcp_port(ip, ssh_port, timeout)
    if ssh_open:
        if collect_detail:
            b12_data = collect_b12_complete_data(ip, java, filial, nome, timeout, user, password, ssh_port, on_log=on_log)
            hostname = b12_data.get('hostname', 'N/A') or 'N/A'
            collection_status = b12_data.get('collection_status')
            if collection_status == "SUCCESS":
                status = f"SSH OK ({b12_data.get('fields_collected', 0)} campos)"
                level = "SUCCESS"
            elif collection_status == "AUTH_FAILED":
                status = "Falha autenticação"
                level = "WARNING"
            else:
                status = "SSH sem coleta"
                level = "WARNING"
        else:
            hostname = get_hostname_ssh(ip, timeout, user, password, ssh_port)
            b12_data = None
            status = "SSH aberto"
            level = "SUCCESS"
    else:
        hostname = "N/A"
        b12_data = make_b12_status_data(java, filial, nome, ip, "OFFLINE", "ssh_port_closed")
        status = "Offline"
        level = "INFO"

    return (
        {
            "filial": filial, "java": java, "historico": target.get("historico", ""),
            "nome": nome, "ip": ip, "ssh": ssh_open, "hostname": hostname, "b12_data": b12_data,
        },
        status, level,
    )


# ---------------------------------------------------------------------------
# Scan Loja (Aba 3)
# ---------------------------------------------------------------------------

def run_store_scan_target(target, auth_context, on_log=None):
    """Executa o scan de um alvo da loja. target = (filial, nome, ip, expected_type, logo)."""
    filial, nome, ip, expected_type, logo = target
    timeout = auth_context["timeout"]
    ssh_timeout = auth_context["ssh_timeout"]
    if expected_type == "B12":
        _emit(on_log, f"{ip:<16} ESPERADO:{expected_type:<12} -> coletado na Aba 2", "INFO")
        return None

    ssh, radmin, printer, ssh_os = False, False, False, None
    if expected_type == "IMPRESSORA":
        printer = auth_context["scan_printer"] and test_tcp_port(ip, 9100, timeout)
        tipo = "IMPRESSORA" if printer else "Offline"
    elif expected_type == "PDV":
        ssh = auth_context["scan_ssh"] and test_tcp_port(ip, 22, timeout)
        ssh_os = "LINUX" if ssh else None
        tipo = "PDV Linux" if ssh else "Offline"
    else:
        radmin = auth_context["scan_radmin"] and test_tcp_port(ip, 7856, timeout)
        if radmin:
            tipo = "TC Win"
        else:
            ssh = auth_context["scan_ssh"] and test_tcp_port(ip, 22, timeout)
            if ssh:
                if try_ssh_auth(ip, auth_context["user_linux"], auth_context["pass_linux"], ssh_timeout):
                    ssh_os = "LINUX"
                    tipo = "TC Linux"
                else:
                    logo_upper = str(logo).upper()
                    win_user = auth_context["user_win_raia"] if "RAIA" in logo_upper else auth_context["user_win_drog"]
                    win_pass = auth_context["pass_win_raia"] if "RAIA" in logo_upper else auth_context["pass_win_drog"]
                    if try_ssh_auth(ip, win_user, win_pass, ssh_timeout):
                        ssh_os = "WIN"
                        tipo = "TC Win"
                    else:
                        tipo = "SSH/Desconhecido"
            else:
                tipo = "Offline"

    return {"filial": filial, "nome": nome, "ip": ip,
            "expected_type": expected_type, "logo": logo,
            "ssh": ssh, "radmin": radmin, "printer": printer,
            "ssh_os": ssh_os, "tipo": tipo}


# ---------------------------------------------------------------------------
# Hardware (Aba 4)
# ---------------------------------------------------------------------------

_NC = 'NAO_COLETADO'

_ERROR_PREFIXES = (
    'SSH_', 'ERRO_SSH', 'PARAMIKO_',
    'WMI_', 'ERRO_WMI',
    'WINDOWS_WMI_', 'FALLBACK_SSH_',
    'PYSNMP_', 'SNMP_',
    'COLETOR_REAL_',
)


def is_hw_success(result):
    """Retorna True se os dados foram coletados com sucesso."""
    os_val = result.get('os', '')
    return not any(os_val.startswith(p) for p in _ERROR_PREFIXES)


def _is_port_open(ip, port, timeout):
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception:
        return False


def _ssh_first_line(client, command):
    _stdin, stdout, _stderr = client.exec_command(command, timeout=10)
    output = stdout.read().decode(errors='ignore').strip()
    return output.splitlines()[0].strip() if output else ""


def _is_wmi_access_denied(error):
    text = str(error).lower()
    return 'access is denied' in text or '-2147024891' in text


def _windows_blocked_status(fallback_status):
    if fallback_status in ('FALLBACK_SSH_INDISPONIVEL', 'FALLBACK_SSH_AUTH_FAILED'):
        return 'WINDOWS_WMI_BLOQUEADO_SSH_INATIVO'
    return f'WINDOWS_WMI_BLOQUEADO; {fallback_status or "FALLBACK_SSH_FALHOU"}'


def _classify_windows_disk(disk):
    model = (getattr(disk, 'Model', '') or '').upper()
    media = (getattr(disk, 'MediaType', '') or '').upper()
    interface = (getattr(disk, 'InterfaceType', '') or '').upper()
    pnp = (getattr(disk, 'PNPDeviceID', '') or '').upper()
    text = ' '.join([model, media, interface, pnp])
    if 'NVME' in text:
        return 'SSD'
    if 'SSD' in text or 'SOLID STATE' in text:
        return 'SSD'
    if 'HDD' in text or 'FIXED HARD DISK' in text or 'ROTATIONAL' in text:
        return 'HDD'
    return 'HDD'


def _get_windows_disk_info(c, os_info):
    """Retorna disco fisico do drive do sistema, em bytes."""
    disks = []
    try:
        system_drive = getattr(os_info, 'SystemDrive', None) or 'C:'
        partitions = c.query(
            f"ASSOCIATORS OF {{Win32_LogicalDisk.DeviceID='{system_drive}'}} "
            "WHERE AssocClass=Win32_LogicalDiskToPartition"
        )
        for partition in partitions:
            disk_index = getattr(partition, 'DiskIndex', None)
            if disk_index is not None:
                disks.extend(c.Win32_DiskDrive(Index=int(disk_index)))
        if not disks:
            disks = list(c.Win32_DiskDrive())
    except Exception:
        disks = list(c.Win32_DiskDrive())

    candidates = []
    for disk in disks:
        try:
            size = int(getattr(disk, 'Size', 0) or 0)
        except (TypeError, ValueError):
            size = 0
        model = getattr(disk, 'Model', '') or ''
        media_type = _classify_windows_disk(disk)
        interface = (getattr(disk, 'InterfaceType', '') or '').upper()
        if interface == 'USB' and len(disks) > 1:
            continue
        candidates.append({'model': model, 'size_bytes': size, 'media_type': media_type})

    if not candidates:
        return {'model': '', 'size_bytes': 0, 'media_type': ''}
    return max(candidates, key=lambda item: item['size_bytes'])


def _ssh_powershell(client, script, timeout=20):
    encoded = base64.b64encode(script.encode('utf-16le')).decode('ascii')
    command = f'powershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand {encoded}'
    _stdin, stdout, _stderr = client.exec_command(command, timeout=timeout)
    return stdout.read().decode(errors='ignore').strip()


def _collect_hardware_windows_ssh(ip, user, password, timeout):
    """Fallback Windows: coleta via SSH executando PowerShell local."""
    nc = _NC
    result = {
        'ip': ip,
        'hostname': nc, 'cpu_model': nc, 'cores': None,
        'ram_gb': None, 'disk_gb': None, 'os': nc, 'os_version': nc,
        'kernel': nc, 'cores_fisicos': nc, 'memoria_total': None,
        'mac_address': nc, 'mb_manufacturer': nc, 'mb_product_name': nc,
        'mb_version': nc, 'hdd_media_type': nc, 'hdd_model': nc, 'hdd_size': None,
    }
    if paramiko is None:
        result['os'] = 'FALLBACK_SSH_PARAMIKO_NAO_INSTALADO'
        return result
    if not _is_port_open(ip, 22, min(timeout, 5)):
        result['os'] = 'FALLBACK_SSH_INDISPONIVEL'
        return result

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            ip, username=user, password=password,
            timeout=timeout, banner_timeout=timeout, auth_timeout=timeout,
            look_for_keys=False, allow_agent=False,
        )

        result['hostname'] = _ssh_powershell(client, '$env:COMPUTERNAME', timeout) or nc
        result['cpu_model'] = _ssh_powershell(
            client, '(Get-CimInstance Win32_Processor | Select-Object -First 1).Name', timeout,
        ) or nc
        cores = safe_int(_ssh_powershell(
            client, '(Get-CimInstance Win32_Processor | Select-Object -First 1).NumberOfCores', timeout,
        ), None)
        result['cores'] = cores
        result['cores_fisicos'] = str(cores) if cores else nc

        mem_bytes = safe_int(_ssh_powershell(
            client, '(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory', timeout,
        ), 0)
        result['memoria_total'] = mem_bytes or None
        result['ram_gb'] = round(mem_bytes / 1073741824, 2) if mem_bytes else None

        result['os'] = _ssh_powershell(client, '(Get-CimInstance Win32_OperatingSystem).Caption', timeout) or nc
        result['os_version'] = _ssh_powershell(client, '(Get-CimInstance Win32_OperatingSystem).Version', timeout) or nc
        result['kernel'] = result['os_version']

        mb_json = _ssh_powershell(
            client,
            "$cs=Get-CimInstance Win32_ComputerSystem; "
            "$prod=Get-CimInstance Win32_ComputerSystemProduct; "
            "[pscustomobject]@{Manufacturer=$cs.Manufacturer;Model=$cs.Model;Version=$prod.Version} | ConvertTo-Json -Compress",
            timeout,
        )
        try:
            mb = json.loads(mb_json) if mb_json else {}
        except Exception:
            mb = {}
        result['mb_manufacturer'] = mb.get('Manufacturer') or nc
        result['mb_product_name'] = mb.get('Model') or nc
        result['mb_version'] = mb.get('Version') or nc

        disk_json = _ssh_powershell(
            client,
            "$sys=$env:SystemDrive; "
            "$ld=Get-CimInstance Win32_LogicalDisk -Filter \"DeviceID='$sys'\"; "
            "$part=Get-CimAssociatedInstance -InputObject $ld -Association Win32_LogicalDiskToPartition | Select-Object -First 1; "
            "$disk=Get-CimAssociatedInstance -InputObject $part -Association Win32_DiskDriveToDiskPartition | Select-Object -First 1; "
            "if(-not $disk){$disk=Get-CimInstance Win32_DiskDrive | Sort-Object Size -Descending | Select-Object -First 1}; "
            "$pd=Get-PhysicalDisk | Where-Object { $_.FriendlyName -eq $disk.Model } | Select-Object -First 1; "
            "$media=if($pd){$pd.MediaType.ToString()}else{$disk.MediaType}; "
            "[pscustomobject]@{Model=$disk.Model;Size=[int64]$disk.Size;MediaType=$media;Interface=$disk.InterfaceType;PNP=$disk.PNPDeviceID} | ConvertTo-Json -Compress",
            timeout,
        )
        try:
            disk = json.loads(disk_json) if disk_json else {}
        except Exception:
            disk = {}
        hdd_bytes = safe_int(disk.get('Size'), 0)
        result['hdd_size'] = hdd_bytes or None
        result['disk_gb'] = round(hdd_bytes / 1073741824, 2) if hdd_bytes else None
        result['hdd_model'] = disk.get('Model') or nc
        media_text = ' '.join(str(disk.get(k) or '') for k in ('Model', 'MediaType', 'Interface', 'PNP')).upper()
        result['hdd_media_type'] = 'SSD' if any(token in media_text for token in ('SSD', 'NVME', 'SOLID STATE')) else 'HDD'

        result['mac_address'] = _ssh_powershell(
            client,
            "(Get-CimInstance Win32_NetworkAdapter -Filter \"PhysicalAdapter=True AND MACAddress IS NOT NULL\" | Select-Object -First 1).MACAddress",
            timeout,
        ) or nc
    except paramiko.AuthenticationException:
        result['os'] = 'FALLBACK_SSH_AUTH_FAILED'
    except Exception as e:
        result['os'] = f'FALLBACK_SSH_ERRO: {e}'
    finally:
        client.close()
    return result


def collect_hardware_windows(ip, bandeira, creds_bundle, on_log=None):
    """Coleta hardware de TC Windows via WMI, com fallback SSH/PowerShell."""
    nc = _NC
    result = {
        'ip': ip,
        'hostname': nc, 'cpu_model': nc, 'cores': None,
        'ram_gb': None, 'disk_gb': None, 'os': nc, 'os_version': nc,
        'kernel': nc, 'cores_fisicos': nc, 'memoria_total': None,
        'mac_address': nc, 'mb_manufacturer': nc, 'mb_product_name': nc,
        'mb_version': nc, 'hdd_media_type': nc, 'hdd_model': nc, 'hdd_size': None,
    }
    logo = str(bandeira or '').upper()
    if 'RAIA' in logo:
        user, password, timeout = creds_bundle['win_raia_user'], creds_bundle['win_raia_pass'], creds_bundle['win_raia_timeout']
    else:
        user, password, timeout = creds_bundle['win_drog_user'], creds_bundle['win_drog_pass'], creds_bundle['win_drog_timeout']

    if wmi_module is None or pythoncom is None:
        fallback = _collect_hardware_windows_ssh(ip, user, password, timeout)
        return fallback if is_hw_success(fallback) else {**result, 'os': 'WMI_NAO_INSTALADO'}

    pythoncom.CoInitialize()
    try:
        c = wmi_module.WMI(computer=ip, user=user, password=password)

        cpu = c.Win32_Processor()[0]
        comp = c.Win32_ComputerSystem()[0]
        prod = c.Win32_ComputerSystemProduct()[0]
        os_info = c.Win32_OperatingSystem()[0]
        nics = c.Win32_NetworkAdapter(PhysicalAdapter=True)
        disk_info = _get_windows_disk_info(c, os_info)

        result['hostname'] = comp.Name or nc
        result['cpu_model'] = cpu.Name or nc
        result['cores'] = cpu.NumberOfCores
        result['cores_fisicos'] = str(cpu.NumberOfCores) if cpu.NumberOfCores else nc

        mem_bytes = int(comp.TotalPhysicalMemory or 0)
        result['memoria_total'] = mem_bytes
        result['ram_gb'] = round(mem_bytes / 1073741824, 2) if mem_bytes else None

        hdd_bytes = disk_info.get('size_bytes') or 0
        result['hdd_size'] = hdd_bytes
        result['disk_gb'] = round(hdd_bytes / 1073741824, 2) if hdd_bytes else None
        result['hdd_model'] = disk_info.get('model') or nc
        result['hdd_media_type'] = disk_info.get('media_type') or nc

        result['os'] = os_info.Caption or nc
        result['os_version'] = os_info.Version or nc
        result['kernel'] = os_info.Version or nc

        result['mb_manufacturer'] = comp.Manufacturer or nc
        result['mb_product_name'] = comp.Model or nc
        result['mb_version'] = prod.Version or nc

        if nics:
            result['mac_address'] = nics[0].MACAddress or nc

    except Exception as e:
        if _is_wmi_access_denied(e):
            fallback = _collect_hardware_windows_ssh(ip, user, password, timeout)
            if is_hw_success(fallback):
                result = fallback
            else:
                result['os'] = _windows_blocked_status(fallback.get('os'))
                result['hostname'] = 'Inacessivel WMI/SSH'
        else:
            result['os'] = f'ERRO_WMI: {e}'
    finally:
        pythoncom.CoUninitialize()
    return result


def collect_hardware_printer(ip, creds_bundle):
    """Coleta dados de impressora via SNMP (pysnmp)."""
    import asyncio

    nc = _NC
    result = {
        'ip': ip,
        'hostname': nc, 'cpu_model': nc, 'cores': 0,
        'ram_gb': None, 'disk_gb': None, 'os': nc, 'os_version': nc,
        'kernel': 'Firmware', 'cores_fisicos': '0', 'memoria_total': 0,
        'mac_address': nc, 'mb_manufacturer': nc, 'mb_product_name': nc,
        'mb_version': nc, 'hdd_media_type': None, 'hdd_model': None, 'hdd_size': None,
    }
    if not _PYSNMP_OK:
        result['os'] = 'PYSNMP_NAO_INSTALADO'
        return result

    community = creds_bundle.get('snmp_community', 'public')
    port = int(creds_bundle.get('snmp_port', 161) or 161)
    timeout = int(creds_bundle.get('snmp_timeout', 5) or 5)

    oids = {
        'sysDescr': '1.3.6.1.2.1.1.1.0',
        'device_descr': '1.3.6.1.2.1.25.3.2.1.3.1',
        'epson_model': '1.3.6.1.4.1.1248.3.1.3.1.3.8.0',
        'mac_address': '1.3.6.1.2.1.2.2.1.6.1',
        'serial_number': '1.3.6.1.2.1.43.5.1.1.17.1',
    }

    def snmp_get(oid):
        try:
            if _PYSNMP_ASYNC:
                async def run_get():
                    return await getCmd(
                        SnmpEngine(),
                        CommunityData(community, mpModel=0),
                        UdpTransportTarget((ip, port), timeout=timeout, retries=1),
                        ContextData(),
                        ObjectType(ObjectIdentity(oid)),
                    )
                err_indication, err_status, _, var_binds = asyncio.run(run_get())
            else:
                it = getCmd(
                    SnmpEngine(),
                    CommunityData(community, mpModel=0),
                    UdpTransportTarget((ip, port), timeout=timeout, retries=1),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                )
                err_indication, err_status, _, var_binds = next(it)
            if err_indication or err_status:
                return None
            return str(var_binds[0][1])
        except Exception:
            return None

    sys_descr = snmp_get(oids['sysDescr'])
    device_descr = snmp_get(oids['device_descr'])
    epson_model = snmp_get(oids['epson_model'])
    mac_raw = snmp_get(oids['mac_address'])
    serial = snmp_get(oids['serial_number'])

    if not sys_descr:
        result['os'] = 'SNMP_SEM_RESPOSTA'
        return result

    fabricante = (sys_descr.split()[0] if sys_descr else nc)
    if fabricante.lower() == 'epson' and epson_model:
        modelo = f'EPSON {epson_model}'
    else:
        modelo = device_descr or sys_descr

    mac_clean = ''
    if mac_raw:
        hex_only = re.sub(r'[^0-9A-Fa-f]', '', mac_raw)
        if len(hex_only) >= 12:
            mac_clean = ':'.join(hex_only[i:i + 2] for i in range(0, 12, 2))

    result['hostname'] = f'Printer-{ip.split(".")[-1]}'
    result['mb_manufacturer'] = fabricante
    result['mb_product_name'] = modelo
    result['mb_version'] = serial or nc
    result['mac_address'] = mac_clean or nc
    result['os'] = f'Printer OS ({fabricante})'
    result['os_version'] = 'Firmware'
    result['kernel'] = 'Firmware'
    return result


def collect_hardware_linux(ip, creds_bundle, on_log=None):
    """Coleta completa via SSH Linux para tb_devices + tb_devices_detail."""
    nc = _NC
    result = {
        'ip': ip,
        'hostname': nc, 'cpu_model': nc, 'cores': None,
        'ram_gb': None, 'disk_gb': None, 'os': nc, 'os_version': nc,
        'kernel': nc, 'cores_fisicos': nc, 'memoria_total': None,
        'mac_address': nc, 'mb_manufacturer': nc, 'mb_product_name': nc,
        'mb_version': nc, 'hdd_media_type': nc, 'hdd_model': nc, 'hdd_size': None,
    }

    timeout = creds_bundle.get('linux_timeout', 10)
    if not _is_port_open(ip, 22, min(timeout, 5)):
        result['os'] = 'SSH_INDISPONIVEL'
        return result
    if paramiko is None:
        result['os'] = 'PARAMIKO_NAO_INSTALADO'
        return result

    user = creds_bundle['linux_user']
    password = creds_bundle['linux_pass']
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=password, timeout=timeout, banner_timeout=timeout)

        def get(cmd):
            return _ssh_first_line(client, cmd)

        result['hostname'] = (
            get("cat /etc/hostname") or get("hostname") or nc
        )
        result['cpu_model'] = (
            get("grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | xargs") or nc
        )
        result['cores'] = collect_cpu_cores(client, timeout=timeout)

        mem_info = collect_memory_info(client, timeout=timeout)
        result['ram_gb'] = mem_info.get('ram_gb')
        result['memoria_total'] = mem_info.get('memoria_total')

        os_info = collect_os_info(client, timeout=timeout)
        result['os'] = os_info.get('os') or nc
        result['os_version'] = os_info.get('os_version') or nc

        result['kernel'] = result['os_version']
        result['cores_fisicos'] = str(result['cores']) if result['cores'] is not None else nc

        result['mac_address'] = collect_mac_address(client, timeout=timeout) or nc
        mb_info = collect_motherboard_info(client, password=password, timeout=timeout)
        result['mb_manufacturer'] = mb_info.get('mb_manufacturer') or nc
        result['mb_product_name'] = mb_info.get('mb_product_name') or nc
        result['mb_version'] = mb_info.get('mb_version') or nc

        disk_info = collect_disk_info(client, password=password, timeout=timeout)
        result['hdd_media_type'] = disk_info.get('hdd_media_type') or nc
        result['hdd_model'] = disk_info.get('hdd_model') or nc
        result['hdd_size'] = disk_info.get('hdd_size')
        result['disk_gb'] = disk_info.get('disk_gb')

    except paramiko.AuthenticationException:
        result['os'] = 'AUTH_FAILED'
        _emit(on_log, f"Falha de autenticação SSH em {ip} com usuario='{user}' senha_tamanho={len(password or '')}", "WARNING")
    except Exception as e:
        result['os'] = f'ERRO_SSH: {e}'
    finally:
        client.close()
    return result


# ---------------------------------------------------------------------------
# Persistencia — usada pelo Autopilot (Abas 2/3/4 mantem suas proprias
# gravacoes inalteradas; a logica SQL aqui e espelhada da delas).
# ---------------------------------------------------------------------------

B12_TRACKED_FIELD_COUNT = 15


def _save_b12_collection_status(conn, result, b12_data):
    duration = 0
    if b12_data.get('collection_end') and b12_data.get('collection_start'):
        duration = int((b12_data['collection_end'] - b12_data['collection_start']).total_seconds())

    conn.execute("""
        INSERT OR REPLACE INTO tb_b12_data_collection_status (
            java, ip_b12, nome_filial, collection_status, collection_date, collection_duration_seconds,
            hostname_collected, hostname_value,
            hostname_raw_collected, hostname_raw_value,
            os_collected, os_value,
            os_version_collected, os_version_value,
            kernel_collected, kernel_value,
            cidr_collected, cidr_value,
            cores_collected, cores_value,
            memory_collected, memory_value_bytes,
            mac_collected, mac_value,
            mb_manufacturer_collected, mb_manufacturer_value,
            mb_product_collected, mb_product_value,
            mb_version_collected, mb_version_value,
            disk_media_type_collected, disk_media_type_value,
            disk_model_collected, disk_model_value,
            disk_size_collected, disk_size_value,
            fields_collected_count, collection_percentage, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        result['java'], result['ip'], result['nome'], b12_data.get('collection_status', 'PARTIAL'),
        b12_data.get('collection_date'),
        duration,
        1 if b12_data.get('hostname') else 0, b12_data.get('hostname'),
        1 if b12_data.get('hostname_raw') else 0, b12_data.get('hostname_raw'),
        1 if b12_data.get('os') else 0, b12_data.get('os'),
        1 if b12_data.get('os_version') else 0, b12_data.get('os_version'),
        1 if b12_data.get('kernel') else 0, b12_data.get('kernel'),
        1 if b12_data.get('cidr') else 0, b12_data.get('cidr'),
        1 if b12_data.get('cores') else 0, b12_data.get('cores'),
        1 if b12_data.get('memory') else 0, safe_int(b12_data.get('memory'), 0),
        1 if b12_data.get('mac') else 0, b12_data.get('mac'),
        1 if b12_data.get('mb_manufacturer') else 0, b12_data.get('mb_manufacturer'),
        1 if b12_data.get('mb_product') else 0, b12_data.get('mb_product'),
        1 if b12_data.get('mb_version') else 0, b12_data.get('mb_version'),
        1 if b12_data.get('disk_type') else 0, b12_data.get('disk_type'),
        1 if b12_data.get('disk_model') else 0, b12_data.get('disk_model'),
        1 if b12_data.get('disk_size') else 0, safe_int(b12_data.get('disk_size'), 0),
        b12_data.get('fields_collected', 0),
        (b12_data.get('fields_collected', 0) / B12_TRACKED_FIELD_COUNT * 100) if b12_data.get('fields_collected') else 0,
    ))


def save_b12_result(config_mgr, result, run_id=None):
    """Persiste um resultado de run_b12_check: tb_devices_detail,
    tb_b12_data_collection_status, tb_devices_detail_history, tb_filial.cidr."""
    b12_data = result.get('b12_data')
    if not b12_data:
        return
    conn = config_mgr.get_sqlite_connection()
    try:
        conn.execute("PRAGMA foreign_keys = OFF")
        ip, java, filial = result['ip'], result['java'], result['filial']
        _save_b12_collection_status(conn, result, b12_data)

        if b12_data.get('collection_status') == 'SUCCESS':
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            detail_values = (
                java, ip,
                b12_data.get('hostname') or b12_data.get('hostname_raw') or 'N/A',
                'B12',
                b12_data.get('os') or 'N/A',
                b12_data.get('kernel'),
                b12_data.get('cores'),
                safe_int(b12_data.get('memory'), 0),
                b12_data.get('mac'),
                b12_data.get('mb_manufacturer'),
                b12_data.get('mb_product'),
                b12_data.get('mb_version'),
                b12_data.get('disk_type'),
                b12_data.get('disk_model'),
                safe_int(b12_data.get('disk_size'), 0),
            )
            conn.execute("""
                INSERT OR REPLACE INTO tb_devices_detail (
                    java, ip, hostname, tipo_equipamento, sistema_operacional,
                    kernel, cores_fisicos, memoria_total, mac_address,
                    mb_manufacturer, mb_product_name, mb_version,
                    hdd_media_type, hdd_model, hdd_size, data_coleta, data_atualizacao
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, detail_values + (now_str, now_str))
            conn.execute("""
                INSERT INTO tb_devices_detail_history (
                    run_id, java, ip, hostname, tipo_equipamento, sistema_operacional,
                    kernel, cores_fisicos, memoria_total, mac_address,
                    mb_manufacturer, mb_product_name, mb_version,
                    hdd_media_type, hdd_model, hdd_size, data_coleta
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ip, data_coleta) DO NOTHING
            """, (run_id,) + detail_values + (now_str,))

            if b12_data.get('cidr'):
                conn.execute("UPDATE tb_filial SET cidr = ? WHERE filial = ?", (b12_data['cidr'], filial))

        conn.commit()
    finally:
        conn.close()


def save_store_scan_results(config_mgr, results, run_id=None, full_refresh=False):
    """Persiste resultados de run_store_scan_target: tb_detected_devices +
    tb_detected_devices_history. `results` = lista de dicts (uma loja ou lote)."""
    to_save = [r for r in results if r and r["tipo"] != "Offline"]
    if not to_save:
        return 0
    conn = config_mgr.get_sqlite_connection()
    try:
        rows = [
            (r["filial"], r["ip"], r.get("expected_type", ""),
             int(r["ssh"]), int(r["radmin"]), int(r.get("printer", 0)),
             r["tipo"], r.get("logo", ""))
            for r in to_save
        ]
        verb = "INSERT OR REPLACE" if full_refresh else "INSERT OR IGNORE"
        conn.executemany(
            f"{verb} INTO tb_detected_devices"
            " (filial, ip, expected_type, ssh, radmin, printer, device_type, logo)"
            " VALUES (?,?,?,?,?,?,?,?)",
            rows)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hist_rows = [(run_id,) + row + (now_str,) for row in rows]
        conn.executemany(
            "INSERT INTO tb_detected_devices_history"
            " (run_id, filial, ip, expected_type, ssh, radmin, printer, device_type, logo, snapshot_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(ip, snapshot_at) DO NOTHING",
            hist_rows)
        conn.commit()
        return len(rows)
    finally:
        conn.close()


def ensure_hw_columns(config_mgr):
    """Garante que as colunas de hardware existem em tb_detected_devices."""
    new_cols = [
        ("hw_hostname", "TEXT"), ("hw_cpu_model", "TEXT"), ("hw_cores", "INTEGER"),
        ("hw_ram_gb", "REAL"), ("hw_disk_gb", "REAL"), ("hw_os", "TEXT"),
        ("hw_os_version", "TEXT"), ("hw_kernel", "TEXT"), ("hw_cores_fisicos", "TEXT"),
        ("hw_memoria_total", "INTEGER"), ("hw_mac_address", "TEXT"),
        ("hw_mb_manufacturer", "TEXT"), ("hw_mb_product_name", "TEXT"), ("hw_mb_version", "TEXT"),
        ("hw_hdd_media_type", "TEXT"), ("hw_hdd_model", "TEXT"), ("hw_hdd_size", "INTEGER"),
        ("hw_scanned_at", "DATETIME"),
    ]
    conn = config_mgr.get_sqlite_connection()
    try:
        for col, coltype in new_cols:
            try:
                conn.execute(f"ALTER TABLE tb_detected_devices ADD COLUMN {col} {coltype}")
            except Exception:
                pass
        conn.commit()
    finally:
        conn.close()


def save_hardware_result(config_mgr, result, run_id=None):
    """Persiste um resultado de run_hardware_scan em tb_detected_devices +
    tb_detected_devices_history (snapshot completo, relido apos o UPDATE)."""
    conn = config_mgr.get_sqlite_connection()
    try:
        conn.execute(
            "UPDATE tb_detected_devices SET"
            "  hw_hostname=?,    hw_cpu_model=?,     hw_cores=?,"
            "  hw_ram_gb=?,      hw_disk_gb=?,       hw_os=?,"
            "  hw_os_version=?,  hw_kernel=?,        hw_cores_fisicos=?,"
            "  hw_memoria_total=?, hw_mac_address=?, hw_mb_manufacturer=?,"
            "  hw_mb_product_name=?, hw_mb_version=?, hw_hdd_media_type=?,"
            "  hw_hdd_model=?,   hw_hdd_size=?,      hw_scanned_at=CURRENT_TIMESTAMP"
            " WHERE ip=?",
            (
                result['hostname'], result['cpu_model'], result['cores'],
                result['ram_gb'], result['disk_gb'], result['os'],
                result['os_version'], result['kernel'], result['cores_fisicos'],
                result['memoria_total'], result['mac_address'], result['mb_manufacturer'],
                result['mb_product_name'], result['mb_version'], result['hdd_media_type'],
                result['hdd_model'], result['hdd_size'],
                result['ip'],
            ),
        )
        row = conn.execute("SELECT * FROM tb_detected_devices WHERE ip = ?", (result['ip'],)).fetchone()
        if row:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                "INSERT INTO tb_detected_devices_history ("
                " run_id, filial, ip, expected_type, ssh, radmin, printer, device_type, logo,"
                " detected_at, hw_hostname, hw_cpu_model, hw_cores, hw_ram_gb, hw_disk_gb, hw_os,"
                " hw_os_version, hw_kernel, hw_cores_fisicos, hw_memoria_total, hw_mac_address,"
                " hw_mb_manufacturer, hw_mb_product_name, hw_mb_version, hw_hdd_media_type,"
                " hw_hdd_model, hw_hdd_size, hw_scanned_at, snapshot_at"
                ") VALUES (?,?,?,?,?,?,?,?,?, ?,?,?,?,?,?,?, ?,?,?,?,?, ?,?,?,?, ?,?,?,?)"
                " ON CONFLICT(ip, snapshot_at) DO NOTHING",
                (
                    run_id, row["filial"], row["ip"], row["expected_type"], row["ssh"], row["radmin"],
                    row["printer"], row["device_type"], row["logo"],
                    row["detected_at"], row["hw_hostname"], row["hw_cpu_model"], row["hw_cores"],
                    row["hw_ram_gb"], row["hw_disk_gb"], row["hw_os"], row["hw_os_version"],
                    row["hw_kernel"], row["hw_cores_fisicos"], row["hw_memoria_total"], row["hw_mac_address"],
                    row["hw_mb_manufacturer"], row["hw_mb_product_name"], row["hw_mb_version"],
                    row["hw_hdd_media_type"], row["hw_hdd_model"], row["hw_hdd_size"],
                    row["hw_scanned_at"], now_str,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def run_hardware_scan(dev, creds_bundle, on_log=None):
    """Coleta hardware para um dispositivo. dev = {'filial','ip','device_type','bandeira'}."""
    filial, ip, dtype, bandeira = dev["filial"], dev["ip"], dev["device_type"], dev["bandeira"]
    if dtype == 'TC Win':
        result = collect_hardware_windows(ip, bandeira, creds_bundle, on_log=on_log)
    elif dtype == 'IMPRESSORA':
        result = collect_hardware_printer(ip, creds_bundle)
    else:
        result = collect_hardware_linux(ip, creds_bundle, on_log=on_log)

    result["filial"] = filial
    result["device_type"] = dtype
    result["bandeira"] = bandeira
    return result
