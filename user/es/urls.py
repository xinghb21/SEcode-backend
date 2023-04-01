from django.urls import path, include
from . import views


urlpatterns = [
    path("checkuser", views.check_user)
]
