from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .google_services_detector import detect_services

@csrf_exempt  # For testing only - remove in production!
@require_http_methods(["POST"])
def analyze_intent(request):
    try:
        # Parse JSON body
        data = json.loads(request.body)
        text = data.get('text', '')
        
        if not text:
            return JsonResponse({
                'error': 'Text parameter is required'
            }, status=400)
        
        # Detect services
        services = detect_services(text)
        
        return JsonResponse({
            'success': True,
            'text': text,
            'services': services
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)