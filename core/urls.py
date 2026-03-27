
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pos.urls')),
    path('inventory/', include('inventory.urls')),
    path('accounts/', include('accounts.urls')),
    path('reports/', include('reports.urls')),
    path('settings/', include('settings_app.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
