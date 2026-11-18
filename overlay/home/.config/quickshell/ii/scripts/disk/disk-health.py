#!/usr/bin/env python3
"""Health of the drive holding a block device, read from UDisks2 without root; prints one JSON line."""
import json
import subprocess
import sys

UDISKS = "org.freedesktop.UDisks2"


def busctl(*args):
    out = subprocess.run(["busctl", "--system", "-j", *args], capture_output=True, text=True, check=True).stdout
    return json.loads(out)["data"]


def prop(path, iface, name):
    return busctl("get-property", UDISKS, path, f"{UDISKS}.{iface}", name)


def interfaces(path):
    out = subprocess.run(["busctl", "--system", "introspect", "--list", UDISKS, path],
                         capture_output=True, text=True, check=True).stdout
    return {line.split()[0] for line in out.splitlines() if " interface " in line}


def nvme(drive):
    attrs = busctl("call", UDISKS, drive, f"{UDISKS}.NVMe.Controller", "SmartGetAttributes", "a{sv}", "0")[0]
    value = {k: v["data"] for k, v in attrs.items()}
    warnings = prop(drive, "NVMe.Controller", "SmartCriticalWarning")
    problems = []
    if warnings:
        problems.append("critical warning: " + ", ".join(warnings))
    if value["media_errors"]:
        problems.append(f"{value['media_errors']} media errors")
    if value["avail_spare"] <= value["spare_thresh"]:
        problems.append(f"spare {value['avail_spare']}%")
    return {
        "health": "failing" if warnings else "warning" if problems else "good",
        "problems": problems,
        "worn": value["percent_used"],
        "written": value["total_data_written"],
        "hours": prop(drive, "NVMe.Controller", "SmartPowerOnHours"),
    }


def ata(drive):
    if not prop(drive, "Drive.Ata", "SmartEnabled"):
        return None
    failing = prop(drive, "Drive.Ata", "SmartFailing")
    bad = prop(drive, "Drive.Ata", "SmartNumBadSectors")
    problems = (["SMART says failing"] if failing else []) + ([f"{bad} bad sectors"] if bad > 0 else [])
    return {
        "health": "failing" if failing else "warning" if problems else "good",
        "problems": problems,
        "worn": None,
        "written": None,
        "hours": prop(drive, "Drive.Ata", "SmartPowerOnSeconds") // 3600,
    }


def main():
    drive = prop(f"/org/freedesktop/UDisks2/block_devices/{sys.argv[1]}", "Block", "Drive")
    found = interfaces(drive)
    if f"{UDISKS}.NVMe.Controller" in found:
        result = nvme(drive)
    elif f"{UDISKS}.Drive.Ata" in found:
        result = ata(drive)
    else:
        result = None
    print(json.dumps(result))


if __name__ == "__main__":
    main()
