from django.urls import path, include
from asset.views import asset
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.routers import DefaultRouter

router = DefaultRouter(trailing_slash=False)
router.register("", asset, basename="asset")

urlpatterns = router.urls