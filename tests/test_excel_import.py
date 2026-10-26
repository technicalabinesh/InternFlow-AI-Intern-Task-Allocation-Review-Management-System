"""Tests for Excel import, validation, error detection, and export."""

import io
import datetime
import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Intern, Task, TaskAssignment
from services.excel_service import ExcelService
from config.settings import EXCEL_COLUMNS


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_blank_template_has_all_24_columns():
    content = ExcelService.generate_blank_template()
    assert content is not None
    df = pd.read_excel(io.BytesIO(content))
    assert list(df.columns) == EXCEL_COLUMNS
    assert len(df.columns) == 24


def test_sample_105_interns_generation_and_validation():
    content = ExcelService.generate_sample_100_interns()
    is_valid, df, errors, summary = ExcelService.parse_and_validate(content, "sample.xlsx")
    assert is_valid is True
    assert len(errors) == 0
    assert len(df) == 105
    assert summary["unique_interns"] == 105
    assert summary["valid_rows"] == 105


def test_detect_missing_columns():
    df = pd.DataFrame({
        "Intern_ID": ["INT-101"],
        "Intern_Name": ["Test Intern"],
    })
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    is_valid, parsed_df, errors, summary = ExcelService.parse_and_validate(buf.getvalue(), "bad.xlsx")
    assert is_valid is False
    assert any("Missing mandatory columns" in e["error"] for e in errors)


def test_detect_invalid_email_and_invalid_date():
    rows = []
    # Build complete row with bad email and bad date
    row = {col: "Test" for col in EXCEL_COLUMNS}
    row["Intern_ID"] = "INT-999"
    row["Email"] = "invalid-email-address"
    row["Deadline"] = "not-a-date"
    row["Meeting_Link"] = "not_a_valid_url_at_all"
    rows.append(row)

    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    df.to_excel(buf, index=False)

    is_valid, parsed_df, errors, summary = ExcelService.parse_and_validate(buf.getvalue(), "invalid.xlsx")
    assert is_valid is False
    error_texts = [e["error"] for e in errors]
    assert any("Invalid email format" in err for err in error_texts)
    assert any("Invalid date in Deadline" in err for err in error_texts)


def test_import_to_database_and_export(test_db):
    content = ExcelService.generate_sample_100_interns()
    is_valid, df, errors, summary = ExcelService.parse_and_validate(content, "sample.xlsx")
    assert is_valid is True

    result = ExcelService.import_to_database(df, test_db, user_email="admin@internflow.ai")
    assert result["interns_upserted"] == 105
    assert result["assignments_upserted"] == 105

    # Check database counts
    assert test_db.query(Intern).count() == 105
    assert test_db.query(TaskAssignment).count() == 105

    # Export back to Excel
    exported_bytes = ExcelService.export_from_database(test_db)
    assert exported_bytes is not None
    exported_df = pd.read_excel(io.BytesIO(exported_bytes))
    assert len(exported_df) == 105
    assert list(exported_df.columns) == EXCEL_COLUMNS
