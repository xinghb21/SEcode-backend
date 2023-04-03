from django.urls import path, include
import user.views as userviews
import department.views as dpviews
from user.views import UserViewSet

from rest_framework.routers import DefaultRouter
#TODO add urls
router = DefaultRouter(trailing_slash=False)
router.register("user", UserViewSet, basename="user")
# print(router.urls)

urlpatterns = [
    path('entity/create',dpviews.createEt),
    path('entity/delete',dpviews.deleteEt),
    path('entity/assgin',dpviews.assginES),
    path('entity/deleteadmin',dpviews.deleteES),
    path('entity/superget',dpviews.getEt),
    path('user/es/', include("user.es.urls")),
    path('user/ep/', include('user.ep.urls')),
    path('user/<username>', userviews.home),
] + router.urls
