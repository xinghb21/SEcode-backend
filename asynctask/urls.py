from django.urls import path, include
from asynctask.views import asynctask
from rest_framework.routers import DefaultRouter

router = DefaultRouter(trailing_slash=False)
router.register("", asynctask, basename="asynctask")

urlpatterns = router.urls+[
    
]