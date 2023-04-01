from django.urls import path, include
from es import views


urlpatterns = [
    path("checkuser", views.check_user)
]
