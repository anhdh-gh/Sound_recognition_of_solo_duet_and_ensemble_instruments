from django.shortcuts import render
from django.views import View


class HomeHandler(View):
    def get(self, request):
        return render(request, "home.html", {})

class DashboardHandler(View):
    def get(self, request):
        return render(request, "dashboard.html", {})