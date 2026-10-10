from apps.core.models import TestCase
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from apps.utils.logger_manager import get_logger
import json
from django.shortcuts import render
from apps.ai_agents.test_case_reviewer.reviewer import TestCaseReviewerAgent
from django.http import JsonResponse
import xlwt
from django.views.decorators.http import require_http_methods
from datetime import datetime
from django.http import HttpResponse
from django.conf import settings
from apps.llm import LLMServiceFactory
from apps.knowledge.service import get_knowledgeService_instance
from apps.llm.utils import get_agent_llm_configs


logger = get_logger(__name__)

DEFAULT_PROVIDER, PROVIDERS = get_agent_llm_configs("test_case_reviewer")
DEFAULT_LLM_CONFIG = PROVIDERS.get(DEFAULT_PROVIDER, {})

llm_service = LLMServiceFactory.create(
    provider=DEFAULT_PROVIDER,
)

knowledge_service = get_knowledgeService_instance()


def review_view(request):
    """View function for test case review page"""
    pending_cases = TestCase.objects.filter(status='pending').order_by('-created_at')
    approved_cases = TestCase.objects.filter(status='approved').order_by('-created_at')
    rejected_cases = TestCase.objects.filter(status='rejected').order_by('-created_at')
    
    page_size = 15
    
    pending_paginator = Paginator(pending_cases, page_size)
    pending_page = request.GET.get('pending_page', 1)
    try:
        pending_test_cases = pending_paginator.page(pending_page)
    except PageNotAnInteger:
        pending_test_cases = pending_paginator.page(1)
    except EmptyPage:
        pending_test_cases = pending_paginator.page(pending_paginator.num_pages)
    
    approved_paginator = Paginator(approved_cases, page_size)
    approved_page = request.GET.get('approved_page', 1)
    try:
        approved_test_cases = approved_paginator.page(approved_page)
    except PageNotAnInteger:
        approved_test_cases = approved_paginator.page(1)
    except EmptyPage:
        approved_test_cases = approved_paginator.page(approved_paginator.num_pages)
    
    rejected_paginator = Paginator(rejected_cases, page_size)
    rejected_page = request.GET.get('rejected_page', 1)
    try:
        rejected_test_cases = rejected_paginator.page(rejected_page)
    except PageNotAnInteger:
        rejected_test_cases = rejected_paginator.page(1)
    except EmptyPage:
        rejected_test_cases = rejected_paginator.page(rejected_paginator.num_pages)
    
    context = {
        'pending_test_cases': pending_test_cases,
        'approved_test_cases': approved_test_cases,
        'rejected_test_cases': rejected_test_cases,
    }
    
    return render(request, 'review.html', context)


@require_http_methods(["POST"])
def case_review(request):
    """Test case review API endpoint"""
    try:
        data = json.loads(request.body)
        test_case_id = data.get('test_case_id')
        
        logger.info(f"Received review request, test case ID: {test_case_id}")
        
        if not test_case_id:
            logger.error("Test case ID is empty")
            return JsonResponse({
                'success': False,
                'message': 'Test case ID cannot be empty'
            }, status=400)
            
        try:
            test_case = TestCase.objects.get(id=test_case_id)
            logger.info(f"Found test case: ID={test_case.id}")
        except TestCase.DoesNotExist:
            logger.error(f"Cannot find test case with ID {test_case_id}")
            return JsonResponse({
                'success': False,
                'message': f'Cannot find test case with ID {test_case_id}'
            }, status=404)
        
        logger.info("Calling review Agent...")
        test_case_reviewer = TestCaseReviewerAgent(llm_service, knowledge_service)
        review_result = test_case_reviewer.review(test_case)
        logger.info(f"Review completed, result: {review_result}")
        
        review_content = review_result.content if hasattr(review_result, 'content') else str(review_result)
        
        return JsonResponse({
            'success': True,
            'review_result': review_content
        })
        
    except json.JSONDecodeError:
        logger.error("JSON parse error", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error during review: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Review failed: {str(e)}'
        }, status=500)


def case_review_detail(request):
    return render(request, 'case_review_detail.html')


@require_http_methods(["GET"])
def get_test_case(request, test_case_id):
    """Get single test case from database"""
    try:
        test_case = TestCase.objects.get(id=test_case_id)
        return JsonResponse({
            'id': test_case.id,
            'description': test_case.description,
            'test_steps': test_case.test_steps,
            'expected_results': test_case.expected_results,
            'status': test_case.status
        })
    except TestCase.DoesNotExist:
        return JsonResponse({'error': 'Test case does not exist'}, status=404)


def get_test_cases(request, test_case_ids: str):
    """Get multiple test cases from database"""
    try:
        ids = test_case_ids.split(',')
        test_cases = TestCase.objects.filter(id__in=ids).values(
            'id', 'title', 'description', 'test_steps', 
            'expected_results', 'status', 'requirements', 'llm_provider'
        )
        return JsonResponse({
            'success': True,
            'test_cases': list(test_cases)
        })
    except TestCase.DoesNotExist:
        return JsonResponse({'error': 'Test cases do not exist'}, status=404)


@require_http_methods(["POST"])
def update_test_case(request):
    data = json.loads(request.body)
    logger.info(f"Updating test case: {data}")
    try:
        test_case = TestCase.objects.get(id=data['test_case_id'])
        test_case.status = data['status']
        test_case.description = data['description']
        test_case.test_steps = data['test_steps']
        test_case.expected_results = data['expected_results']
        test_case.save()
        return JsonResponse({'success': True})
    except TestCase.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Test case does not exist'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}) 


def copy_test_cases(request):
    """Return selected test cases collection"""
    try:
        ids = request.GET.get('ids')
        response = get_test_cases(request, ids)
        response_data = json.loads(response.content)
        if response_data.get('success'):
            test_cases = response_data.get('test_cases')
            return JsonResponse({
                'success': True,
                'test_cases': test_cases
            })
        else:
            return JsonResponse({
                'success': False,
                'message': response_data.get('message')
            })
    except TestCase.DoesNotExist:
        return JsonResponse({'error': 'Test cases do not exist'}, status=404)


def export_test_cases_excel(request):
    """Export test cases to Excel file"""
    try:
        ids = request.GET.get('ids')
        if not ids:
            return JsonResponse({'success': False, 'message': 'No test case IDs provided'})
            
        response = get_test_cases(request, ids)
        response_data = json.loads(response.content)
        
        if not response_data.get('success'):
            return JsonResponse({'success': False, 'message': 'Failed to retrieve test case data'})
            
        test_cases = response_data.get('test_cases')
        
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Test Cases')
        
        header_style = xlwt.XFStyle()
        header_font = xlwt.Font()
        header_font.bold = True
        header_style.font = header_font
        
        headers = ['No.', 'Description', 'Test Steps', 'Expected Results', 'Status']
        for col, header in enumerate(headers):
            ws.write(0, col, header, header_style)
            ws.col(col).width = 256 * 30
        
        for row, test_case in enumerate(test_cases, start=1):
            ws.write(row, 0, row)
            ws.write(row, 1, test_case.get('description', ''))
            ws.write(row, 2, test_case.get('test_steps', ''))
            ws.write(row, 3, test_case.get('expected_results', ''))
            ws.write(row, 4, test_case.get('status', ''))
            
            ws.row(row).height_mismatch = True
            ws.row(row).height = 20 * 40
        
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        case_count = len(test_cases)
        filename = f"test_cases_{current_time}_{case_count}_cases.xls"
        
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        wb.save(response)
        return response
        
    except Exception as e:
        logger.error(f"Export to Excel failed: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Export to Excel failed: {str(e)}'
        }) 


@require_http_methods(["DELETE"])
def delete_test_cases(request):
    """Delete selected test cases"""
    try:
        ids = request.GET.get('ids', '')
        if not ids:
            return JsonResponse({'success': False, 'message': 'No test case IDs provided'})
            
        test_case_ids = ids.split(',')
        TestCase.objects.filter(id__in=test_case_ids).delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {len(test_case_ids)} test cases'
        })
    except Exception as e:
        logger.error(f"Failed to delete test cases: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Deletion failed: {str(e)}'
        }) 