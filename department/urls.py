from django.urls import path, include
import user.views as userviews
import department.views as dpviews
from user.views import UserViewSet

from rest_framework.routers import DefaultRouter

urlpatterns = [
    path('create',dpviews.createEt),
    path('delete',dpviews.deleteEt),
    path('assgin',dpviews.assginES),
    path('deleteadmin',dpviews.deleteES),
    path('superget',dpviews.getEt),
    path('deleteall',dpviews.deleteAllEt),
    path('deletealladmins',dpviews.deleteAllES),
]