from django.urls import path, include
import user.views as views

#TODO add urls

urlpatterns = [
    #path('startup', views.startup),
    path('user/createuser',views.create_user),
    path('user/deleteuser',views.delete_user),
    path('user/login',views.login),
    path('user/logout',views.logout)
]
