
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import UserProfile


def login_view(request):
    if request.user.is_authenticated:
        return redirect('pos:index')
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html', {})


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def profile(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        profile.phone = request.POST.get('phone', profile.phone)
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
        profile.save()
        messages.success(request, 'Profile updated.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'profile': profile})


@login_required
def user_list(request):
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('pos:index')
    users = User.objects.select_related('profile').all().order_by('username')
    return render(request, 'accounts/users.html', {'users': users})


@login_required
def user_add(request):
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('pos:index')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        role = request.POST.get('role', 'cashier')
        if username and password:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
            else:
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=request.POST.get('first_name', ''),
                    last_name=request.POST.get('last_name', ''),
                    email=request.POST.get('email', ''),
                    is_staff='is_staff' in request.POST,
                )
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.role = role
                profile.phone = request.POST.get('phone', '')
                profile.save()
                messages.success(request, f'User "{username}" created.')
                return redirect('accounts:users')
        else:
            messages.error(request, 'Username and password are required.')
    return render(request, 'accounts/user_form.html', {
        'roles': UserProfile.ROLES,
        'action': 'Add',
    })


@login_required
def user_edit(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('pos:index')
    user = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.is_staff = 'is_staff' in request.POST
        new_password = request.POST.get('password', '')
        if new_password:
            user.set_password(new_password)
        user.save()
        profile.role = request.POST.get('role', profile.role)
        profile.phone = request.POST.get('phone', '')
        profile.save()
        messages.success(request, 'User updated.')
        return redirect('accounts:users')
    return render(request, 'accounts/user_form.html', {
        'edit_user': user,
        'profile': profile,
        'roles': UserProfile.ROLES,
        'action': 'Edit',
    })
