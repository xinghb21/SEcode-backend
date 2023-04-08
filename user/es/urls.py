from django.urls import path, include
from user.es.views import EsViewSet
from rest_framework.routers import DefaultRouter
router = DefaultRouter(trailing_slash=False)
router.register("", EsViewSet, basename="es")

urlpatterns = router.urls