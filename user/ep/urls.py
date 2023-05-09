from django.urls import path, include
from user.ep.views import EpViewSet
import user.ns.views as views
from rest_framework.routers import DefaultRouter
router = DefaultRouter(trailing_slash=False)
router.register("", EpViewSet, basename="ns")

urlpatterns = router.urls +[
    path('as/', include("user.ep.analyse.urls")),
    path('aw/', include("user.ep.aware.urls")),
]