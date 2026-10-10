from django.urls import path
from . import views

app_name = 'java_code_analyzer'

urlpatterns = [
    # Page routes
    path('', views.java_code_analyzer, name='java_code_analyzer'),
    path('java_code_analyzer/', views.java_code_analyzer, name='java_code_analyzer'),

    # API routes
    path('api/java-code-analyzer-service/', views.java_code_analyzer_service_api, name='java_code_analyzer_service_api'),
    path('api/download-report/', views.download_report, name='download_report'),
]