from django.urls import path
from hirethon_template.managers.views import (
    create_user_view, create_team_view, 
    get_teams_list_view, get_users_list_view, create_team_member_view,
    get_teams_management_view, toggle_team_status_view, create_team_member_for_team_view,
    get_users_management_view, toggle_user_status_view
)


app_name = "managers"
urlpatterns = [
    path("create-user/", create_user_view, name="create-user"),
    path("create-team/", create_team_view, name="create-team"),
    path("teams-list/", get_teams_list_view, name="teams-list"),
    path("users-list/", get_users_list_view, name="users-list"),
    path("create-team-member/", create_team_member_view, name="create-team-member"),
    path("teams-management/", get_teams_management_view, name="teams-management"),
    path("toggle-team-status/<int:team_id>/", toggle_team_status_view, name="toggle-team-status"),
    path("add-member-to-team/<int:team_id>/", create_team_member_for_team_view, name="add-member-to-team"),
    path("users-management/", get_users_management_view, name="users-management"),
    path("toggle-user-status/<int:user_id>/", toggle_user_status_view, name="toggle-user-status"),
]