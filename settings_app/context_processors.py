
from .models import AppSettings


def app_settings(request):
    settings = AppSettings.get_settings()
    return {'app_settings': settings}
