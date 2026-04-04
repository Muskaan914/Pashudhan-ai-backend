"""
ml_model/predictor.py — uses Claude Vision API (no TensorFlow needed)
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
            raise ValueError("ANTHROPIC_API_KEY not set in environment variables")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def predict(image_bytes: bytes) -> dict:
    # Resize image to reduce API payload
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((512, 512))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    img_b64 = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")

    client = _get_client()

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=300,
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
                        "text": """Analyze this livestock image. Respond ONLY with a JSON object, no markdown:
{
  "breed": "detected breed name or Cow or Buffalo or Unknown",
  "confidence": 90,
  "health_status": "Healthy or Unhealthy",
  "health_details": "brief observation about coat, body condition, visible issues"
}"""
                    }
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

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
    
    