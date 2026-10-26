"""Seed database with sample 105 interns, tasks, and demo data if empty."""

import sys
from pathlib import Path

# Ensure workspace root is in path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.connection import init_db, get_db
from database.models import Intern, TaskAssignment
from services.excel_service import ExcelService


def seed_database_if_empty():
    init_db()
    with get_db() as db:
        intern_count = db.query(Intern).count()
        if intern_count < 10:
            print("Database has fewer than 10 interns. Generating 105 sample interns...")
            sample_bytes = ExcelService.generate_sample_100_interns()
            is_valid, df, errors, summary = ExcelService.parse_and_validate(sample_bytes, "sample.xlsx")
            if is_valid and df is not None:
                res = ExcelService.import_to_database(df, db, user_email="system@internflow.ai")
                print(f"Seeded: {res}")
            else:
                print(f"Error validating sample: {errors}")
        else:
            print(f"Database already populated with {intern_count} interns.")


if __name__ == "__main__":
    seed_database_if_empty()
