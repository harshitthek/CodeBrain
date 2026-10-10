"""
Django settings for code_brain project.
"""

import os
import sys
from pathlib import Path


# Configure Hugging Face mirror for SentenceTransformer model downloads
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# Timezone settings
TIME_ZONE = 'UTC'
USE_TZ = False

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Ensure project root directory is in Python path
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key-here'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    '*'
]

# Whether to enable Milvus
ENABLE_MILVUS = False

# Directory configuration for uploaded test case files
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')
MEDIA_URL = '/uploads/'

# Allow all origins for CORS (development use; adjust for production)
CORS_ORIGIN_ALLOW_ALL = True

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Custom applications
    'apps.core',
    'apps.llm',
    # 'apps.knowledge',
    'apps.knowledge.apps.KnowledgeConfig',
    'apps.ai_agents.iface_case_generator.apps.IfaceCaseGeneratorConfig',
    'apps.ai_agents.java_code_analyzer.apps.JavaCodeAnalyzerConfig',
    'apps.ai_agents.prd_analyzer.apps.PrdAnalyzerConfig',
    'apps.ai_agents.test_case_generator.apps.TestCaseGeneratorConfig',
    'apps.ai_agents.test_case_reviewer.apps.TestCaseReviewerConfig',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# Defaults to SQLite for zero-setup local execution (no Docker or MySQL required).
# Set USE_MYSQL=true or provide MYSQL_HOST to use MySQL.
use_mysql = os.environ.get('USE_MYSQL', 'false').lower() == 'true' or bool(os.environ.get('MYSQL_HOST'))
if not use_mysql or os.environ.get('USE_SQLITE', 'false').lower() == 'true' or 'test' in sys.argv or 'pytest' in sys.modules:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('MYSQL_DB', 'code_brain_db'),
            'USER': os.environ.get('MYSQL_USER', 'root'),
            'PASSWORD': os.environ.get('MYSQL_PASSWORD', 'test123456'),
            'HOST': os.environ.get('MYSQL_HOST', 'localhost'),
            'PORT': os.environ.get('MYSQL_PORT', '3306'),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
USE_I18N = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# LLM Providers Configuration
LLM_PROVIDERS = {
    'default_provider': 'deepseek',
    'deepseek': {
        'name': 'DeepSeek',
        # 'model': 'deepseek-chat', # deepseek-reasoner for thinking mode
        # 'api_base': 'https://api.deepseek.com/v1', # official deepseek base_url

        'model': 'deepseek-v3.1',
        'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        
        'temperature': 0.7,
        'max_tokens': 128000,
    },
    'qwen': {
        'name': 'Qwen',
        'model': 'qwen3-max-2025-09-23',
        'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        'temperature': 0.7,
        'max_tokens': 65000,
    },
    'openai': {
        'name': 'OpenAI',
        'model': os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
        'base_url': os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
        'temperature': 0.7,
        'max_tokens': 4096,
    },
    'ollama': {
        'name': 'Ollama (Local)',
        'model': os.getenv('OLLAMA_MODEL', 'llama3'),
        'base_url': os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434/v1'),
        'temperature': 0.7,
        'max_tokens': 4096,
    },
    'groq': {
        'name': 'Groq',
        'model': os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile'),
        'base_url': os.getenv('GROQ_BASE_URL', 'https://api.groq.com/openai/v1'),
        'temperature': 0.7,
        'max_tokens': 4096,
    },
}

# AI Agent LLM provider configuration, customizable per Agent
AGENT_LLM_DEFAULTS = {
    "test_case_generator":  {"provider": "deepseek"},
    "test_case_reviewer":   {"provider": "deepseek"},
    "prd_analyzer":         {"provider": "deepseek"},
    "java_code_analyzer":   {"provider": "deepseek"},
    "iface_case_generator": {"provider": "deepseek"},
}

# Vector Database Configuration
VECTOR_DB_CONFIG = {
    'host': '172.16.50.57',
    'port': '19530',
    'db_name': 'qa_knowledge',
    'collection_name': 'vv_knowledge_collection',
}

# Java Source Code Analyzer Service URL
JAVA_ANALYZER_SERVICE_URL = "http://java-analyzer:80"

# Java Project Configuration
JAVA_PROJECTS_BASE_DIR = "../"
PROJECT_ID_REPO_MAPPING = {
    # Add project mappings here
}

# Git Credentials Configuration
GIT_CREDENTIALS = {
    'username': '',
    'password': '',
}

# Hugging Face tokenizers parallelism setting
os.environ["TOKENIZERS_PARALLELISM"] = "false" 


# Embedding Provider Configuration: "local" (local BGE-M3) | "aliyun" (Aliyun text-embedding-v4)
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "aliyun")

# Aliyun Embedding Configuration
ALIYUN_EMBEDDING_CONFIG = {
    'api_key': os.getenv('QWEN_API_KEY', ''),
    'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings',
    'model': 'text-embedding-v4',
    'batch_size': 10,
}


