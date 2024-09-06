from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model  # Import get_user_model
from django.urls import reverse

User = get_user_model()  # Get the custom user model

class CustomUserAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)  # Use CustomUser to find user
        except User.DoesNotExist:
            return None

        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)  # Use CustomUser to find user
        except User.DoesNotExist:
            return None

    def get_success_url(self):
        return reverse('record')
