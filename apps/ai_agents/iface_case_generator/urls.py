from django.urls import path
from . import views

app_name = 'iface_case_generator'

urlpatterns = [
    # Page routes
    path('', views.iface_case_generator, name='iface_case_generator'),

    # API routes
    path('download_file/', views.download_file, name='download_file'),
    path('api/testcase-rule-template/', views.get_testcase_rule_template, name='get_testcase_rule_template'),
    path('api/get-generation-progress/', views.get_generation_progress_api, name='get_generation_progress'),
    path('api/execute/', views.execute_test_cases, name='execute_test_cases'),
    path('api/export-pytest/', views.export_pytest_view, name='export_pytest'),
    path('api/export-postman/', views.export_postman_view, name='export_postman'),
]
