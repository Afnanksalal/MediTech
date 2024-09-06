from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UserLoginForm, UserRegistrationForm
from django.contrib.auth import get_user_model  # Import get_user_model

User = get_user_model()


def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('record')
            else:
                form.add_error(None, 'Invalid username or password.')
    else:
        form = UserLoginForm()

    return render(request, 'app/login.html', {'form': form})

def signup(request):
    if request.method == 'POST':
        print("Signup view - POST request received")  # Debug 1
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            print("Signup form is valid")  # Debug 2
            user = form.save(commit=False)

            # Check Password Confirmation
            password1 = form.cleaned_data.get('password1')
            password2 = form.cleaned_data.get('password2')

            if password1 != password2:
                print("Passwords do not match") # Debug 8
                form.add_error('password2', 'Passwords do not match.')
                return render(request, 'app/signup.html', {'form': form})

            print("Setting password using set_password") # Debug 9
            user.set_password(password2)
            user.save()
            print("User saved successfully")  # Debug 3

            print("Authenticating with username:", user.username, "and password:", password2) # Debug 10
            user = authenticate(request, username=user.username, password=password2)

            if user is not None:
                print("User authenticated successfully")  # Debug 4
                login(request, user)
                return redirect('record')
            else:
                print("User authentication failed")  # Debug 5
                form.add_error(None, 'Signup failed. Please try again.')
        else:
            print("Signup form is invalid:", form.errors)  # Debug 6
    else:
        print("Signup view - GET request received")  # Debug 7
        form = UserRegistrationForm()

    return render(request, 'app/signup.html', {'form': form})
def logout_view(request):
    logout(request)
    return redirect('index')


def index(request):
    return render(request, 'app/index.html')


def about(request):
    return render(request, 'app/about.html')


@login_required
def record(request):
    return render(request, 'app/record.html')
