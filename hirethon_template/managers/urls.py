from django.urls import path
from hirethon_template.managers.views import create_user_view


app_name = "managers"
urlpatterns = [
    path("create-user/", create_user_view, name="create-user"),
]