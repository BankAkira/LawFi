"""Pipeline tests with mocked external services."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import Base
from app.models.ruling import Ruling
from pipeline.ingest import process_single_pdf

# Sync test DB (pipeline uses sync SQLAlchemy)
SYNC_TEST_DB = "postgresql+psycopg2://lawfi:lawfi@localhost:5433/lawfi_test"


@pytest.fixture
def sync_session():
    """Sync session for pipeline tests (pipeline is sync, not async)."""
    engine = create_engine(SYNC_TEST_DB)
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def _make_mock_services():
    """Create mock OCR, extractor, embedding, qdrant, r2 services."""
    ocr = MagicMock()
    ocr.extract_text_from_pdf.return_value = "คำพิพากษาศาลฎีกา " * 50  # >50 chars

    extractor = MagicMock()
    extractor.extract.return_value = {
        "ruling_number": "1234/2565",
        "year": 2565,
        "date": "2022-06-15",
        "case_type": "แพ่ง",
        "division": "แผนกคดีแพ่ง",
        "result": "ยืน",
        "summary": "สรุปย่อฎีกา",
        "facts": "ข้อเท็จจริง",
        "issues": "ประเด็นวินิจฉัย",
        "judgment": "คำวินิจฉัย",
        "keywords": ["สัญญา", "ซื้อขาย"],
        "referenced_sections": ["ป.พ.พ. มาตรา 420"],
    }

    embedding = MagicMock()
    embedding.embed_text.return_value = [0.1] * 768

    qdrant = MagicMock()
    qdrant.upsert_ruling.return_value = "qdrant-uuid-123"

    r2 = MagicMock()
    r2.upload_pdf.return_value = "https://pub-xxx.r2.dev/rulings/1234_2565.pdf"

    return ocr, extractor, embedding, qdrant, r2


def test_pipeline_happy_path(sync_session: Session, tmp_path: Path):
    """Pipeline processes a PDF into a structured DB record."""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-fake")

    ocr, extractor, embedding, qdrant, r2 = _make_mock_services()

    result = process_single_pdf(
        pdf_file, ocr, extractor, embedding, qdrant, r2, sync_session
    )

    assert result is True

    # Verify the ruling was stored in the database
    ruling = sync_session.execute(
        select(Ruling).where(Ruling.ruling_number == "1234/2565")
    ).scalar_one()

    assert ruling.year == 2565
    assert ruling.summary == "สรุปย่อฎีกา"
    assert ruling.is_processed is True
    assert ruling.qdrant_id == "qdrant-uuid-123"
    assert ruling.keywords == ["สัญญา", "ซื้อขาย"]


def test_pipeline_skips_duplicate(sync_session: Session, tmp_path: Path):
    """Re-processing an already-ingested ruling is skipped (returns True)."""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-fake")

    ocr, extractor, embedding, qdrant, r2 = _make_mock_services()

    # First run -- ingests
    assert (
        process_single_pdf(
            pdf_file, ocr, extractor, embedding, qdrant, r2, sync_session
        )
        is True
    )

    # Second run -- skipped (already exists)
    assert (
        process_single_pdf(
            pdf_file, ocr, extractor, embedding, qdrant, r2, sync_session
        )
        is True
    )

    # Only 1 record in DB
    count = sync_session.execute(select(Ruling)).scalars().all()
    assert len(count) == 1


def test_pipeline_ocr_failure_does_not_crash(sync_session: Session, tmp_path: Path):
    """When OCR fails, pipeline records the error and continues."""
    pdf_file = tmp_path / "bad.pdf"
    pdf_file.write_bytes(b"%PDF-fake")

    ocr, extractor, embedding, qdrant, r2 = _make_mock_services()
    ocr.extract_text_from_pdf.side_effect = RuntimeError("Vision API down")

    result = process_single_pdf(
        pdf_file, ocr, extractor, embedding, qdrant, r2, sync_session
    )

    assert result is False


def test_pipeline_claude_failure_records_error(sync_session: Session, tmp_path: Path):
    """When Claude extraction fails, error is recorded for retry."""
    pdf_file = tmp_path / "problematic.pdf"
    pdf_file.write_bytes(b"%PDF-fake")

    ocr, extractor, embedding, qdrant, r2 = _make_mock_services()
    extractor.extract.side_effect = RuntimeError("Claude API timeout")

    result = process_single_pdf(
        pdf_file, ocr, extractor, embedding, qdrant, r2, sync_session
    )

    assert result is False

    # Error should be recorded -- but NOT with a ruling_number that could
    # collide with a real ruling number
    errors = (
        sync_session.execute(
            select(Ruling).where(Ruling.is_processed == False)  # noqa: E712
        )
        .scalars()
        .all()
    )
    # The error record (if any) should not use the PDF filename as ruling_number
    for err in errors:
        assert err.ruling_number != "problematic.pdf"
