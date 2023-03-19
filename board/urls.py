from django.urls import path, include
import board.views as views

urlpatterns = [
    path('startup', views.startup),
    path('boards', views.boards),
    # TODO Start: [Student] add routing paths for `boards/<index>` and `user/<userName>`
    path('boards/<index>',views.boards_index),
    path('user/<userName>',views.user_index)
    # TODO End: [Student] add routing paths for `boards/<index>` and `user/<userName>`
]
