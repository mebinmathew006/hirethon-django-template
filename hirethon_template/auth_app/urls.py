from django.urls import path

from hirethon_template.auth_app.views import login_view, TokenRefreshFromCookieView


app_name = "auth_app"
urlpatterns = [
    path("login/", login_view, name="login"),
    path("refresh_token/", TokenRefreshFromCookieView.as_view(), name="refresh_token"),
]