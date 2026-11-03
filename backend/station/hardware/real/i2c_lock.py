"""Shared lock for I2C bus 1.

All devices on bus 1 (LCD, gas sensor) must acquire this lock before
any I2C transaction to prevent bus contention.
"""
from __future__ import annotations

import threading

BUS_1_LOCK = threading.Lock()
