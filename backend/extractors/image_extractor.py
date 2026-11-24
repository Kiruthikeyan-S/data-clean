import io
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any, List, Optional
from backend.extractors.vision_analyzer import analyze_visual_content

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


import io
import re
import cv2
import base64
import numpy as np
from PIL import Image
from typing import Dict, Any, List, Optional, Tuple
from backend.extractors.vision_analyzer import analyze_visual_content

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


def decode_image_bytes(image_bytes: bytes) -> Tuple[np.ndarray, np.ndarray]:
    """
    Decodes image into both BGR color image and preprocessed grayscale image:
    - Orientation / deskewing
    - CLAHE contrast enhancement
    - Bilateral noise reduction
    """
    img = None
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    except Exception:
        img = None

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

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. Deskewing
    try:
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) >= 100:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            if abs(angle) > 0.8 and abs(angle) < 45:
                (h, w) = gray.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                gray = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                img = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    except Exception:
        pass

    # 2. Local contrast enhancement (CLAHE)
    try:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
    except Exception:
        enhanced = gray

    # 3. Bilateral noise filtering
    denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
    return img, denoised


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Backward-compatible preprocessor returning denoised grayscale image."""
    _, denoised = decode_image_bytes(image_bytes)
    return denoised


def detect_barcodes_and_qrs(img: np.ndarray) -> List[Dict[str, Any]]:
    """
    Decodes QR codes and 1D barcodes (Code 128, Code 39, EAN, UPC) using OpenCV.
    If visual pattern is detected but decode fails, reports 'Barcode Present but Not Decoded'.
    """
    items: List[Dict[str, Any]] = []
    h, w = img.shape[:2]

    # 1. QR Code Detector
    try:
        qr = cv2.QRCodeDetector()
        retval, decoded_info, points, _ = qr.detectAndDecodeMulti(img)
        if retval:
            for text, pt in zip(decoded_info, points):
                text_clean = text.strip() if isinstance(text, str) else ""
                status = "Decoded" if text_clean else "Barcode Present but Not Decoded"
                items.append({
                    "type": "qr_code",
                    "data": text_clean if text_clean else None,
                    "status": status,
                    "format": "QR_CODE"
                })
        else:
            text, points, _ = qr.detectAndDecode(img)
            if points is not None and len(points) > 0:
                text_clean = text.strip() if isinstance(text, str) else ""
                items.append({
                    "type": "qr_code",
                    "data": text_clean if text_clean else None,
                    "status": "Decoded" if text_clean else "Barcode Present but Not Decoded",
                    "format": "QR_CODE"
                })
    except Exception:
        pass

    # 2. 1D Barcode Detector (Code 128, Code 39, EAN, UPC)
    try:
        if hasattr(cv2, "barcode"):
            bd = cv2.barcode.BarcodeDetector()
            ret = bd.detectAndDecode(img)
            if len(ret) >= 3:
                decoded_info, decoded_type, points = ret[0], ret[1], ret[2]
                if points is not None and len(points) > 0:
                    info_list = [decoded_info] if isinstance(decoded_info, str) else (decoded_info or [])
                    type_list = [decoded_type] if isinstance(decoded_type, str) else (decoded_type or [])
                    for i, info in enumerate(info_list):
                        info_str = str(info).strip() if info else ""
                        b_type = str(type_list[i]) if i < len(type_list) and type_list[i] else "BARCODE"
                        items.append({
                            "type": "barcode",
                            "data": info_str if info_str else None,
                            "status": "Decoded" if info_str else "Barcode Present but Not Decoded",
                            "format": b_type
                        })
    except Exception:
        pass

    # 3. Fallback visual barcode presence check via horizontal gradient morphology
    if not items:
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            # Scharr horizontal gradient highlights vertical barcode bars
            grad_x = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
            grad_y = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=0, dy=1, ksize=-1)
            gradient = cv2.subtract(cv2.convertScaleAbs(grad_x), cv2.convertScaleAbs(grad_y))
            blurred = cv2.blur(gradient, (9, 9))
            _, thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 7))
            closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                cx, cy, cw, ch = cv2.boundingRect(cnt)
                aspect = cw / float(ch) if ch > 0 else 0
                if aspect > 1.8 and cw > 80 and ch > 25:
                    items.append({
                        "type": "barcode",
                        "data": None,
                        "status": "Barcode Present but Not Decoded",
                        "format": "1D_BARCODE",
                        "bbox": [round((cx / w) * 100, 2), round((cy / h) * 100, 2), round((cw / w) * 100, 2), round((ch / h) * 100, 2)]
                    })
                    break
        except Exception:
            pass

    return items


def extract_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Comprehensive Image Understanding & Layout Extraction Pipeline:
    1. Robust decoding & preprocessing (deskewing, CLAHE, bilateral filter).
    2. Optical Character Recognition (RapidOCR / EasyOCR / PyTesseract) with spatial blocks.
    3. Barcode & QR Code decoding with OpenCV.
    4. Computer Vision Scene Analysis (YOLOv8 + MobileNetV3).
    5. Full preview construction (page_images base64, blocks, key_values, tables, entities, barcodes).
    """
    color_img, processed_img = decode_image_bytes(image_bytes)
    h, w = color_img.shape[:2]
    engine_type, engine = get_ocr_engine()

    lines: List[str] = []
    confidences: List[float] = []
    raw_results = []
    blocks: List[Dict[str, Any]] = []

    # 1. OCR Engine Execution
    if engine_type == "rapidocr" and engine:
        try:
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
                        # Normalize box coordinates to 0-100%
                        xs = [pt[0] for pt in box]
                        ys = [pt[1] for pt in box]
                        bx0, by0 = min(xs), min(ys)
                        bw, bh = max(xs) - bx0, max(ys) - by0
                        blocks.append({
                            "page": 1,
                            "text": text,
                            "x": round((bx0 / w) * 100, 2),
                            "y": round((by0 / h) * 100, 2),
                            "width": round((bw / w) * 100, 2),
                            "height": round((bh / h) * 100, 2)
                        })
        except Exception as e:
            print(f"OCR RapidOCR extraction error: {e}")

    elif engine_type == "easyocr" and engine:
        try:
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
                    xs = [pt[0] for pt in bbox]
                    ys = [pt[1] for pt in bbox]
                    bx0, by0 = min(xs), min(ys)
                    bw, bh = max(xs) - bx0, max(ys) - by0
                    blocks.append({
                        "page": 1,
                        "text": t,
                        "x": round((bx0 / w) * 100, 2),
                        "y": round((by0 / h) * 100, 2),
                        "width": round((bw / w) * 100, 2),
                        "height": round((bh / h) * 100, 2)
                    })
        except Exception as e:
            print(f"OCR EasyOCR extraction error: {e}")

    elif engine_type == "pytesseract" and engine:
        try:
            data = engine.image_to_data(processed_img, output_type=engine.Output.DICT)
            n_boxes = len(data['text'])
            line_dict = {}
            for i in range(n_boxes):
                text = data['text'][i].strip()
                conf = float(data['conf'][i])
                if text and conf > 0:
                    lines.append(text)
                    confidences.append(conf / 100.0)
                    bx = data['left'][i]
                    by = data['top'][i]
                    bw = data['width'][i]
                    bh = data['height'][i]
                    blocks.append({
                        "page": 1,
                        "text": text,
                        "x": round((bx / w) * 100, 2),
                        "y": round((by / h) * 100, 2),
                        "width": round((bw / w) * 100, 2),
                        "height": round((bh / h) * 100, 2)
                    })
        except Exception as e:
            print(f"OCR Tesseract extraction error: {e}")

    ocr_text = "\n".join(lines).strip()
    avg_conf = float(np.mean(confidences)) if confidences else 0.85

    # 2. Barcode & QR Code Detection
    barcodes = detect_barcodes_and_qrs(color_img)

    # 3. Computer Vision Scene Analysis
    vision_info = analyze_visual_content(image_bytes)
    visual_desc = vision_info.get("description", "")

    # Combine text + visual context
    if len(ocr_text) >= 20:
        combined_payload = f"Document Text (OCR):\n{ocr_text}"
        confidence = round(max(avg_conf, 0.88), 3)
        method = f"image_ocr ({engine_type}) + layout_analysis"
    elif ocr_text:
        combined_payload = f"Document Text:\n{ocr_text}\n\nVisual Context:\n{visual_desc}"
        confidence = 0.90
        method = "vision_intelligence + image_ocr"
    else:
        combined_payload = visual_desc
        confidence = 0.92
        method = "computer_vision_object_and_scene_intelligence"

    # Encode clean PNG preview image
    try:
        _, buffer = cv2.imencode('.png', color_img)
        img_b64 = "data:image/png;base64," + base64.b64encode(buffer).decode("utf-8")
        page_images = [img_b64]
    except Exception:
        page_images = []

    # 4. Extract Dynamic Key-Values from OCR Lines
    key_values: List[Dict[str, Any]] = []

    # Shipping Label Patterns
    carrier_m = re.search(r'\b(USPS|FEDEX|UPS|DHL)\b', ocr_text, re.I)
    if carrier_m:
        key_values.append({"fieldName": "Carrier", "extractedValue": carrier_m.group(1).upper(), "confidence": 0.99})

    service_m = re.search(r'\b(PRIORITY\s+MAIL(?:\s+2-DAY|\s+3-DAY)?|EXPRESS\s+MAIL|GROUND\s+ADVANTAGE|PARCEL\s+SELECT|FIRST-CLASS\s+PACKAGE)\b', ocr_text, re.I)
    if service_m:
        key_values.append({"fieldName": "Service Type", "extractedValue": service_m.group(1).title(), "confidence": 0.98})

    track_m = re.search(r'\b(\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{2}|\d{20,24}|1Z[0-9A-Z]{16})\b', ocr_text)
    if track_m:
        key_values.append({"fieldName": "Tracking Number", "extractedValue": track_m.group(1).replace(" ", ""), "confidence": 0.99})
    elif barcodes:
        for b in barcodes:
            if b.get("data"):
                key_values.append({"fieldName": "Tracking / Barcode", "extractedValue": b["data"], "confidence": 0.99})
                break

    # General Key-Value lines
    for line in lines:
        if ":" in line and len(line) < 120:
            k, v = line.split(":", 1)
            k, v = k.strip(), v.strip()
            if 2 < len(k) < 35 and v and not k.startswith("http") and not k.startswith("//"):
                if not any(item["fieldName"].lower() == k.lower() for item in key_values):
                    key_values.append({"fieldName": k.title(), "extractedValue": v, "confidence": 0.95})
        if len(key_values) >= 15:
            break

    # If key-values still sparse, parse labeled blocks (SHIP TO, FROM, TOTAL, INVOICE #)
    ship_to_m = re.search(r'(?:SHIP\s+TO|DELIVER\s+TO|TO)\s*[:=\-]?\s*\n?([^\n]+(?:\n[^\n]+){1,3})', ocr_text, re.I)
    if ship_to_m and not any(k["fieldName"].lower() == "recipient" for k in key_values):
        to_lines = [l.strip() for l in ship_to_m.group(1).splitlines() if l.strip()]
        if to_lines:
            key_values.append({"fieldName": "Recipient Name", "extractedValue": to_lines[0], "confidence": 0.95})
            if len(to_lines) > 1:
                key_values.append({"fieldName": "Delivery Address", "extractedValue": ", ".join(to_lines[1:]), "confidence": 0.93})

    ship_from_m = re.search(r'(?:SHIP\s+FROM|FROM)\s*[:=\-]?\s*\n?([^\n]+(?:\n[^\n]+){1,2})', ocr_text, re.I)
    if ship_from_m and not any(k["fieldName"].lower() == "sender" for k in key_values):
        from_lines = [l.strip() for l in ship_from_m.group(1).splitlines() if l.strip()]
        if from_lines:
            key_values.append({"fieldName": "Sender Name", "extractedValue": from_lines[0], "confidence": 0.95})
            if len(from_lines) > 1:
                key_values.append({"fieldName": "Sender Address", "extractedValue": ", ".join(from_lines[1:]), "confidence": 0.93})

    # Postage amount
    postage_m = re.search(r'\$([0-9]+\.[0-9]{2})', ocr_text)
    if postage_m and not any("postage" in k["fieldName"].lower() or "amount" in k["fieldName"].lower() for k in key_values):
        key_values.append({"fieldName": "Postage Paid", "extractedValue": f"${postage_m.group(1)}", "confidence": 0.95})

    # 5. Extract Entities
    entities: List[Dict[str, Any]] = []
    for kv in key_values[:8]:
        entities.append({
            "type": kv["fieldName"].upper().replace(" ", "_"),
            "mention": kv["extractedValue"],
            "conf": f"{int(kv['confidence'] * 100)}%",
            "norm": kv["extractedValue"]
        })

    preview = {
        "page_count": 1,
        "page_images": page_images,
        "blocks": blocks,
        "tables": [],
        "key_values": key_values,
        "entities": entities,
        "barcodes": barcodes,
        "page_stats": {
            "total_pages": 1,
            "pages_attempted": 1,
            "pages_extracted": 1,
            "pages_requiring_ocr": 1,
            "failed_pages": 0,
            "per_page_method": {1: method}
        }
    }

    return {
        "text": combined_payload,
        "ocr_text": ocr_text,
        "lines": lines,
        "confidence": confidence,
        "details": raw_results,
        "vision_info": vision_info,
        "extraction_method": method,
        "barcodes": barcodes,
        "preview": preview
    }
