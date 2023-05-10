from django.urls import path, include
from user.ep.aware.views import AwViewSet
from rest_framework.routers import DefaultRouter
router = DefaultRouter(trailing_slash=False)
router.register("", AwViewSet, basename="aw")

urlpatterns = router.urls