from django.urls import path

from main.views import HomeHandler, DashboardHandler, DashboardAddFiledHandler, DashboardEditFiledHandler, \
    DashboardDeleteFiledHandler, DownloadFeaturesExcelHandler, DashboardDetailFileHandler, ImportDataHandler

app_name = "main"

urlpatterns = [
    path('', HomeHandler.as_view(), name='home'),
    path('dashboard', DashboardHandler.as_view(), name='dashboard'),
    path('dashboard/file/add', DashboardAddFiledHandler.as_view(), name='add-file'),
    path('dashboard/file/edit/<int:id>', DashboardEditFiledHandler.as_view(), name='edit-file'),
    path('dashboard/file/detail/<int:id>', DashboardDetailFileHandler.as_view(), name='detail-file'),
    path('dashboard/file/delete/<int:id>', DashboardDeleteFiledHandler.as_view(), name='delete-file'),
    path('dashboard/file/download', DownloadFeaturesExcelHandler.as_view(), name='download'),
    path('dashboard/file/import', ImportDataHandler.as_view(), name='import')
]