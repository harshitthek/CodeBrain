from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

from .models import TestCase, KnowledgeBase
from ..knowledge.service import get_knowledgeService_instance

from django.conf import settings
from apps.llm import LLMServiceFactory
from apps.utils.logger_manager import get_logger
from django.views.decorators.csrf import csrf_exempt
import os
from datetime import datetime
from apps.knowledge.milvus_helper import process_singel_file

import hashlib


logger = get_logger(__name__)

llm_config = getattr(settings, 'LLM_PROVIDERS', {})
DEFAULT_PROVIDER = llm_config.get('default_provider', 'deepseek')
PROVIDERS = {k: v for k, v in llm_config.items() if k != 'default_provider'}
DEFAULT_LLM_CONFIG = PROVIDERS.get(DEFAULT_PROVIDER, {})

llm_service = LLMServiceFactory.create(
    provider=DEFAULT_PROVIDER,
)

knowledge_service = get_knowledgeService_instance()


def index(request):
    """Home page view"""
    total_test_cases = TestCase.objects.count()
    pending_count = TestCase.objects.filter(status='pending').count()
    approved_count = TestCase.objects.filter(status='approved').count()
    rejected_count = TestCase.objects.filter(status='rejected').count()
    
    recent_test_cases = TestCase.objects.order_by('-created_at')[:10]
    
    context = {
        'total_test_cases': total_test_cases,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'recent_test_cases': recent_test_cases,
    }
    
    return render(request, 'index.html', context)


def format_test_cases_to_html(test_cases):
    """Format test cases into HTML"""
    html = ""
    for i, test_case in enumerate(test_cases):
        html += "<div class='test-case mb-4'>"
        html += f"<h4>Test Case #{i+1}: {test_case.get('description', 'No description')}</h4>"
        
        # Test steps
        html += "<div class='test-steps mb-3'>"
        html += "<h5>Test Steps:</h5>"
        html += "<ol>"
        for step in test_case.get('test_steps', []):
            html += f"<li>{step}</li>"
        html += "</ol>"
        html += "</div>"
        
        # Expected results
        html += "<div class='expected-results'>"
        html += "<h5>Expected Results:</h5>"
        html += "<ol>"
        for result in test_case.get('expected_results', []):
            html += f"<li>{result}</li>"
        html += "</ol>"
        html += "</div>"
        
        html += "</div>"
    
    return html


def knowledge_view(request):
    """Knowledge base management page"""
    return render(request, 'knowledge.html')


@require_http_methods(["POST"])
def add_knowledge(request):
    """Add knowledge base entry"""
    try:
        data = json.loads(request.body)
        title = data.get('title')
        content = data.get('content')
        
        if not title or not content:
            return JsonResponse({
                'success': False,
                'message': 'Title and content cannot be empty'
            })
        
        knowledge_id = knowledge_service.add_knowledge(title, content)
        
        return JsonResponse({
            'success': True,
            'message': 'Knowledge entry added successfully',
            'knowledge_id': knowledge_id
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


def knowledge_list(request):
    """Get list of knowledge base entries"""
    try:
        knowledge_items = KnowledgeBase.objects.all().order_by('-created_at')
        
        items = []
        for item in knowledge_items:
            items.append({
                'id': item.id,
                'title': item.title,
                'content': item.content,
                'created_at': item.created_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'knowledge_items': items
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@require_http_methods(["POST"])
def search_knowledge(request):
    """Search knowledge base"""
    try:
        data = json.loads(request.body)
        query = data.get('query')
        
        if not query:
            return JsonResponse({
                'success': False,
                'message': 'Search query cannot be empty'
            })
        
        query_embedding = knowledge_service.embedder.get_embeddings(query)[0]
        logger.info(f"Query: '{query}', embedding dim: {len(query_embedding)}, first 5 dims: {query_embedding[:5]}")
        results = knowledge_service.search_knowledge(query)
        
        return JsonResponse({
            'success': True,
            'results': results
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@csrf_exempt
def upload_single_file(request):
    """Handle file uploads for knowledge base"""
    if request.method == 'GET':
        return render(request, 'upload.html')
    elif request.method == 'POST':
        if 'single_file' in request.FILES:
            uploaded_file = request.FILES['single_file']
            
            upload_dir = settings.MEDIA_ROOT
            file_path = os.path.join(upload_dir, uploaded_file.name)
            
            is_overwrite = False
            if os.path.exists(file_path):
                logger.info(f"Duplicate file detected, overwriting: {file_path}")
                is_overwrite = True
                
                try:
                    knowledge_service.vector_store.delete_by_source(file_path)
                    logger.info("Successfully deleted old vector records")
                except Exception as e:
                    logger.error(f"Failed to delete old vector records: {str(e)}")
                    return JsonResponse({
                        'success': False,
                        'error': f'Failed to delete old data when overwriting file: {str(e)}'
                    })
                
                try:
                    os.remove(file_path)
                    logger.info("Successfully deleted old file")
                except Exception as e:
                    logger.error(f"Failed to delete old file: {str(e)}")
                    return JsonResponse({
                        'success': False,
                        'error': f'Failed to delete old file: {str(e)}'
                    })
                
            try:
                logger.info(f"Uploaded file: {uploaded_file}")
                if not uploaded_file:
                    return JsonResponse({'success': False, 'error': 'No file received'})
                
                file_categories = {
                    "CSV": [".csv"],
                    "E-mail": [".eml", ".msg", ".p7s"],
                    "EPUB": [".epub"],
                    "Excel": [".xls", ".xlsx"],
                    "HTML": [".html"],
                    "Image": [".bmp", ".heic", ".jpeg", ".png", ".tiff"],
                    "Markdown": [".md"],
                    "Org Mode": [".org"],
                    "Open Office": [".odt"],
                    "PDF": [".pdf"],
                    "Plain text": [".txt"],
                    "PowerPoint": [".ppt", ".pptx"],
                    "reStructured Text": [".rst"],
                    "Rich Text": [".rtf"],
                    "TSV": [".tsv"],
                    "Word": [".doc", ".docx"],
                    "XML": [".xml"]
                }
                file_type = os.path.splitext(uploaded_file.name)[1]
                logger.info(f"Uploaded file type: {file_type}")
                logger.info(f"Uploaded file name: {uploaded_file.name}")
                
                if not file_type:
                    logger.error("File has no extension")
                    return JsonResponse({'success': False, 'error': 'File must include an extension'})
                
                supported_extensions = [ext.lower() for exts in file_categories.values() for ext in exts]

                if file_type not in supported_extensions:
                    return JsonResponse({'success': False, 'error': 'Unsupported file type'})
                
                os.makedirs(upload_dir, exist_ok=True)
                with open(file_path, 'wb+') as f:
                    for chunk in uploaded_file.chunks():
                        f.write(chunk)
                logger.info(f"File saved successfully, path: {file_path}")

                chunks = process_singel_file(file_path)
                if not chunks:
                    return JsonResponse({'success': False, 'error': 'No valid content in file'})

                if isinstance(chunks, list):
                    text_contents = []
                    for i, chunk in enumerate(chunks):
                        if hasattr(chunk, 'text'):
                            text_contents.append(str(chunk.text))
                        else:
                            text_contents.append(str(chunk))
                
                    logger.info(f"Extracted {len(text_contents)} text contents")
                else:
                    if hasattr(chunks, 'text'):
                        text_contents = [str(chunks.text)]
                    else:
                        text_contents = [str(chunks)]
                    logger.info(f"Extracted single text content: {text_contents[0][:100]}...")

                logger.info("Starting embedding generation")
                start_time = datetime.now()

                try:
                    all_embeddings = knowledge_service.embedder.get_embeddings(texts=text_contents, show_progress_bar=False)
                    logger.info(f"Successfully generated {len(all_embeddings)} embeddings")
                    
                    embeddings_list = []
                    for emb in all_embeddings:
                        if hasattr(emb, 'tolist'):
                            emb = emb.tolist()
                        embeddings_list.append(emb)
                    
                    data_to_insert = []
                    for i in range(len(text_contents)):
                        item = {
                            "embedding": embeddings_list[i],
                            "content": text_contents[i],
                            "metadata": '{}',
                            "source": file_path,
                            "doc_type": file_type,
                            "chunk_id": f"{hashlib.md5(os.path.basename(file_path).encode()).hexdigest()[:10]}_{i:04d}",
                            "upload_time": datetime.now().isoformat()
                        }
                        data_to_insert.append(item)
                    
                    logger.info(f"Inserting {len(data_to_insert)} records into Milvus")
                    knowledge_service.vector_store.add_data(data_to_insert)
                    logger.info("Data insertion complete")
                    
                    total_time = (datetime.now() - start_time).total_seconds()
                    logger.info(f"Embedding generation and insertion completed in {total_time:.2f} seconds")
                    
                    return JsonResponse({
                        'success': True, 
                        'count': len(text_contents),
                        'message': f'Successfully {"overwrote" if is_overwrite else "imported"} file to knowledge base'
                    })
                    
                except Exception as e:
                    logger.error(f"Error during embedding generation or insertion: {str(e)}", exc_info=True)
                    return JsonResponse({
                        'success': False, 
                        'error': str(e)
                    })
                
            except Exception as e:
                logger.error(f"Error processing uploaded file: {str(e)}", exc_info=True)
                return JsonResponse({
                    'success': False, 
                    'error': str(e)
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
