import io
import json
import os
from datetime import date, timedelta

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


# ── Home ──────────────────────────────────────────────────────────────────────
def home(request):
    return JsonResponse({"message": "Pashudhan AI Backend Running 🚀"})


# ── 1. Breed Scan  POST /api/predict/ ────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def predict_view(request):
    if "image" not in request.FILES:
        return JsonResponse({"success": False, "error": "No image provided"}, status=400)

    image_bytes = request.FILES["image"].read()

    try:
        from ml_model.predictor import predict
        result = predict(image_bytes)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({
        "success":        True,
        "breed":          result["breed"],
        "confidence":     result["confidence"],
        "health_status":  result["health_status"],
        "health_details": result["health_details"],
    })


# ── 2. Symptom Analysis  POST /api/analyze-symptoms/ ─────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def analyze_symptoms(request):
    try:
        body     = json.loads(request.body)
        symptoms = body.get("symptoms", "").strip()
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    if not symptoms:
        return JsonResponse({"success": False, "error": "symptoms field required"}, status=400)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return JsonResponse({"success": False, "error": "ANTHROPIC_API_KEY not set"}, status=500)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=600,
            system="""You are an expert AI veterinarian for Indian livestock.
Respond ONLY with a JSON object, no markdown:
{
  "possible_conditions": ["condition1", "condition2"],
  "severity": "mild or moderate or severe",
  "immediate_actions": ["action1", "action2"],
  "medicines": ["medicine (dosage)"],
  "when_to_call_vet": "explanation",
  "prevention": "tip"
}""",
            messages=[{"role": "user", "content": f"Symptoms: {symptoms}"}],
        )

        raw    = msg.content[0].text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
        return JsonResponse({"success": True, **result})

    except json.JSONDecodeError:
        return JsonResponse({"success": True, "raw_advice": raw})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# ── 3. Milk Tracking ─────────────────────────────────────────────────────────
_MILK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "milk_data.json")


def _load_milk():
    if os.path.exists(_MILK_FILE):
        with open(_MILK_FILE) as f:
            return json.load(f)
    return {}


def _save_milk(data):
    with open(_MILK_FILE, "w") as f:
        json.dump(data, f)


@csrf_exempt
@require_http_methods(["POST"])
def add_milk(request):
    try:
        body   = json.loads(request.body)
        liters = float(body.get("liters", 0))
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid body"}, status=400)

    if liters <= 0:
        return JsonResponse({"success": False, "error": "liters must be > 0"}, status=400)

    today = str(date.today())
    data  = _load_milk()
    data[today] = liters
    _save_milk(data)

    return JsonResponse({"success": True, "date": today, "liters": liters})


@require_http_methods(["GET"])
def weekly_milk(request):
    data  = _load_milk()
    today = date.today()

    weekly = []
    for i in range(6, -1, -1):
        day     = today - timedelta(days=i)
        day_str = str(day)
        weekly.append({
            "date":   day_str,
            "day":    day.strftime("%a"),
            "liters": data.get(day_str, 0),
        })

    monthly = [data[str(today - timedelta(days=i))]
               for i in range(30)
               if str(today - timedelta(days=i)) in data]

    monthly_avg = round(sum(monthly) / len(monthly), 1) if monthly else 0

    return JsonResponse({
        "success":         True,
        "weekly":          weekly,
        "monthly_average": monthly_avg,
    })