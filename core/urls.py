
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
path('admin/', admin.site.urls),
path('', include('pos.urls')),
path('settings/', include('settings_app.urls')),
path('reports/', include('reports.urls')),
]
