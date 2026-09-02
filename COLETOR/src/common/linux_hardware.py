#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Helpers de coleta de hardware Linux via SSH."""

import os
import shlex
import re


_INVALID_DMI_VALUES = {
    "",
    "none",
    "n/a",
    "not specified",
    "not available",
    "to be filled by o.e.m.",
    "to be filled by oem",
    "default string",
    "system product name",
    "system version",
}


def _exec(client, command, timeout=10):
    _stdin, stdout, _stderr = client.exec_command(command, timeout=timeout)
    return stdout.read().decode(errors="ignore").strip()


def _first_line(client, command, timeout=10):
    output = _exec(client, command, timeout)
    return output.splitlines()[0].strip() if output else ""


def _sudo_command(command, password):
    if not password:
        return f"sudo -n {command}"
    return f"printf '%s\\n' {shlex.quote(password)} | sudo -S -p '' {command}"


def _clean_value(value):
    value = str(value or "").strip()
    return "" if value.lower() in _INVALID_DMI_VALUES else value


def _parse_dmidecode_system(output):
    fields = {}
    for line in output.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = _clean_value(value)
        if key == "manufacturer":
            fields["mb_manufacturer"] = value
        elif key == "product name":
            fields["mb_product_name"] = value
        elif key == "version":
            fields["mb_version"] = value
    return fields


def collect_motherboard_info(client, password="", timeout=10):
    """Coleta fabricante/modelo/versao do sistema/placa-mae."""
    sys_values = {
        "mb_manufacturer": (
            _first_line(client, "cat /sys/class/dmi/id/sys_vendor 2>/dev/null", timeout)
            or _first_line(client, "cat /sys/class/dmi/id/board_vendor 2>/dev/null", timeout)
        ),
        "mb_product_name": (
            _first_line(client, "cat /sys/class/dmi/id/product_name 2>/dev/null", timeout)
            or _first_line(client, "cat /sys/class/dmi/id/board_name 2>/dev/null", timeout)
        ),
        "mb_version": (
            _first_line(client, "cat /sys/class/dmi/id/product_version 2>/dev/null", timeout)
            or _first_line(client, "cat /sys/class/dmi/id/board_version 2>/dev/null", timeout)
        ),
    }
    sys_values = {key: _clean_value(value) for key, value in sys_values.items()}
    if any(sys_values.values()):
        return sys_values

    commands = [
        "dmidecode | sed -n '/^System Information/,/^$/p'",
        "sudo -n dmidecode | sed -n '/^System Information/,/^$/p'",
        _sudo_command("dmidecode", password),
    ]
    for command in commands:
        output = _exec(client, command, timeout)
        if not output:
            continue
        match = re.search(r"System Information(.*?)(?:\n\n|\Z)", output, re.S)
        fields = _parse_dmidecode_system(match.group(1) if match else output)
        if any(fields.values()):
            return {
                "mb_manufacturer": fields.get("mb_manufacturer", ""),
                "mb_product_name": fields.get("mb_product_name", ""),
                "mb_version": fields.get("mb_version", ""),
            }
    return {"mb_manufacturer": "", "mb_product_name": "", "mb_version": ""}


def _to_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        try:
            return int(float(str(value).strip()))
        except (TypeError, ValueError):
            return None


def collect_memory_info(client, timeout=10):
    """Coleta MemTotal em bytes via /proc/meminfo, com fallback para free -b."""
    raw = _first_line(
        client,
        "awk '/^MemTotal:/ {printf \"%.0f\", $2*1024}' /proc/meminfo 2>/dev/null",
        timeout,
    )
    mem_bytes = _to_int(raw)
    if not mem_bytes:
        raw = _first_line(client, "free -b 2>/dev/null | awk '/^Mem:/ {print $2}'", timeout)
        mem_bytes = _to_int(raw)
    return {
        "memoria_total": mem_bytes,
        "ram_gb": round(mem_bytes / 1073741824, 2) if mem_bytes else None,
    }


def collect_os_info(client, timeout=10):
    os_name = (
        _first_line(
            client,
            "awk -F= '/^PRETTY_NAME=/ {gsub(/\"/, \"\", $2); print $2}' /etc/os-release 2>/dev/null",
            timeout,
        )
        or _first_line(client, "uname -sr", timeout)
    )
    kernel = _first_line(client, "uname -r", timeout)
    return {"os": os_name, "kernel": kernel, "os_version": kernel}


def collect_cpu_cores(client, timeout=10):
    raw = (
        _first_line(client, "grep '^cpu cores' /proc/cpuinfo | head -1 | awk '{print $NF}'", timeout)
        or _first_line(client, "nproc 2>/dev/null", timeout)
        or _first_line(client, "grep -c '^processor' /proc/cpuinfo 2>/dev/null", timeout)
    )
    return _to_int(raw)


def collect_mac_address(client, timeout=10):
    return _first_line(
        client,
        "ip link show 2>/dev/null | awk '/ether/ {print $2; exit}'",
        timeout,
    )


def _parse_lsblk_pairs(output):
    disks = []
    for line in output.splitlines():
        try:
            values = dict(part.split("=", 1) for part in shlex.split(line) if "=" in part)
        except ValueError:
            continue
        if values.get("TYPE") != "disk":
            continue
        try:
            size = int(values.get("SIZE") or 0)
        except ValueError:
            size = 0
        name = values.get("NAME", "")
        model = _clean_value(values.get("MODEL", ""))
        rota = values.get("ROTA", "")
        tran = values.get("TRAN", "")
        media_type = "HDD" if rota == "1" else "SSD" if rota == "0" else ""
        if name.lower().startswith("nvme") or tran.lower() == "nvme":
            media_type = "SSD"
        disks.append({
            "name": name,
            "model": model,
            "size": size,
            "media_type": media_type or "N/C",
        })
    return disks


def _root_disk_name(client, timeout=10):
    source = _first_line(client, "findmnt -n -o SOURCE / 2>/dev/null", timeout)
    if not source:
        return ""
    parent = _first_line(client, f"lsblk -no PKNAME {shlex.quote(source)} 2>/dev/null", timeout)
    if parent:
        return parent
    return os.path.basename(source).strip()


def collect_disk_info(client, password="", timeout=10):
    """Coleta disco fisico da particao raiz, com fallback para maior disco real."""
    root_disk = _root_disk_name(client, timeout)
    list_command = "lsblk -dn -b -P -o NAME,MODEL,SIZE,ROTA,TYPE,TRAN 2>/dev/null"
    output = _exec(client, list_command, timeout)
    if not output:
        output = _exec(client, f"sudo -n {list_command}", timeout)
    if not output:
        output = _exec(client, _sudo_command(list_command, password), timeout)

    disks = _parse_lsblk_pairs(output)
    if not disks:
        return {"hdd_media_type": "", "hdd_model": "", "hdd_size": None, "disk_gb": None}

    selected = next((disk for disk in disks if disk["name"] == root_disk), None)
    is_gadget = selected and selected["model"].replace(" ", "_") == "File-Stor_Gadget"
    if selected is None or is_gadget or (selected.get("size") or 0) < 10737418240:
        candidates = [
            disk for disk in disks
            if disk["model"].replace(" ", "_") != "File-Stor_Gadget"
            and (disk.get("size") or 0) >= 10737418240
        ]
        selected = max(candidates or disks, key=lambda disk: disk["size"])

    size = selected["size"] or None
    return {
        "hdd_media_type": selected["media_type"],
        "hdd_model": selected["model"] or selected["name"],
        "hdd_size": size,
        "disk_gb": round(size / 1073741824, 2) if size else None,
    }
