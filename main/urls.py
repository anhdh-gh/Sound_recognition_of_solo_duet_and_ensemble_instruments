from django.urls import path

from main.views import HomeHandler, DashboardHandler

app_name = "main"

urlpatterns = [
    path('', HomeHandler.as_view(), name='home'),
    path('dashboard', DashboardHandler.as_view(), name='dashboard'),
]