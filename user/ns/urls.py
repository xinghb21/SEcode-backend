from django.urls import path, include
from user.ns.views import NsViewSet
from rest_framework.routers import DefaultRouter
router = DefaultRouter(trailing_slash=False)
router.register("", NsViewSet, basename="ns")

urlpatterns = router.urls