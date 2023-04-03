from django.urls import path, include
from user.ep.views import EpViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("", EpViewSet, basename="es")

urlpatterns = router.urls