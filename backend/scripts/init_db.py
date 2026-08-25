import _bootstrap  # noqa: F401

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.database import Base, engine
from app.db import models  # noqa: F401


Base.metadata.create_all(bind=engine)

# Older local databases may predate the ORM uniqueness declaration. Before
# adding the index, detect duplicates so the upgrade fails with a useful
# message instead of an opaque SQLite/PostgreSQL IntegrityError.
with engine.begin() as connection:
    duplicates = connection.execute(
        text(
            "SELECT message_id, COUNT(*) AS n "
            "FROM cases GROUP BY message_id HAVING COUNT(*) > 1 LIMIT 10"
        )
    ).fetchall()

if duplicates:
    examples = ", ".join(f"{row[0]} ({row[1]} rows)" for row in duplicates)
    raise SystemExit(
        "Database upgrade stopped: duplicate case message IDs exist. "
        f"Resolve the duplicates first. Examples: {examples}"
    )

try:
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "uq_cases_message_id ON cases (message_id)"
            )
        )
except IntegrityError as exc:
    raise SystemExit(
        "Could not create the Gmail idempotency index. Check existing case "
        "message IDs before continuing."
    ) from exc

print("Database ready. Gmail message idempotency index verified.")
