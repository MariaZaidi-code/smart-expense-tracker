import os
import tempfile

db_file = tempfile.mktemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"

import app.config  # noqa: E402
app.config.settings.database_url = os.environ["DATABASE_URL"]

import app.db as dbmod  # noqa: E402
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

dbmod.engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
dbmod.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=dbmod.engine)

import app.deps as depsmod  # noqa: E402
depsmod.SessionLocal = dbmod.SessionLocal

from app.main import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
