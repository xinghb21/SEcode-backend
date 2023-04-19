from django.urls import path, include
from feishu.views import feishu
from rest_framework.routers import DefaultRouter

router = DefaultRouter(trailing_slash=False)
router.register("", feishu, basename="feishu")

urlpatterns = router.urls+[
    
]