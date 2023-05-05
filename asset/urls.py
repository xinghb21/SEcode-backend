from django.urls import path, include
from asset.views import asset, assetclass
import asset.views as assetView
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.routers import DefaultRouter

router = DefaultRouter(trailing_slash=False)
router.register("", asset, basename="asset")

urlpatterns = router.urls + [
    path("assetclass", assetclass.as_view()),
    path("getdetail",assetView.getdetail),
    path("fulldetail/<id>",assetView.fulldetail)
]