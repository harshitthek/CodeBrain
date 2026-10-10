"""
URL configuration for code_brain project.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    # MeterSphere interface test case generation route
    path('iface_case_generator/', include('apps.ai_agents.iface_case_generator.urls')),
    path('java_code_analyzer/', include('apps.ai_agents.java_code_analyzer.urls')),
    path('prd_analyzer/', include('apps.ai_agents.prd_analyzer.urls')),
    path('test_case_generator/', include('apps.ai_agents.test_case_generator.urls')),
    path('test_case_reviewer/', include('apps.ai_agents.test_case_reviewer.urls')),

] 