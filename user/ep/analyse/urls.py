from django.urls import path, include
from user.ep.analyse.views import AsViewSet
from rest_framework.routers import DefaultRouter
router = DefaultRouter(trailing_slash=False)
router.register("", AsViewSet, basename="as")

urlpatterns = router.urls