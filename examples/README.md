# Reference Material

This directory preserves the original Project One starter application,
documentation, and Raspberry Pi hardware smoke tests. It is useful for tracing
the project's development and for device-level checks, but it is not imported by
or copied into the deployed application.

Active runtime code:

- backend/api: PostgreSQL data API
- backend/station: detection, cameras, and hardware service
- frontend: Gradio operator interface

Run the system and its automated tests using the commands in the root README.md.
Run scripts under examples/RPi/tests manually on Raspberry Pi hardware; they are
smoke-test utilities, not pytest unit tests.
