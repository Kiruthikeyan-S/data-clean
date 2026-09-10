import io
from typing import Dict, Any, List, Optional
import numpy as np
from PIL import Image

_yolo_model = None
_mobilenet_model = None
_mobilenet_weights = None
_mobilenet_transforms = None

def get_vision_models():
    global _yolo_model, _mobilenet_model, _mobilenet_weights, _mobilenet_transforms
    if _mobilenet_model is None:
        try:
            import torchvision.models as models
            from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small
            import torch
            _mobilenet_weights = MobileNet_V3_Small_Weights.DEFAULT
            _mobilenet_model = mobilenet_v3_small(weights=_mobilenet_weights)
            _mobilenet_model.eval()
            _mobilenet_transforms = _mobilenet_weights.transforms()
        except Exception as e:
            print(f"MobileNet load error: {e}")
            _mobilenet_model = None

    if _yolo_model is None:
        try:
            from ultralytics import YOLO
            _yolo_model = YOLO("yolov8n.pt")
        except Exception as e:
            print(f"YOLO load error: {e}")
            _yolo_model = None

    return _yolo_model, _mobilenet_model, _mobilenet_transforms, _mobilenet_weights


def analyze_visual_content(image_bytes: bytes) -> Dict[str, Any]:
    """
    Analyzes visual images (photos of food, objects, products, nature, scenes)
    using computer vision models (YOLO + MobileNet) and visual heuristics.
    """
    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
    except Exception as e:
        return {"error": f"Image decode failed: {e}"}

    width, height = pil_img.size
    yolo, mobilenet, transforms, weights = get_vision_models()

    detected_objects: List[Dict[str, Any]] = []
    top_categories: List[Dict[str, Any]] = []

    # 1. YOLO Object Detection
    if yolo is not None:
        try:
            results = yolo(pil_img, verbose=False)
            if results and len(results) > 0:
                boxes = results[0].boxes
                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    name = results[0].names.get(cls_id, f"object_{cls_id}")
                    if conf >= 0.25:
                        detected_objects.append({
                            "label": name.replace("_", " ").title(),
                            "confidence": round(conf, 2),
                            "class_id": cls_id
                        })
        except Exception as e:
            print(f"YOLO inference error: {e}")

    # 2. MobileNet Classification (Top 5 ImageNet classes)
    if mobilenet is not None and transforms is not None and weights is not None:
        try:
            import torch
            input_tensor = transforms(pil_img).unsqueeze(0)
            with torch.no_grad():
                prediction = mobilenet(input_tensor).squeeze(0).softmax(0)
                top5_prob, top5_catid = torch.topk(prediction, 5)
                categories = weights.meta["categories"]
                for i in range(5):
                    cat_name = categories[top5_catid[i].item()]
                    prob = float(top5_prob[i].item())
                    if prob >= 0.05:
                        top_categories.append({
                            "category": cat_name.replace("_", " ").title(),
                            "probability": round(prob * 100, 1)
                        })
        except Exception as e:
            print(f"MobileNet inference error: {e}")

    # 3. Dominant Color Estimation
    img_small = pil_img.resize((50, 50))
    colors = img_small.getcolors(maxcolors=2500)
    dominant_color_names = []
    if colors:
        sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)[:3]
        for count, (r, g, b) in sorted_colors:
            if r > 180 and g > 180 and b > 180:
                dominant_color_names.append("White / Light")
            elif r < 50 and g < 50 and b < 50:
                dominant_color_names.append("Black / Dark")
            elif r > g and r > b:
                dominant_color_names.append("Red / Brown / Warm")
            elif g > r and g > b:
                dominant_color_names.append("Green")
            elif b > r and b > g:
                dominant_color_names.append("Blue")
            elif r > 150 and g > 120 and b < 80:
                dominant_color_names.append("Golden / Yellow / Fried")
            else:
                dominant_color_names.append(f"RGB({r},{g},{b})")

    # 4. Summarize visual scene
    objects_summary = ", ".join([f"{o['label']} ({int(o['confidence']*100)}%)" for o in detected_objects]) if detected_objects else "No distinct isolated bounding objects"
    categories_summary = ", ".join([f"{c['category']} ({c['probability']}%)" for c in top_categories]) if top_categories else "General visual image"

    visual_description = (
        f"Visual Image Analysis (Dimensions: {width}x{height}px):\n"
        f"- Top Recognized Visual Categories: {categories_summary}\n"
        f"- Detected Specific Objects: {objects_summary}\n"
        f"- Dominant Colors: {', '.join(set(dominant_color_names)) if dominant_color_names else 'Natural'}\n"
    )

    return {
        "width": width,
        "height": height,
        "detected_objects": detected_objects,
        "top_categories": top_categories,
        "dominant_colors": list(set(dominant_color_names)),
        "description": visual_description
    }
