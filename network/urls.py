
from django.urls import path, re_path

from . import views



urlpatterns = [
    path("", views.index, name="index"),
    path("all", views.all, name="all"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("profile/<int:pk>", views.profile, name="profile"),
    path("following", views.following, name="following"),
    path("like", views.like, name="like"),
    path("edit/<int:pk>", views.edit, name="edit"),
    #re_path(r'^posts/(?P<pk>\d+)/update/$', views.post_update, name='post_update'),
    #re_path(r'^$',like_button, name='likes'),
]
