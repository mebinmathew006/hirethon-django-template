from django.urls import path
from hirethon_template.members.views import (
    get_user_dashboard_view,
    get_user_schedule_view,
    get_day_slots_view,
    request_leave_view,
    request_swap_view,
    get_swap_requests_view,
    respond_to_swap_request_view,
    get_user_teams_oncall_view,
    get_all_teams_oncall_view
)

app_name = "members"
urlpatterns = [
    path("dashboard/", get_user_dashboard_view, name="user-dashboard"),
    path("schedule/", get_user_schedule_view, name="user-schedule"),
    path("day-slots/<int:year>/<int:month>/<int:day>/", get_day_slots_view, name="day-slots"),
    path("request-leave/", request_leave_view, name="request-leave"),
    path("request-swap/", request_swap_view, name="request-swap"),
    path("swap-requests/", get_swap_requests_view, name="swap-requests"),
    path("swap-requests/<int:swap_request_id>/respond/", respond_to_swap_request_view, name="respond-swap-request"),
    path("teams-oncall/", get_user_teams_oncall_view, name="user-teams-oncall"),
    path("all-teams-oncall/", get_all_teams_oncall_view, name="all-teams-oncall"),
]
