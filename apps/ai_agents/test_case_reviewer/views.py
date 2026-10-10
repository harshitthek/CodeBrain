from apps.core.models import TestCase, TestCaseReview
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
        
        # Persist review record in database
        try:
            reviewer_user = request.user if request.user.is_authenticated else None
            TestCaseReview.objects.create(
                test_case=test_case,
                reviewer=reviewer_user,
                review_comments=review_content
            )
            logger.info(f"Saved TestCaseReview record for TestCase id={test_case.id}")
        except Exception as save_err:
            logger.warning(f"Failed to persist review record: {str(save_err)}")

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
    """Export test cases to modern Excel (.xlsx) file using openpyxl"""
    try:
        from io import BytesIO
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter

        ids = request.GET.get('ids')
        if not ids or ids.strip() == 'all':
            test_cases_qs = TestCase.objects.all().order_by('-created_at')
            test_cases = [
                {
                    'id': tc.id,
                    'title': tc.title,
                    'description': tc.description,
                    'test_steps': tc.test_steps,
                    'expected_results': tc.expected_results,
                    'status': tc.status,
                    'priority': tc.priority or 'P2'
                }
                for tc in test_cases_qs
            ]
        else:
            response = get_test_cases(request, ids)
            response_data = json.loads(response.content)
            if not response_data.get('success'):
                return JsonResponse({'success': False, 'message': 'Failed to retrieve test case data'})
            test_cases = response_data.get('test_cases', [])

        if not test_cases:
            return JsonResponse({'success': False, 'message': 'No test cases to export'})

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Test Cases"

        headers = ['No.', 'ID', 'Description', 'Test Steps', 'Expected Results', 'Status', 'Priority']
        ws.append(headers)

        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
        thin_border = Border(
            left=Side(style='thin', color='D9D9D9'),
            right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'),
            bottom=Side(style='thin', color='D9D9D9')
        )
        alignment_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
        alignment_left = Alignment(horizontal="left", vertical="top", wrap_text=True)

        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = alignment_center
            cell.border = thin_border

        for idx, tc in enumerate(test_cases, start=1):
            row_num = idx + 1
            ws.append([
                idx,
                tc.get('id', ''),
                tc.get('description', ''),
                tc.get('test_steps', ''),
                tc.get('expected_results', ''),
                tc.get('status', ''),
                tc.get('priority', 'P2')
            ])
            for col_num in range(1, len(headers) + 1):
                cell = ws.cell(row=row_num, column=col_num)
                cell.border = thin_border
                if col_num in [1, 2, 6, 7]:
                    cell.alignment = alignment_center
                else:
                    cell.alignment = alignment_left

        col_widths = {1: 8, 2: 10, 3: 40, 4: 45, 5: 40, 6: 15, 7: 12}
        for col_num, width in col_widths.items():
            col_letter = get_column_letter(col_num)
            ws.column_dimensions[col_letter].width = width

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_cases_{current_time}_{len(test_cases)}_cases.xlsx"

        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
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