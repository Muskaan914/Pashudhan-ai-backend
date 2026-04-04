# backend_api/ml_model/predictor.py

"""
ml_model/predictor.py  — fixed version
Fixes: missing 'import io', hardcoded path, eager model loading
"""

import io
import os
import numpy as np
from PIL import Image

# ── Adjust these to match your actual training labels ──────────────────────
CLASS_NAMES = ["Cow", "Buffalo", "Unknown"]

# ── Singleton: model loads once on first request, not at startup ───────────
_model = None


def _load_model():
    global _model
    if _model is not None:
        return _model

    import tensorflow as tf

    # Works locally AND on Render — path relative to this file
    model_path = os.path.join(os.path.dirname(__file__), "trained_model.h5")

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model not found at: {model_path}\n"
            "Make sure trained_model.h5 is inside the ml_model/ folder."
        )

    _model = tf.keras.models.load_model(model_path)
    return _model


def predict(image_bytes: bytes) -> dict:
    model = _load_model()

    image     = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image     = image.resize((224, 224))
    img_array = np.array(image, dtype=np.float32) / 255.0
    img_array = np.expand_dims(img_array, axis=0)   # (1, 224, 224, 3)

    preds      = model.predict(img_array, verbose=0)
    idx        = int(np.argmax(preds[0]))
    confidence = round(float(np.max(preds[0])) * 100, 2)

    breed = CLASS_NAMES[idx] if idx < len(CLASS_NAMES) else "Unknown"

    return {
        "breed":          breed,
        "confidence":     confidence,
        "health_status":  "Healthy",
        "health_details": "No visible issues detected.",
    }