from django.urls import path
from . import views

app_name = 'test_case_reviewer'

urlpatterns = [
    # Page routes
    path('', views.review_view, name='review'),
    path('case-review-detail/', views.case_review_detail, name='case_review_detail'),

    # API routes
    path('case-review-detail/api/test-case/<int:test_case_id>/', views.get_test_case, name='get_test_case'),
    path('test_case_reviewer/api/copy-test-cases/', views.copy_test_cases, name='copy_test_cases'),
    path('test_case_reviewer/api/export-test-cases-excel/', views.export_test_cases_excel, name='export_test_cases_excel'),
    path('api/delete-test-cases/', views.delete_test_cases, name='delete_test_cases'),
    path('case-review-detail/api/update-test-case/', views.update_test_case, name='update_test_case'),
    path('case-review-detail/api/review/', views.case_review, name='case_review'),
    path('api/test-cases/<str:test_case_ids>/', views.get_test_cases, name='get_test_cases'),
]