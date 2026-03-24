"""Extract structured data from ruling text using Claude (Anthropic)."""

import json

import anthropic

from app.config import settings

EXTRACTION_PROMPT = """คุณเป็นผู้เชี่ยวชาญด้านกฎหมายไทย กรุณาวิเคราะห์คำพิพากษาศาลฎีกาต่อไปนี้ แล้วแยกข้อมูลออกมาเป็น JSON

ข้อมูลที่ต้องแยก:
1. ruling_number: เลขฎีกา (เช่น "1234/2565")
2. year: ปี พ.ศ. (ตัวเลข)
3. date: วันที่พิพากษา (รูปแบบ YYYY-MM-DD ถ้ามี, ใช้ปี ค.ศ.)
4. case_type: ประเภทคดี (เลือกจาก: แพ่ง, อาญา, แรงงาน, ภาษี, ทรัพย์สินทางปัญญา, ล้มละลาย, ปกครอง, ครอบครัว, เยาวชน, สิ่งแวดล้อม, อื่นๆ)
5. division: แผนก (ถ้ามี)
6. result: ผลคำพิพากษา (เลือกจาก: ยืน, กลับ, แก้, ยกฟ้อง, ยกอุทธรณ์, กลับอุทธรณ์, อื่นๆ)
7. summary: สรุปย่อคำพิพากษา (2-3 ประโยค)
8. facts: ข้อเท็จจริง (สรุปสาระสำคัญ)
9. issues: ประเด็นที่ศาลวินิจฉัย
10. judgment: คำวินิจฉัยของศาล
11. keywords: คำสำคัญ (array ของ string, 3-10 คำ)
12. referenced_sections: มาตราที่อ้างอิง (array ของ string, เช่น ["ป.พ.พ. มาตรา 420", "ป.อ. มาตรา 157"])

ตอบเป็น JSON เท่านั้น ไม่ต้องมีคำอธิบายอื่น ถ้าไม่พบข้อมูลใดให้ใส่ null

คำพิพากษา:
{text}"""


class RulingExtractor:
    """Extract structured data from ruling text using Claude."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def extract(self, ruling_text: str) -> dict:
        """Extract structured data from ruling text.

        Returns a dict with all fields, or raises on failure.
        """
        # Truncate very long texts to fit context window
        max_chars = 180_000  # ~45K tokens for Claude
        if len(ruling_text) > max_chars:
            ruling_text = ruling_text[:max_chars]

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(text=ruling_text),
                }
            ],
        )

        response_text = message.content[0].text.strip()

        # Parse JSON from response (handle markdown code blocks)
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        return json.loads(response_text)

    def extract_batch(self, texts: list[str]) -> list[dict]:
        """Extract structured data from multiple ruling texts."""
        results = []
        for text in texts:
            try:
                result = self.extract(text)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})
        return results
