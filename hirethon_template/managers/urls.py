from django.urls import path
from hirethon_template.managers.views import (
    create_user_view, create_team_view, 
    get_teams_list_view, get_users_list_view, create_team_member_view
)


app_name = "managers"
urlpatterns = [
    path("create-user/", create_user_view, name="create-user"),
    path("create-team/", create_team_view, name="create-team"),
    path("teams-list/", get_teams_list_view, name="teams-list"),
    path("users-list/", get_users_list_view, name="users-list"),
    path("create-team-member/", create_team_member_view, name="create-team-member"),
]