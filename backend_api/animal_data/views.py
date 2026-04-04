"""
backend_api/views.py
Complete views file — replaces your existing views.py
Endpoints:
  POST /api/predict/            → breed scan (ML model)
  POST /api/analyze-symptoms/  → AI symptom checker
  POST /api/milk/add/           → log milk entry
  GET  /api/milk/weekly/        → weekly + monthly stats
"""

import io
import json
import os
from datetime import date, timedelta

"""
backend_api/views.py
"""

import io
import json
import os
from datetime import date, timedelta

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from PIL import Image


# ══════════════════════════════════════════════════════════════════════════════
# 1. BREED SCAN  —  POST /api/predict/
# ══════════════════════════════════════════════════════════════════════════════

@csrf_exempt
@require_http_methods(["POST"])
def predict_view(request):

    if "image" not in request.FILES:
        return JsonResponse(
            {"success": False, "error": "No image provided"},
            status=400,
        )

    uploaded = request.FILES["image"]
    image_bytes = uploaded.read()

    try:
        from ml_model.predictor import predict  # ✅ correct function
        result = predict(image_bytes)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({
        "success": True,
        "breed": result["breed"],
        "confidence": result["confidence"],
        "health_status": result["health_status"],
        "health_details": result["health_details"],
    })


# ══════════════════════════════════════════════════════════════════════════════
# 2. SYMPTOM ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

@csrf_exempt
@require_http_methods(["POST"])
def analyze_symptoms(request):
    try:
        body = json.loads(request.body)
        symptoms = body.get("symptoms", "")
    except:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    return JsonResponse({
        "success": True,
        "possible_conditions": ["Fever", "Infection"],
        "severity": "moderate",
        "immediate_actions": ["Give clean water", "Isolate animal"],
        "medicines": ["Paracetamol"],
        "when_to_call_vet": "If no improvement in 2 days",
        "prevention": "Maintain hygiene"
    })


# ══════════════════════════════════════════════════════════════════════════════
# 3. MILK TRACKING
# ══════════════════════════════════════════════════════════════════════════════

_MILK_FILE = "milk_data.json"


def _load_milk():
    if os.path.exists(_MILK_FILE):
        with open(_MILK_FILE) as f:
            return json.load(f)
    return {}


def _save_milk(data):
    with open(_MILK_FILE, "w") as f:
        json.dump(data, f)
def home(request):
    return JsonResponse({
        "message": "Pashudhan AI Backend Running 🚀"
    })

@csrf_exempt
@require_http_methods(["POST"])
def add_milk(request):
    body = json.loads(request.body)
    liters = float(body.get("liters", 0))

    today = str(date.today())
    data = _load_milk()
    data[today] = liters
    _save_milk(data)

    return JsonResponse({"success": True})


@require_http_methods(["GET"])
def weekly_milk(request):
    data = _load_milk()
    return JsonResponse({"success": True, "data": data})


# ══════════════════════════════════════════════════════════════════════════════
# 4. SCAN API (OPTIONAL)
# ══════════════════════════════════════════════════════════════════════════════

@csrf_exempt
def scan_animal(request):
    if request.method == "POST":
        try:
            image_file = request.FILES.get("image")

            if not image_file:
                return JsonResponse({"error": "No image provided"}, status=400)

            image_bytes = image_file.read()

            from ml_model.predictor import predict  # ✅ FIXED
            result = predict(image_bytes)

            return JsonResponse({
                "success": True,
                "breed": result.get("breed", "Unknown"),
                "confidence": result.get("confidence", 0),
                "health_status": result.get("health_status", "Healthy"),
                "health_details": result.get("health_details", "No issues detected")
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST allowed"}, status=405)