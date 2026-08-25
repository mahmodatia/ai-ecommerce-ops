import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["AI_PROVIDER"] = "rules"
os.environ["SHOPIFY_MODE"] = "mock"
os.environ["GMAIL_MODE"] = "mock"
os.environ["TASKS_MODE"] = "sync"

import pytest

from app.core.config import get_settings
get_settings.cache_clear()

from app.core.database import Base, engine


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def pytest_sessionfinish(session, exitstatus):
    Base.metadata.drop_all(bind=engine)
    path = Path("test.db")
    if path.exists():
        try:
            path.unlink()
        except PermissionError:
            pass
