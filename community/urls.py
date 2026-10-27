from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.forum, name="forum"),
    path("projects/", views.projects, name="projects"),
    path("projects/new/", views.project_create, name="project_create"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path("projects/<int:pk>/edit/", views.project_edit, name="project_edit"),
    path("projects/<int:pk>/vote/", views.project_vote, name="project_vote"),
    path("discussions/new/", views.topic_create, name="topic_create"),
    path("discussions/<int:pk>/", views.topic_detail, name="topic_detail"),
    path("discussions/<int:pk>/edit/", views.topic_edit, name="topic_edit"),
    path("discussions/<int:pk>/reply/", views.reply_create, name="reply_create"),
    path("discussions/<int:pk>/like/", views.topic_like, name="topic_like"),
    path("signup/", views.signup, name="signup"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
