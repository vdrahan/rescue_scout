from __future__ import annotations

import re
import subprocess
import time
from typing import Callable


def get_interface_ip(interface: str, timeout_s: float = 2.0) -> str:
    try:
        output = subprocess.check_output(
            ["ip", "-4", "addr", "show", interface],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=timeout_s,
        )
    except Exception:
        return "-"
    match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", output)
    return match.group(1) if match else "-"


def get_host_interface_ips(timeout_s: float = 2.0) -> tuple[str, str]:
    """LAN / Wi-Fi IPv4 from `ip -4 addr show` on eth0 and wlan0."""
    return get_interface_ip("eth0", timeout_s), get_interface_ip("wlan0", timeout_s)


def wait_for_host_interface_ips(
    max_wait_s: float = 25.0,
    poll_s: float = 1.0,
    on_wait: Callable[[str], None] | None = None,
    lookup_timeout_s: float = 2.0,
) -> tuple[str, str]:
    deadline = time.time() + max(0.0, max_wait_s)
    last_lan, last_wifi = "-", "-"
    wait_tick = 0
    while time.time() < deadline:
        lan_ip, wifi_ip = get_host_interface_ips(timeout_s=lookup_timeout_s)
        last_lan, last_wifi = lan_ip, wifi_ip
        if lan_ip != "-" or wifi_ip != "-":
            return lan_ip, wifi_ip
        if on_wait is not None:
            dots = "." * ((wait_tick % 3) + 1)
            on_wait(f"Network wait{dots}")
            wait_tick += 1
        time.sleep(max(0.1, poll_s))
    return last_lan, last_wifi


def request_sudo_poweroff() -> None:
    """Trigger shutdown via sudo (NOPASSWD expected). Runs detached so HTTP can respond."""
    try:
        subprocess.Popen(
            ["sudo", "poweroff"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as exc:
        print(f"[POWEROFF] sudo poweroff failed to start: {exc}")
