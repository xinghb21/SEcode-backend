from django.urls import path, include
import user.views as userviews
import department.views as dpviews
from user.views import UserViewSet

from rest_framework.routers import DefaultRouter
#TODO add urls
router = DefaultRouter(trailing_slash=False)
router.register("", UserViewSet, basename="user")

urlpatterns = router.urls + [
    path('es/', include("user.es.urls")),
    path('ns/', include("user.ns.urls")),
    path('home/<username>', userviews.home),
    path('username',userviews.name)
]
