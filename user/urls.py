from django.urls import path, include
import user.views as views

#TODO add urls

urlpatterns = [
    path('startup', views.startup),
]
