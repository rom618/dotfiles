#!/usr/bin/env python3
import glob
import time

ENGINE = "rcs"
SAMPLE_DELAY_SECONDS = 0.3


def read_cycles():
    busy_total = 0
    period_total = 0
    for fdinfo_path in glob.glob("/proc/[0-9]*/fdinfo/*"):
        try:
            with open(fdinfo_path, "r") as f:
                text = f.read()
        except (OSError, ValueError):
            continue

        if "drm-driver:\txe" not in text and "drm-driver:\tamdgpu" not in text:
            continue

        busy_key = f"drm-cycles-{ENGINE}:"
        period_key = f"drm-total-cycles-{ENGINE}:"
        busy = None
        period = None
        for line in text.splitlines():
            if line.startswith(busy_key):
                busy = int(line.split()[1])
            elif line.startswith(period_key):
                period = int(line.split()[1])
        if busy is not None and period is not None:
            busy_total += busy
            period_total += period

    return busy_total, period_total


def main():
    busy1, period1 = read_cycles()
    time.sleep(SAMPLE_DELAY_SECONDS)
    busy2, period2 = read_cycles()

    period_delta = period2 - period1
    busy_delta = busy2 - busy1

    if period_delta <= 0:
        print(0)
        return

    percentage = max(0.0, min(100.0, busy_delta / period_delta * 100))
    print(round(percentage))


if __name__ == "__main__":
    main()
