from django.shortcuts import render, redirect
from .admin import UserCreateForm
from django.contrib.auth import logout as log_out, login as log_in, authenticate
from django.contrib.auth.forms import AuthenticationForm

# Create your views here.


def index(request):
    return render(request, 'index.html')


def register(request):
    form = UserCreateForm()
    if request.method == 'POST':
        form = UserCreateForm(data=request.POST)
        if form.is_valid():
            user = form.save()
            if user is not None:
                log_in(request, user)
                return redirect('/')

    return render(request, 'register.html', {'formulario': form})


def login(request):
    form = AuthenticationForm()
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None:
                log_in(request, user)
                return redirect('/')

    return render(request, 'login.html', {'formulario': form})


def logout(request):
    log_out(request)
    return redirect('/')

