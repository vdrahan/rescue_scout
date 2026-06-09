from __future__ import annotations

import time

from config import AppConfig
from hardware.lcd_service import LCDService
from hardware.network import wait_for_host_interface_ips


def lcd_startup_network_carousel(cfg: AppConfig, lcd: LCDService) -> None:
    """Daemon thread: wait for network, then rotate LAN/WIFI IPs on the LCD."""
    lan_ip, wifi_ip = wait_for_host_interface_ips(
        max_wait_s=25.0,
        poll_s=1.0,
        on_wait=lambda msg: lcd.show_lines("Status: WAITING", msg, force=True),
    )
    startup_pages = [("LAN", lan_ip), ("WIFI", wifi_ip)]
    page_interval_s = 1.2
    deadline = time.time() + max(0.0, cfg.startup_ip_seconds)
    page_idx = 0
    while time.time() < deadline:
        label, ip_value = startup_pages[page_idx % len(startup_pages)]
        lcd.show_lines(f"{label} IP", ip_value, force=True)
        page_idx += 1
        sleep_for = min(page_interval_s, max(0.0, deadline - time.time()))
        if sleep_for <= 0:
            break
        time.sleep(sleep_for)
    lcd.show_waiting()
