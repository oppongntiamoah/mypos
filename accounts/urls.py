
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('users/', views.user_list, name='users'),
    path('users/add/', views.user_add, name='user_add'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
]
