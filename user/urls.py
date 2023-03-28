﻿from django.urls import path, include
import user.views as userviews
import department.views as dpviews
#TODO add urls

urlpatterns = [
    path('user/createuser',userviews.create_user),
    path('user/deleteuser',userviews.delete_user),
    path('user/login',userviews.login),
    path('user/logout',userviews.logout),
    path('user/<username>',userviews.home),
    path('entity/create',dpviews.createEt),
    path('entity/delete',dpviews.deleteEt)
]
