from django.urls import path
from . import views

urlpatterns = [
    path('api/detect-services/', views.analyze_intent, name='detect_services'),
]