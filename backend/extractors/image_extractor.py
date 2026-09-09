import io
import cv2
import numpy as np
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
    Applies OpenCV preprocessing:
    - Decodes image
    - Converts to grayscale
    - Noise reduction (bilateral filter)
    - Contrast enhancement / thresholding when appropriate
    """
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image.")
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Noise reduction
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # Adaptive thresholding / contrast adjustment if needed
    # We return the denoised image as standard high-quality OCR input
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
                # item format: [box, text, score]
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
        # Fallback if no OCR is available
        lines = ["[OCR Engine not configured]"]
        confidences = [0.0]

    full_text = "\n".join(lines)
    avg_conf = float(np.mean(confidences)) if confidences else 0.0

    return {
        "text": full_text,
        "lines": lines,
        "confidence": round(avg_conf, 3),
        "details": raw_results
    }
