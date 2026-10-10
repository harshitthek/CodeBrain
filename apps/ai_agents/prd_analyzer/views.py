import os
from django.http import JsonResponse
from apps.utils.logger_manager import get_logger
from apps.ai_agents.prd_analyzer.analyser import PrdAnalyserAgent
from django.conf import settings
from apps.llm import LLMServiceFactory
from django.shortcuts import render
from apps.utils.file_transfer import word_to_markdown
from apps.llm.utils import get_agent_llm_configs


llm_config = getattr(settings, 'LLM_PROVIDERS', {})
DEFAULT_PROVIDER, PROVIDERS = get_agent_llm_configs("prd_analyzer")
DEFAULT_LLM_CONFIG = PROVIDERS.get(DEFAULT_PROVIDER, {})

llm_service = LLMServiceFactory.create(
    provider=DEFAULT_PROVIDER,
)

logger = get_logger(__name__)


def prd_analyzer(request):
    """Extract test points and test scenarios from PRD document"""
    if request.method == 'GET':
        return render(request, 'prd_analyzer.html')
    elif request.method == 'POST':
        if 'single_file' in request.FILES:
            uploaded_file = request.FILES['single_file']
            file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)
            
            if os.path.exists(file_path):
                return JsonResponse({
                    'success': False,
                    'error': 'File already exists'
                })
            logger.info(f"Uploaded file: {uploaded_file}")
            if not uploaded_file:
                return JsonResponse({'success': False, 'error': 'No file received'})
            file_type = os.path.splitext(uploaded_file.name)[1]
            if file_type != '.docx':
                return JsonResponse({'success': False, 'error': 'Unsupported file type'})
            logger.info(f"Uploaded file type: {file_type}")
            logger.info(f"Uploaded file name: {uploaded_file.name}")
            
            # Save temporary file
            save_dir = 'prd/'
            os.makedirs(save_dir, exist_ok=True)
            file_path = os.path.join(save_dir, f"{uploaded_file.name}")
            with open(file_path, 'wb+') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
            logger.info(f"Temporary file saved successfully, path: {file_path}")
            
            # Convert file
            word_to_markdown(file_path, file_path.replace('.docx', '.md'))
            with open(file_path.replace('.docx', '.md'), 'r', encoding='utf-8') as f:
                prd_content = f.read()
            logger.info(f"PRD content: {prd_content}")
            
            analyser = PrdAnalyserAgent(llm_service=llm_service)
            result = analyser.analyse(prd_content)
            return JsonResponse({
                'success': True,
                'result': result
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No file received'
            })
        return JsonResponse({
            'success': False,
            'error': 'Unsupported request method'
        })