# backend_api/urls.py
from django.urls import path
from animal_data import views

 
urlpatterns = [
    path("", views.home),
    path("api/predict/",           views.predict_view,    name="predict"),
    path("api/analyze-symptoms/",  views.analyze_symptoms, name="analyze_symptoms"),
    path("api/milk/add/",          views.add_milk,         name="add_milk"),
    path("api/milk/weekly/",       views.weekly_milk,      name="weekly_milk"),

    
    path("api/scan/", views.scan_animal),
]
 