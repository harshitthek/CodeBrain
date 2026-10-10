from django.urls import path
from . import views
from .views_sse import stream_logs

urlpatterns = [
    # Page routes
    path('', views.index, name='index'),
    path('knowledge/', views.knowledge_view, name='knowledge'),
    
    # Knowledge base file upload page
    path('upload/', views.upload_single_file, name='upload_single_file'),

    # API routes
    path('api/add-knowledge/', views.add_knowledge, name='add_knowledge'),
    path('api/knowledge-list/', views.knowledge_list, name='knowledge_list'),
    path('api/search-knowledge/', views.search_knowledge, name='search_knowledge'),   
    path('api/update-status/', views.update_test_case_status, name='update_test_case_status'),
    path('api/stream-logs/', stream_logs, name='stream_logs'),

    # Autonomous Multi-Agent Pipeline routes
    path('pipeline/', views.pipeline_view, name='pipeline'),
    path('pipeline/run/', views.pipeline_run_api, name='pipeline_run'),
    path('pipeline/export/', views.pipeline_export_tms, name='pipeline_export'),
]
