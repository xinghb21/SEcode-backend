from django.urls import path, include
from user.ep.views import EpViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter(trailing_slash=False)
router.register("", EpViewSet, basename="es")

urlpatterns = router.urls