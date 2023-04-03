from django.urls import path, include
import user.views as userviews
import department.views as dpviews
from user.views import UserViewSet

from rest_framework.routers import DefaultRouter
#TODO add urls
router = DefaultRouter(trailing_slash=False)
router.register("", UserViewSet, basename="user")
# print(router.urls)

urlpatterns = router.urls + [
    path('es/', include("user.es.urls")),
    path('ep/', include('user.ep.urls')),
    path('<username>', userviews.home),
]
