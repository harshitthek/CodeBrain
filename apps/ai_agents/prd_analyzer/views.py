import os
import json
import tempfile
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


def extract_content_from_file(uploaded_file, file_type: str) -> str:
    """Extract plain text / markdown from uploaded document."""
    file_type = file_type.lower()

    if file_type in ['.md', '.txt']:
        raw_bytes = uploaded_file.read()
        try:
            return raw_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return raw_bytes.decode('latin-1', errors='replace')

    elif file_type == '.pdf':
        try:
            import pypdf
            reader = pypdf.PdfReader(uploaded_file)
            pages = [page.extract_text() or "" for page in reader.pages]
            extracted = "\n\n".join(pages).strip()
            if not extracted:
                raise ValueError("PDF contains no extractable text or is image-based.")
            return extracted
        except Exception as e:
            logger.error(f"Failed to extract PDF text: {str(e)}", exc_info=True)
            raise ValueError(f"Could not extract text from PDF: {str(e)}")

    elif file_type == '.docx':
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, 'input.docx')
            output_path = os.path.join(temp_dir, 'output.md')
            with open(input_path, 'wb+') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
            word_to_markdown(input_path, output_path)
            if not os.path.exists(output_path):
                raise ValueError("DOCX conversion failed: output Markdown file was not generated.")
            with open(output_path, 'r', encoding='utf-8') as f:
                return f.read()

    else:
        raise ValueError(f"Unsupported file format '{file_type}'. Supported: .docx, .md, .txt, .pdf")


def prd_analyzer(request):
    """Extract test points and test scenarios from PRD document or raw text"""
    if request.method == 'GET':
        return render(request, 'prd_analyzer.html')
    elif request.method == 'POST':
        prd_content = ""

        # Check for raw text submission (direct paste)
        raw_text = request.POST.get('raw_text', '').strip()
        if not raw_text and request.content_type == 'application/json':
            try:
                body_data = json.loads(request.body)
                if isinstance(body_data, dict):
                    raw_val = body_data.get('raw_text')
                    if isinstance(raw_val, str):
                        raw_text = raw_val.strip()
            except Exception:
                pass

        if raw_text:
            prd_content = raw_text
            logger.info(f"Received raw text PRD input of {len(prd_content)} characters")
        elif 'single_file' in request.FILES:
            uploaded_file = request.FILES['single_file']
            file_type = os.path.splitext(uploaded_file.name)[1].lower()
            logger.info(f"Processing uploaded file: {uploaded_file.name} ({file_type})")
            try:
                prd_content = extract_content_from_file(uploaded_file, file_type)
            except Exception as e:
                logger.error(f"Error parsing uploaded file: {str(e)}")
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
        else:
            return JsonResponse({'success': False, 'error': 'No file or text content received'}, status=400)

        if not prd_content.strip():
            return JsonResponse({'success': False, 'error': 'PRD content is empty'}, status=400)

        try:
            analyser = PrdAnalyserAgent(llm_service=llm_service)
            result = analyser.analyse(prd_content)
            return JsonResponse({
                'success': True,
                'result': result
            })
        except Exception as e:
            logger.error(f"PRD Analysis failed: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': f"Analysis error: {str(e)}"}, status=500)

    return JsonResponse({
        'success': False,
        'error': 'Unsupported request method'
    }, status=405)
