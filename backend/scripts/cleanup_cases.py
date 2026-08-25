import _bootstrap  # noqa: F401
import argparse

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.db.repository import CaseRepository


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--days",
        type=int,
        default=get_settings().data_retention_days,
    )
    args = parser.parse_args()

    with SessionLocal() as db:
        result = CaseRepository(db).cleanup_older_than(args.days)

    print(
        " | ".join(
            [
                f"Deleted cases: {result['deleted_cases']}",
                f"actions: {result['deleted_actions']}",
                f"corrections: {result['deleted_corrections']}",
                f"simulations: {result['deleted_simulations']}",
            ]
        )
    )


if __name__ == "__main__":
    main()
