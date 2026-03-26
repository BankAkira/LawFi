"""Seed script -- populate the database with sample data for development.

Usage:
    python -m scripts.seed

Idempotent: safe to run multiple times. Skips records that already exist.
"""

import bcrypt
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base
from app.models.ruling import CaseType, Ruling, RulingResult
from app.models.user import SubscriptionTier, User

SYNC_DB_URL = settings.database_url.replace("+asyncpg", "+psycopg2")

SAMPLE_RULINGS = [
    {
        "ruling_number": "1001/2565",
        "year": 2565,
        "case_type": CaseType.CIVIL,
        "result": RulingResult.UPHELD,
        "summary": "จำเลยผิดสัญญาซื้อขายที่ดิน โจทก์มีสิทธิเรียกค่าเสียหาย",
        "facts": "โจทก์ทำสัญญาซื้อขายที่ดินกับจำเลย จำเลยไม่โอนกรรมสิทธิ์ตามสัญญา",
        "issues": "จำเลยผิดสัญญาหรือไม่ โจทก์มีสิทธิเรียกค่าเสียหายเพียงใด",
        "judgment": "ศาลฎีกาเห็นพ้องกับศาลอุทธรณ์ว่าจำเลยผิดสัญญา พิพากษายืน",
        "keywords": ["สัญญาซื้อขาย", "ที่ดิน", "ค่าเสียหาย", "ผิดสัญญา"],
        "referenced_sections": ["ป.พ.พ. มาตรา 453", "ป.พ.พ. มาตรา 222"],
    },
    {
        "ruling_number": "2345/2564",
        "year": 2564,
        "case_type": CaseType.CRIMINAL,
        "result": RulingResult.REVERSED,
        "summary": "จำเลยถูกฟ้องฐานฉ้อโกง ศาลฎีกากลับคำพิพากษาศาลอุทธรณ์",
        "facts": "จำเลยหลอกลวงผู้เสียหายให้โอนเงินโดยอ้างว่าจะนำไปลงทุน",
        "issues": "การกระทำของจำเลยเป็นความผิดฐานฉ้อโกงหรือไม่",
        "judgment": "ศาลฎีกาเห็นว่าพยานหลักฐานโจทก์ไม่เพียงพอ กลับคำพิพากษา",
        "keywords": ["ฉ้อโกง", "พยานหลักฐาน", "การลงทุน"],
        "referenced_sections": ["ป.อ. มาตรา 341", "ป.วิ.อ. มาตรา 227"],
    },
    {
        "ruling_number": "789/2566",
        "year": 2566,
        "case_type": CaseType.LABOR,
        "result": RulingResult.MODIFIED,
        "summary": "นายจ้างเลิกจ้างไม่เป็นธรรม ศาลแก้ค่าชดเชย",
        "facts": "ลูกจ้างทำงานมา 10 ปี ถูกเลิกจ้างโดยไม่มีเหตุอันสมควร",
        "issues": "การเลิกจ้างเป็นธรรมหรือไม่ ค่าชดเชยเท่าใด",
        "judgment": "ศาลฎีกาแก้คำพิพากษาเรื่องค่าชดเชยเป็น 300 วัน",
        "keywords": ["เลิกจ้าง", "ค่าชดเชย", "แรงงาน", "ไม่เป็นธรรม"],
        "referenced_sections": ["พ.ร.บ.คุ้มครองแรงงาน มาตรา 118"],
    },
    {
        "ruling_number": "456/2563",
        "year": 2563,
        "case_type": CaseType.CIVIL,
        "result": RulingResult.DISMISSED,
        "summary": "โจทก์ฟ้องละเมิดจากอุบัติเหตุรถยนต์ ศาลยกฟ้อง",
        "facts": "โจทก์ขับรถชนจำเลย โจทก์อ้างว่าจำเลยประมาท",
        "issues": "ฝ่ายใดเป็นผู้ประมาท โจทก์มีส่วนผิดหรือไม่",
        "judgment": "ศาลฎีกาเห็นว่าโจทก์เป็นฝ่ายประมาทเอง พิพากษายกฟ้อง",
        "keywords": ["ละเมิด", "อุบัติเหตุ", "รถยนต์", "ประมาท"],
        "referenced_sections": ["ป.พ.พ. มาตรา 420", "ป.พ.พ. มาตรา 442"],
    },
    {
        "ruling_number": "3210/2565",
        "year": 2565,
        "case_type": CaseType.CRIMINAL,
        "result": RulingResult.UPHELD,
        "summary": "จำเลยมีความผิดฐานยักยอกทรัพย์ ศาลฎีกายืนตามศาลอุทธรณ์",
        "facts": "จำเลยเป็นพนักงานบริษัท ยักยอกเงินบริษัทไป 5 ล้านบาท",
        "issues": "จำเลยกระทำผิดฐานยักยอกทรัพย์หรือไม่ ลงโทษสถานใด",
        "judgment": "ศาลฎีกาพิพากษายืน จำคุก 3 ปี",
        "keywords": ["ยักยอกทรัพย์", "พนักงาน", "บริษัท"],
        "referenced_sections": ["ป.อ. มาตรา 352"],
    },
    {
        "ruling_number": "567/2567",
        "year": 2567,
        "case_type": CaseType.FAMILY,
        "result": RulingResult.MODIFIED,
        "summary": "คดีหย่า ศาลแก้เรื่องอำนาจปกครองบุตร",
        "facts": "สามีภริยาฟ้องหย่า มีบุตร 2 คน ทั้งสองฝ่ายต้องการอำนาจปกครอง",
        "issues": "อำนาจปกครองบุตรควรอยู่กับฝ่ายใด",
        "judgment": "ศาลฎีกาแก้ให้มารดาเป็นผู้ใช้อำนาจปกครองบุตรทั้งสอง",
        "keywords": ["หย่า", "อำนาจปกครอง", "บุตร", "ครอบครัว"],
        "referenced_sections": ["ป.พ.พ. มาตรา 1520", "ป.พ.พ. มาตรา 1566"],
    },
    {
        "ruling_number": "890/2566",
        "year": 2566,
        "case_type": CaseType.TAX,
        "result": RulingResult.APPEAL_DISMISSED,
        "summary": "ผู้เสียภาษีอุทธรณ์การประเมินภาษีเงินได้นิติบุคคล ศาลยกอุทธรณ์",
        "facts": "บริษัทถูกประเมินภาษีเพิ่มเติม 10 ล้านบาท อ้างว่าคำนวณผิด",
        "issues": "การประเมินของเจ้าพนักงานชอบด้วยกฎหมายหรือไม่",
        "judgment": "ศาลฎีกาเห็นว่าการประเมินถูกต้อง พิพากษายกอุทธรณ์",
        "keywords": ["ภาษีเงินได้", "นิติบุคคล", "ประเมินภาษี"],
        "referenced_sections": ["ป.รัษฎากร มาตรา 65"],
    },
    {
        "ruling_number": "1111/2564",
        "year": 2564,
        "case_type": CaseType.INTELLECTUAL_PROPERTY,
        "result": RulingResult.UPHELD,
        "summary": "จำเลยละเมิดลิขสิทธิ์ซอฟต์แวร์ ศาลยืนตามศาลชั้นต้น",
        "facts": "จำเลยทำซ้ำและจำหน่ายซอฟต์แวร์ของโจทก์โดยไม่ได้รับอนุญาต",
        "issues": "การกระทำของจำเลยเป็นการละเมิดลิขสิทธิ์หรือไม่",
        "judgment": "ศาลฎีกาพิพากษายืน สั่งให้ชดใช้ค่าเสียหาย 2 ล้านบาท",
        "keywords": ["ลิขสิทธิ์", "ซอฟต์แวร์", "ทำซ้ำ", "ทรัพย์สินทางปัญญา"],
        "referenced_sections": ["พ.ร.บ.ลิขสิทธิ์ มาตรา 27", "พ.ร.บ.ลิขสิทธิ์ มาตรา 69"],
    },
    {
        "ruling_number": "2222/2563",
        "year": 2563,
        "case_type": CaseType.CIVIL,
        "result": RulingResult.UPHELD,
        "summary": "ผู้ค้ำประกันต้องรับผิดตามสัญญาค้ำประกัน",
        "facts": "จำเลยที่ 1 กู้เงิน จำเลยที่ 2 เป็นผู้ค้ำประกัน จำเลยที่ 1 ผิดนัด",
        "issues": "ผู้ค้ำประกันต้องรับผิดเพียงใด สิทธิไล่เบี้ยมีหรือไม่",
        "judgment": "ศาลฎีกายืน ผู้ค้ำประกันต้องรับผิดเต็มจำนวน",
        "keywords": ["ค้ำประกัน", "กู้ยืมเงิน", "ผิดนัด", "ไล่เบี้ย"],
        "referenced_sections": ["ป.พ.พ. มาตรา 680", "ป.พ.พ. มาตรา 693"],
    },
    {
        "ruling_number": "3333/2567",
        "year": 2567,
        "case_type": CaseType.CRIMINAL,
        "result": RulingResult.MODIFIED,
        "summary": "จำเลยทำร้ายร่างกายผู้อื่น ศาลแก้โทษจำคุก",
        "facts": "จำเลยทำร้ายร่างกายผู้เสียหายจนได้รับบาดเจ็บสาหัส",
        "issues": "ควรลงโทษจำเลยสถานใด มีเหตุบรรเทาโทษหรือไม่",
        "judgment": "ศาลฎีกาแก้ลดโทษจำคุกเหลือ 1 ปี เนื่องจากมีเหตุบรรเทาโทษ",
        "keywords": ["ทำร้ายร่างกาย", "บาดเจ็บสาหัส", "บรรเทาโทษ"],
        "referenced_sections": ["ป.อ. มาตรา 297", "ป.อ. มาตรา 78"],
    },
]


def seed():
    """Insert sample users and rulings into the database."""
    engine = create_engine(SYNC_DB_URL)
    Base.metadata.create_all(engine)
    session = Session(engine)

    # --- Users ---
    admin_email = "admin@lawfi.com"
    existing_admin = session.execute(
        select(User).where(User.email == admin_email)
    ).scalar_one_or_none()

    if not existing_admin:
        admin = User(
            email=admin_email,
            password_hash=bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode(),
            name="Admin",
            subscription_tier=SubscriptionTier.ENTERPRISE,
        )
        session.add(admin)
        print(f"  Created admin user: {admin_email}")

    test_email = "user@lawfi.com"
    existing_test = session.execute(
        select(User).where(User.email == test_email)
    ).scalar_one_or_none()

    if not existing_test:
        test_user = User(
            email=test_email,
            password_hash=bcrypt.hashpw(b"user1234", bcrypt.gensalt()).decode(),
            name="Test User",
            subscription_tier=SubscriptionTier.FREE,
        )
        session.add(test_user)
        print(f"  Created test user: {test_email}")

    # --- Rulings ---
    created = 0
    for ruling_data in SAMPLE_RULINGS:
        existing = session.execute(
            select(Ruling).where(Ruling.ruling_number == ruling_data["ruling_number"])
        ).scalar_one_or_none()

        if existing:
            continue

        ruling = Ruling(
            full_text=f"คำพิพากษาฎีกาที่ {ruling_data['ruling_number']} {ruling_data['facts']} {ruling_data['judgment']}",
            is_processed=True,
            **ruling_data,
        )
        session.add(ruling)
        created += 1

    session.commit()
    session.close()
    engine.dispose()
    print(f"  Created {created} rulings ({len(SAMPLE_RULINGS) - created} already existed)")
    print("Seed complete.")


if __name__ == "__main__":
    seed()
