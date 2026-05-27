# `services` — start and stop the app

Only one job: call the other packages in the right order.

| Function | What it does |
|----------|----------------|
| `bootstrap_app()` | LCD (`hardware/setup`) → models → inputs; GPIO started in `ui/dashboard` (`start_gpio`) |
| `shutdown_app()` | Stop GPIO button, close cameras, close models, `GPIO.cleanup()` |

**Students:** you usually edit `hardware/`, `models/registry.py`, or `inputs/registry.py` — not this folder.
