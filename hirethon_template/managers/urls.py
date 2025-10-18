from django.urls import path
from hirethon_template.managers.views import (
    create_user_view, create_team_view, 
    get_teams_list_view, get_users_list_view, create_team_member_view,
    get_teams_management_view, toggle_team_status_view, create_team_member_for_team_view,
    get_users_management_view, toggle_user_status_view,
    get_empty_slots_notifications_view, mark_notification_read_view,
    get_leave_requests_view, approve_reject_leave_request_view,
    get_available_users_for_slot_view, assign_user_to_slot_view,
    get_team_members_with_schedule_view, get_dashboard_stats_view
)
from hirethon_template.managers.slot_views import (
    create_slots_manually_view, revalidate_slots_view
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
    path("create-slots/", create_slots_manually_view, name="create-slots"),
    path("revalidate-slots/", revalidate_slots_view, name="revalidate-slots"),
    path("notifications/", get_empty_slots_notifications_view, name="get-notifications"),
    path("mark-notification-read/", mark_notification_read_view, name="mark-notification-read"),
    path("leave-requests/", get_leave_requests_view, name="get-leave-requests"),
    path("leave-requests/<int:leave_request_id>/approve-reject/", approve_reject_leave_request_view, name="approve-reject-leave-request"),
    path("slots/<int:slot_id>/available-users/", get_available_users_for_slot_view, name="get-available-users-for-slot"),
    path("slots/<int:slot_id>/assign-user/", assign_user_to_slot_view, name="assign-user-to-slot"),
    path("teams/<int:team_id>/members-schedule/", get_team_members_with_schedule_view, name="get-team-members-with-schedule"),
    path("dashboard-stats/", get_dashboard_stats_view, name="get-dashboard-stats"),
]