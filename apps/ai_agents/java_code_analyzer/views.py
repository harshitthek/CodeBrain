from apps.utils.logger_manager import get_logger
from django.conf import settings
from apps.llm import LLMServiceFactory
from apps.ai_agents.java_code_analyzer.java_code_analyzer_agent import JavaCodeAnalyzerAgent
import json
import os
from django.http import JsonResponse
from apps.ai_agents.java_code_analyzer.tools import GitTools
from pathlib import Path
from datetime import datetime
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.http import FileResponse, Http404
from urllib.parse import quote
from apps.llm.utils import get_agent_llm_configs


logger = get_logger(__name__)


def java_code_analyzer(request):
    """Java code analyzer page view"""
    if request.method == 'GET':
        DEFAULT_PROVIDER, PROVIDERS = get_agent_llm_configs("java_code_analyzer")
        
        context = {
            'llm_providers': PROVIDERS,
            'llm_provider': DEFAULT_PROVIDER,
        }
        return render(request, 'java_code_analyzer.html', context)


@require_http_methods(["GET"])
def download_report(request):
    """Download Java code analyzer report"""
    filename = request.GET.get('filename', '')
    if not filename:
        raise Http404("Missing filename")

    # Only allow downloading .md files under outputs directory to prevent path traversal
    if '/' in filename or '\\' in filename:
        raise Http404("Invalid filename")
    if not filename.endswith('.md'):
        raise Http404("Only .md files are supported for download")

    outputs_dir = (Path(settings.BASE_DIR) / 'outputs').resolve()
    file_path = (outputs_dir / filename).resolve()
    if outputs_dir not in file_path.parents:
        raise Http404("Invalid file path")
    if not file_path.exists() or not file_path.is_file():
        raise Http404("File does not exist")

    response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
    response['Content-Type'] = 'text/markdown; charset=utf-8'
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@require_http_methods(["POST"])
def java_code_analyzer_service_api(request):
    """Java code analyzer API endpoint"""
    try:
        data = json.loads(request.body)
        project_id = data.get('project_id')
        base_commit = data.get('base_commit')
        new_commit = data.get('new_commit')
        llm_provider = data.get('llm_provider')
        
        logger.info(f"Java code analysis request: project={project_id}, base={base_commit}, target={new_commit}, LLM provider={llm_provider}")
        
        # Validate parameters
        if not project_id or not base_commit or not new_commit:
            return JsonResponse({
                'success': False,
                'error': 'Project ID, base commit, and target commit are required'
            }, status=400)
        
        base_dir = getattr(settings, 'JAVA_PROJECTS_BASE_DIR', None)
        project_mapping = getattr(settings, 'PROJECT_ID_REPO_MAPPING', {})
        
        if not base_dir:
            return JsonResponse({
                'success': False,
                'error': 'JAVA_PROJECTS_BASE_DIR is not configured'
            }, status=500)
        
        repo_path = os.path.join(base_dir, project_id)
        logger.info(f"Constructed project path: {repo_path}")
        
        if not os.path.exists(repo_path):
            return JsonResponse({
                'success': False,
                'error': f'Project {project_id} does not exist. Path: {repo_path}'
            }, status=400)
        
        logger.info(f"Using project path: {repo_path}")

        analyzer_agent = JavaCodeAnalyzerAgent(
            repo_path=repo_path,
            java_analyzer_service_url=getattr(settings, 'JAVA_ANALYZER_SERVICE_URL'),
            max_iterations=100,
            verbose=True,
            llm_provider=llm_provider,
        )
        
        git_tools = GitTools(repo_path)
        output_dir = Path(settings.BASE_DIR) / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{project_id}_analyzer_{base_commit[:8]}_{new_commit[:8]}_{timestamp}.md"
        output_path = output_dir / output_filename

        original_ref = None
        report_content = ""

        try:
            logger.info("Pulling latest code...")
            git_tools.pull_latest()

            logger.info("Recording current Git status...")
            original_ref = git_tools.get_current_ref()
            logger.info(f"Current ref: {original_ref}")

            logger.info(f"Checking out target commit: {new_commit}")
            git_tools.checkout_version(new_commit)
            logger.info(f"Switched to: {new_commit}")

            result = analyzer_agent.analyze(base_commit, new_commit)

            if not isinstance(result, dict):
                logger.error(f"Analysis return type invalid: {type(result)}, value: {result}")
                return JsonResponse({
                    'success': False,
                    'error': f'Analysis return type invalid: {str(result)}'
                }, status=500)

            if result.get('success'):
                report_content = result.get('output', '')
                if report_content:
                    output_path.write_text(report_content, encoding='utf-8')
                    logger.info(f"Analysis report written: {output_path}")
                return JsonResponse({
                    'success': True,
                    'result': report_content or 'Analysis completed, but no detailed results returned',
                    'report_path': str(output_path),
                    'report_filename': output_filename,
                    'report_download_url': f"/java_code_analyzer/api/download-report/?filename={quote(output_filename)}"
                })

            error_msg = result.get('error', 'Analysis failed')
            logger.error(f"Analysis failed: {error_msg}")
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=500)

        finally:
            if original_ref:
                try:
                    git_tools.checkout_version(original_ref)
                    logger.info(f"Restored to original ref: {original_ref}")
                except Exception as restore_error:
                    logger.error(f"Failed to restore original ref: {restore_error}")

    except json.JSONDecodeError:
        logger.error("JSON parse error", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error during Java code analysis: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Analysis failed: {str(e)}'
        }, status=500)
