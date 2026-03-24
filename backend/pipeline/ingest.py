"""Main ingestion pipeline: PDF -> OCR -> Extract -> Embed -> Store.

Usage:
    python -m pipeline.ingest --pdf-dir /path/to/pdfs --batch-size 10
"""

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base
from app.models.ruling import CaseType, Ruling, RulingResult
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService
from pipeline.extractor import RulingExtractor
from pipeline.ocr import OCRService
from pipeline.storage import R2Storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Sync engine for pipeline (not async)
SYNC_DB_URL = settings.database_url.replace("+asyncpg", "+psycopg2")


def get_sync_session() -> Session:
    """Create a synchronous database session for the pipeline."""
    engine = create_engine(SYNC_DB_URL)
    Base.metadata.create_all(engine)
    return Session(engine)


def parse_case_type(value: str | None) -> CaseType | None:
    """Parse case type string to enum."""
    if value is None:
        return None
    for ct in CaseType:
        if ct.value == value:
            return ct
    return CaseType.OTHER


def parse_result(value: str | None) -> RulingResult | None:
    """Parse ruling result string to enum."""
    if value is None:
        return None
    for rr in RulingResult:
        if rr.value == value:
            return rr
    return RulingResult.OTHER


def process_single_pdf(
    pdf_path: Path,
    ocr: OCRService,
    extractor: RulingExtractor,
    embedding_service: EmbeddingService,
    qdrant: QdrantService,
    r2: R2Storage,
    session: Session,
) -> bool:
    """Process a single PDF through the full pipeline.

    Returns True on success, False on failure.
    """
    filename = pdf_path.name
    logger.info(f"Processing: {filename}")

    try:
        # Step 1: OCR -- extract text from PDF
        logger.info(f"  [1/5] OCR: extracting text...")
        raw_text = ocr.extract_text_from_pdf(pdf_path)
        if not raw_text or len(raw_text.strip()) < 50:
            logger.warning(f"  Skipped: insufficient text extracted from {filename}")
            return False

        # Step 2: Claude -- extract structured data
        logger.info(f"  [2/5] Claude: extracting structured data...")
        extracted = extractor.extract(raw_text)

        ruling_number = extracted.get("ruling_number")
        if not ruling_number:
            logger.warning(f"  Skipped: no ruling number found in {filename}")
            return False

        # Check if already exists
        existing = session.execute(
            select(Ruling).where(Ruling.ruling_number == ruling_number)
        ).scalar_one_or_none()
        if existing:
            logger.info(f"  Skipped: ruling {ruling_number} already exists")
            return True

        # Step 3: Upload PDF to R2
        logger.info(f"  [3/5] R2: uploading PDF...")
        object_key = f"rulings/{ruling_number.replace('/', '_')}.pdf"
        pdf_url = r2.upload_pdf(pdf_path, object_key)

        # Step 4: Generate embedding
        logger.info(f"  [4/5] Vertex AI: generating embedding...")
        # Combine summary + facts + issues for embedding
        embed_text = " ".join(
            filter(
                None,
                [
                    extracted.get("summary", ""),
                    extracted.get("facts", ""),
                    extracted.get("issues", ""),
                    extracted.get("judgment", ""),
                ],
            )
        )
        embedding = embedding_service.embed_text(embed_text[:10000])

        # Step 5: Store in PG + Qdrant
        logger.info(f"  [5/5] Storing in PG + Qdrant...")
        ruling = Ruling(
            ruling_number=ruling_number,
            year=extracted.get("year", 0),
            date=_parse_date(extracted.get("date")),
            case_type=parse_case_type(extracted.get("case_type")),
            division=extracted.get("division"),
            result=parse_result(extracted.get("result")),
            summary=extracted.get("summary"),
            facts=extracted.get("facts"),
            issues=extracted.get("issues"),
            judgment=extracted.get("judgment"),
            full_text=raw_text,
            keywords=extracted.get("keywords"),
            referenced_sections=extracted.get("referenced_sections"),
            pdf_url=pdf_url,
            is_processed=True,
        )
        session.add(ruling)
        session.flush()  # Get ruling.id

        # Upsert to Qdrant
        qdrant_id = qdrant.upsert_ruling(
            ruling_id=ruling.id,
            embedding=embedding,
            metadata={
                "ruling_number": ruling_number,
                "year": ruling.year,
                "case_type": ruling.case_type.value if ruling.case_type else "",
                "result": ruling.result.value if ruling.result else "",
                "keywords": ruling.keywords or [],
            },
        )
        ruling.qdrant_id = qdrant_id
        session.commit()

        logger.info(f"  Done: {ruling_number} (ID={ruling.id})")
        return True

    except Exception as e:
        logger.error(f"  Failed: {filename} -- {e}")
        session.rollback()

        # Store error for later retry
        try:
            ruling = Ruling(
                ruling_number=filename,
                year=0,
                full_text=raw_text if "raw_text" in dir() else "",
                is_processed=False,
                processing_error=str(e),
            )
            session.add(ruling)
            session.commit()
        except Exception:
            session.rollback()

        return False


def _parse_date(date_str: str | None) -> datetime | None:
    """Parse date string from Claude output."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def run_pipeline(pdf_dir: str, batch_size: int = 10) -> None:
    """Run the full ingestion pipeline on a directory of PDFs."""
    pdf_dir = Path(pdf_dir)
    if not pdf_dir.exists():
        logger.error(f"Directory not found: {pdf_dir}")
        sys.exit(1)

    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    total = len(pdf_files)
    logger.info(f"Found {total} PDF files in {pdf_dir}")

    # Initialize services
    ocr = OCRService()
    extractor = RulingExtractor()
    embedding_service = EmbeddingService()
    qdrant = QdrantService()
    qdrant.ensure_collection()
    r2 = R2Storage()
    session = get_sync_session()

    success = 0
    failed = 0

    for i, pdf_path in enumerate(pdf_files, 1):
        logger.info(f"[{i}/{total}] ({success} ok, {failed} failed)")

        result = process_single_pdf(
            pdf_path, ocr, extractor, embedding_service, qdrant, r2, session
        )

        if result:
            success += 1
        else:
            failed += 1

        # Rate limiting: avoid hitting API quotas
        if i % batch_size == 0:
            logger.info(f"Batch complete. Pausing 2s...")
            time.sleep(2)

    session.close()
    logger.info(f"Pipeline complete: {success} success, {failed} failed, {total} total")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LawFi PDF ingestion pipeline")
    parser.add_argument(
        "--pdf-dir", required=True, help="Directory containing PDF files"
    )
    parser.add_argument(
        "--batch-size", type=int, default=10, help="Pause every N files"
    )
    args = parser.parse_args()

    run_pipeline(args.pdf_dir, args.batch_size)
