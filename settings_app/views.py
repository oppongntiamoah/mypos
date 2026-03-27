
from django.shortcuts import render
from .models import AppSettings

def settings_view(request):
    obj=AppSettings.objects.first()
    return render(request,'settings.html',{'settings':obj})
