# unit tests for db layer

import pytest
from sqlmodel import Session

from social_media_app.db import (
    create_db_and_tables,
    make_engine,
)


@pytest.fixture
def session():
    # Fresh in-memory DB per test
    engine = make_engine(sqlite_memory=True)
    create_db_and_tables(engine)
    with Session(engine) as s:
        yield s


# ToDo add tests