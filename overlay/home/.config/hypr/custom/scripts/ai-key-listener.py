#!/usr/bin/env python3
import re
import struct
import subprocess
import sys
import time
from pathlib import Path

DEVICE_NAME = "AT Translated Set 2 keyboard"

# Every numeric KEY_* code known to this kernel's input-event-codes.h,
# except KEY_UNKNOWN (240) which is deliberately treated as "unknown" below.
# Regenerate with:
#   python3 -c "import re; print(sorted({int(m.group(2),0) for l in open('/usr/include/linux/input-event-codes.h') for m in [re.match(r'^#define\s+KEY_(\w+)\s+(0x[0-9a-fA-F]+|\d+)\b', l.strip())] if m} - {240}))"
KNOWN_KEY_CODES = frozenset([
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
    21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
    39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56,
    57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74,
    75, 76, 77, 78, 79, 80, 81, 82, 83, 85, 86, 87, 88, 89, 90, 91, 92, 93,
    94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109,
    110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123,
    124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137,
    138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151,
    152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165,
    166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179,
    180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193,
    194, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212,
    213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226,
    227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 241,
    242, 243, 244, 245, 246, 247, 248, 352, 353, 354, 355, 356, 357, 358,
    359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372,
    373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386,
    387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400,
    401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414,
    415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428,
    429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442,
    444, 445, 446, 447, 448, 449, 450, 451, 464, 465, 466, 467, 468, 469,
    470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480, 481, 482, 483,
    484, 485, 497, 498, 499, 500, 501, 502, 503, 504, 505, 506, 512, 513,
    514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525, 526, 527,
    528, 529, 530, 531, 532, 533, 534, 535, 536, 537, 538, 539, 540, 541,
    542, 560, 561, 562, 576, 577, 578, 579, 580, 581, 582, 583, 584, 585,
    586, 587, 588, 589, 590, 591, 592, 593, 594, 595, 596, 597, 598, 608,
    609, 610, 611, 612, 613, 614, 615, 616, 617, 618, 619, 620, 621, 622,
    623, 624, 625, 626, 627, 628, 629, 630, 631, 632, 633, 634, 635, 636,
    637, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649, 656,
    657, 658, 659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670,
    671, 672, 673, 674, 675, 676, 677, 678, 679, 680, 681, 682, 683, 684,
    685, 688, 689, 690, 691, 692, 693, 696, 697, 698, 699, 700, 701, 767,
])

EV_KEY = 1
KEY_UNKNOWN = 240
VALUE_PRESSED = 1

EVENT_FORMAT = "qqHHi"
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)

DEBOUNCE_SECONDS = 1.0

ACTION_COMMAND = ["hyprctl", "dispatch", "hl.dsp.global('quickshell:sidebarRightOpen')"]


def find_device_path(name):
    devices_text = Path("/proc/bus/input/devices").read_text()
    for block in devices_text.split("\n\n"):
        if f'N: Name="{name}"' not in block:
            continue
        m = re.search(r"H: Handlers=.*?(event\d+)", block)
        if m:
            return Path("/dev/input") / m.group(1)
    return None


def is_unknown_key(code):
    return code == KEY_UNKNOWN or code not in KNOWN_KEY_CODES


def trigger_action():
    subprocess.run(ACTION_COMMAND, check=False)


def watch(device_path):
    last_trigger = 0.0
    with device_path.open("rb") as f:
        while True:
            data = f.read(EVENT_SIZE)
            if len(data) != EVENT_SIZE:
                return
            _, _, ev_type, code, value = struct.unpack(EVENT_FORMAT, data)
            if ev_type != EV_KEY or value != VALUE_PRESSED:
                continue
            if not is_unknown_key(code):
                continue
            now = time.monotonic()
            if now - last_trigger < DEBOUNCE_SECONDS:
                continue
            last_trigger = now
            trigger_action()


def main():
    while True:
        device_path = find_device_path(DEVICE_NAME)
        if device_path is None or not device_path.exists():
            time.sleep(5)
            continue
        try:
            watch(device_path)
        except (OSError, struct.error) as e:
            print(f"ai-key-listener: {e}, retrying", file=sys.stderr)
        time.sleep(2)


if __name__ == "__main__":
    main()
