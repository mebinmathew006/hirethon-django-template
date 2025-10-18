from django.urls import path

from hirethon_template.auth_app.views import login_view, TokenRefreshFromCookieView, logout_view


app_name = "auth_app"
urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("refresh_token/", TokenRefreshFromCookieView.as_view(), name="refresh_token"),
]