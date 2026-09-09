import io
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any, List, Optional

# Lazy load OCR engine
_ocr_engine = None

def get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _ocr_engine = ("rapidocr", RapidOCR())
        except Exception:
            try:
                import easyocr
                _ocr_engine = ("easyocr", easyocr.Reader(['en'], gpu=False))
            except Exception:
                try:
                    import pytesseract
                    _ocr_engine = ("pytesseract", pytesseract)
                except Exception:
                    _ocr_engine = ("none", None)
    return _ocr_engine


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Applies robust image decoding (OpenCV with PIL fallback) and preprocessing:
    - Decodes image via cv2.imdecode or PIL.Image.open
    - Converts to RGB/Grayscale
    - Noise reduction (bilateral filter)
    """
    img = None
    
    # 1. Try OpenCV decode
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    except Exception:
        img = None

    # 2. Fallback to PIL decode (handles CMYK, RGBA, WebP, progressive, etc.)
    if img is None:
        try:
            pil_img = Image.open(io.BytesIO(image_bytes))
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")
            img_np = np.array(pil_img)
            img = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        except Exception as e:
            raise ValueError(f"Could not decode image format: {str(e)}")

    if img is None:
        raise ValueError("Could not decode image. Supported formats include PNG, JPG, JPEG, WEBP, BMP, TIFF.")
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Noise reduction
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)
    return denoised


def extract_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Extracts text, confidence scores, and line blocks from image bytes using OpenCV & OCR.
    """
    processed_img = preprocess_image(image_bytes)
    engine_type, engine = get_ocr_engine()
    
    lines: List[str] = []
    confidences: List[float] = []
    raw_results = []
    
    if engine_type == "rapidocr" and engine:
        result, elapse_list = engine(processed_img)
        if result:
            for item in result:
                box = item[0]
                text = item[1].strip()
                score = float(item[2])
                if text:
                    lines.append(text)
                    confidences.append(score)
                    raw_results.append({
                        "text": text,
                        "confidence": score,
                        "bbox": box
                    })
    elif engine_type == "easyocr" and engine:
        result = engine.readtext(processed_img)
        for bbox, text, score in result:
            t = text.strip()
            if t:
                lines.append(t)
                confidences.append(float(score))
                raw_results.append({
                    "text": t,
                    "confidence": float(score),
                    "bbox": [list(pt) for pt in bbox]
                })
    elif engine_type == "pytesseract" and engine:
        data = engine.image_to_data(processed_img, output_type=engine.Output.DICT)
        n_boxes = len(data['text'])
        line_dict = {}
        for i in range(n_boxes):
            text = data['text'][i].strip()
            conf = float(data['conf'][i])
            if text and conf > 0:
                line_num = data['line_num'][i]
                line_dict.setdefault(line_num, []).append(text)
                confidences.append(conf / 100.0)
        for lnum in sorted(line_dict.keys()):
            lines.append(" ".join(line_dict[lnum]))
    else:
        lines = []
        confidences = [0.0]

    full_text = "\n".join(lines).strip()
    avg_conf = float(np.mean(confidences)) if confidences else 0.0

    return {
        "text": full_text,
        "lines": lines,
        "confidence": round(avg_conf, 3),
        "details": raw_results,
        "extraction_method": f"image_ocr ({engine_type})"
    }
