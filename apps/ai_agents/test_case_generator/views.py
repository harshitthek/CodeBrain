import json
from django.http import JsonResponse
from apps.llm import LLMServiceFactory
from apps.ai_agents.test_case_generator.generator import TestCaseGeneratorAgent
from apps.core.models import TestCase
from apps.utils.logger_manager import get_logger
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from apps.knowledge.service import get_knowledgeService_instance
from apps.llm.utils import get_agent_llm_configs


logger = get_logger(__name__)

DEFAULT_PROVIDER, PROVIDERS = get_agent_llm_configs("test_case_generator")
knowledge_service = get_knowledgeService_instance()


async def generate(request):
    """
    View function for test case generation page
    """
    logger.info("===== Entering generate view =====")
    logger.info(f"Request method: {request.method}")
    context = {
        'llm_providers': PROVIDERS,
        'llm_provider': DEFAULT_PROVIDER,
        'requirement': '',
        'test_cases': None
    }
    
    if request.method == 'GET':
        return render(request, 'generate.html', context)
    
    # POST request body parsing
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        logger.error("JSON parse error", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    
    # Parameters validation
    requirements = data.get('requirements', '')
    if not requirements:
        return JsonResponse({
            'success': False,
            'message': 'Requirements description cannot be empty'
        })
        
    llm_provider = data.get('llm_provider', DEFAULT_PROVIDER)
    case_design_methods = data.get('case_design_methods', [])
    case_categories = data.get('case_categories', [])
    case_count = int(data.get('case_count', 10))
    
    logger.info(f"Received data: {json.dumps(data, ensure_ascii=False)}")
    
    try:
        logger.info(f"Using {llm_provider} to generate test cases")
        llm_service = LLMServiceFactory.create(llm_provider)

        generator_agent = TestCaseGeneratorAgent(
            llm_service=llm_service,
            knowledge_service=knowledge_service,
            case_design_methods=case_design_methods,
            case_categories=case_categories,
            case_count=case_count
        )
        logger.info(f"Starting test case generation - requirements: {requirements}...")
        logger.info(f"Selected case design methods: {case_design_methods}")
        logger.info(f"Selected case categories: {case_categories}")
        logger.info(f"Test case count: {case_count}")
        
        test_cases = await generator_agent.async_generate(requirements, input_type="requirement")

        logger.info(f"Test cases generated successfully - count: {len(test_cases)}")
        
        context.update({
            'test_cases': test_cases
        })
        
        return JsonResponse({
            'success': True,
            'test_cases': test_cases
        })
            
    except Exception as e:
        logger.error(f"Error generating test cases: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@require_http_methods(["POST"])
def save_test_case(request):
    """Save test cases"""
    try:
        data = json.loads(request.body)
        requirement = data.get('requirement')
        test_cases_list = data.get('test_cases', [])
        llm_provider = data.get('llm_provider')
        
        if not test_cases_list:
            return JsonResponse({
                'success': False,
                'message': 'Test case data is empty'
            }, status=400)
        
        test_cases_to_create = []
        
        for index, test_case in enumerate(test_cases_list, 1):
            test_case_instance = TestCase(
                title=f"Test Case-{index}",
                description=test_case.get('description', ''),
                test_steps='\n'.join(test_case.get('test_steps', [])),
                expected_results='\n'.join(test_case.get('expected_results', [])),
                requirements=requirement,
                llm_provider=llm_provider,
                status='pending'
            )
            test_cases_to_create.append(test_case_instance)
        
        created_test_cases = TestCase.objects.bulk_create(test_cases_to_create)
        
        logger.info(f"Successfully saved {len(created_test_cases)} test cases")
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully saved {len(created_test_cases)} test cases',
            'test_case_id': [case.id for case in created_test_cases]
        })
        
    except json.JSONDecodeError:
        logger.error("JSON parse error", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error saving test cases: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Save failed: {str(e)}'
        }, status=500)