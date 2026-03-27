
from django.shortcuts import render
from pos.models import Sale

def dashboard(request):
    sales=Sale.objects.all()
    total=sum(s.total for s in sales)
    return render(request,'reports.html',{'total':total})
