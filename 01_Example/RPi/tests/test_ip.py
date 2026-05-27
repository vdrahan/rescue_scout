#!/usr/bin/env python3
"""
Smoke test: print IPv4 addresses using hardware.network (same as the kickoff app).

Run on the Pi (from repo root or from RPi/):
    python RPi/tests/test_ip.py
    cd RPi && python tests/test_ip.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_RPI_ROOT = Path(__file__).resolve().parents[1]
if str(_RPI_ROOT) not in sys.path:
    sys.path.insert(0, str(_RPI_ROOT))

from hardware.network import get_host_interface_ips, get_interface_ip


def main() -> None:
    print("=== IP smoke test (hardware.network) ===\n")

    eth0 = get_interface_ip("eth0")
    wlan0 = get_interface_ip("wlan0")
    lan_ip, wifi_ip = get_host_interface_ips()

    print(f"eth0 (LAN)  : {eth0}")
    print(f"wlan0 (WiFi): {wlan0}")
    print()
    print(f"get_host_interface_ips() -> LAN={lan_ip!r}, WIFI={wifi_ip!r}")

    if lan_ip == "-" and wifi_ip == "-":
        print("\nNo IPv4 on eth0 or wlan0 yet (cable/WiFi or DHCP).")
    else:
        print("\nAt least one interface has an address.")


if __name__ == "__main__":
    main()
