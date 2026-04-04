"""
ml_model/predictor.py — uses Claude Vision API (fast Haiku model)
"""

import io
import os
import base64
import json
import anthropic
from PIL import Image


_client = None

def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def predict(image_bytes: bytes) -> dict:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((512, 512))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    img_b64 = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")

    client = _get_client()

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",   # ← fast model, no timeout
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": 'You are a livestock expert. Look at this image carefully. Is it a cow or buffalo? What specific breed? Reply ONLY with JSON, no markdown, no extra text:\n{"breed": "exact breed name like Holstein Friesian or Gir Cow or Sahiwal or Murrah Buffalo", "confidence": 85, "health_status": "Healthy or Unhealthy", "health_details": "one sentence about coat and body condition"}'
                ],
            }
        ],
    )

    raw = message.content[0].text.strip().replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(raw)
        return {
            "breed":          result.get("breed", "Unknown"),
            "confidence":     result.get("confidence", 85),
            "health_status":  result.get("health_status", "Healthy"),
            "health_details": result.get("health_details", "No visible issues detected."),
        }
    except Exception:
        return {
            "breed":          "Unknown",
            "confidence":     0,
            "health_status":  "Unknown",
            "health_details": raw,
        }