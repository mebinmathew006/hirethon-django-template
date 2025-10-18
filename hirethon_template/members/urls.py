from django.urls import path
from hirethon_template.members.views import (
    get_user_dashboard_view
)

app_name = "members"
urlpatterns = [
    path("dashboard/", get_user_dashboard_view, name="user-dashboard"),
]
