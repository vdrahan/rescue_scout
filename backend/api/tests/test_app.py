from __future__ import annotations

from contextlib import contextmanager

import pytest
from fastapi import HTTPException

pytest.importorskip('psycopg2')


def test_health_checks_database_readiness(monkeypatch) -> None:
    from backend.api import main

    checks: list[str] = []
    monkeypatch.setattr(main, 'db_health', lambda: checks.append('database'))

    assert main.health() == {'status': 'ok', 'service': 'api'}
    assert checks == ['database']


def test_db_health_raises_503_when_database_is_unavailable(monkeypatch) -> None:
    from backend.api import main

    @contextmanager
    def unavailable_db():
        raise RuntimeError('database offline')
        yield

    monkeypatch.setattr(main, 'db', unavailable_db)

    with pytest.raises(HTTPException) as exc_info:
        main.db_health()

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == 'Database unavailable'
