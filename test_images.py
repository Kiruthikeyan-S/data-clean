import io
from PIL import Image, ImageDraw
from backend.pipeline import process_file_pipeline

def test_image_types():
    # 1. Standard RGB PNG with text
    img1 = Image.new("RGB", (600, 200), color=(255, 255, 255))
    d1 = ImageDraw.Draw(img1)
    d1.text((20, 20), "Employee ID: EMP-9982\nName: Alice Wonderland\nEmail: alice@wonderland.io\nSalary: $95,000", fill=(0, 0, 0))
    buf1 = io.BytesIO()
    img1.save(buf1, format="PNG")
    res1 = process_file_pipeline("employee_badge.png", "image/png", buf1.getvalue())
    print("PNG with text status:", res1.status, "Extracted text len:", len(res1.raw_text or ''))
    assert res1.status == "completed"

    # 2. RGBA with Alpha Channel
    img2 = Image.new("RGBA", (500, 150), color=(240, 240, 240, 255))
    d2 = ImageDraw.Draw(img2)
    d2.text((20, 20), "Invoice Number: INV-2026-001\nTotal: $450.00\nDate: 2026-09-09", fill=(10, 10, 10, 255))
    buf2 = io.BytesIO()
    img2.save(buf2, format="PNG")
    res2 = process_file_pipeline("invoice_rgba.png", "image/png", buf2.getvalue())
    print("RGBA PNG status:", res2.status, "Extracted text len:", len(res2.raw_text or ''))
    assert res2.status == "completed"

    # 3. JPEG format
    buf3 = io.BytesIO()
    img1.convert("RGB").save(buf3, format="JPEG")
    res3 = process_file_pipeline("photo.jpg", "image/jpeg", buf3.getvalue())
    print("JPEG status:", res3.status, "Extracted text len:", len(res3.raw_text or ''))
    assert res3.status == "completed"

    print("ALL IMAGE TEST CASES PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_image_types()
