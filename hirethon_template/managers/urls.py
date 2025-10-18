from django.urls import path
from hirethon_template.managers.views import create_user_view, create_team_view


app_name = "managers"
urlpatterns = [
    path("create-user/", create_user_view, name="create-user"),
    path("create-team/", create_team_view, name="create-team"),
]