from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('record/', views.record, name='record'),
]
