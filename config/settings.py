"""
Django settings for code_brain project.
"""

import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Configure Hugging Face mirror for SentenceTransformer model downloads
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# Timezone settings
TIME_ZONE = "UTC"
USE_TZ = False

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Make the documented local `.env` setup work for every Django entry point,
# including `manage.py runserver`, before any setting reads its value.
load_dotenv(BASE_DIR / ".env")

# Ensure project root directory is in Python path
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def env_bool(name: str, default: bool = False) -> bool:
    """Parse boolean environment variables consistently across local and deployed runs."""
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_csv(name: str, default: str = "") -> list[str]:
    return [
        item.strip() for item in os.getenv(name, default).split(",") if item.strip()
    ]


TESTING = "pytest" in sys.modules or "test" in sys.argv
DEBUG = env_bool("DJANGO_DEBUG", False)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG or TESTING:
        SECRET_KEY = "django-insecure-development-only-not-for-production"
    else:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is false."
        )

ALLOWED_HOSTS = env_csv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]")

# Whether to enable Milvus
ENABLE_MILVUS = env_bool("ENABLE_MILVUS", False)

# Directory configuration for uploaded test case files
MEDIA_ROOT = os.path.join(BASE_DIR, "uploads")
MEDIA_URL = "/uploads/"

# CORS middleware is optional; deployments should explicitly list trusted web clients.
CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOWED_ORIGINS = env_csv("CORS_ALLOWED_ORIGINS")

# Keep secure transport opt-in locally, but make the production boundary explicit
# and configurable at the process environment rather than in source control.
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", False)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", False)
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Custom applications
    "apps.core",
    "apps.llm",
    # 'apps.knowledge',
    "apps.knowledge.apps.KnowledgeConfig",
    "apps.ai_agents.iface_case_generator.apps.IfaceCaseGeneratorConfig",
    "apps.ai_agents.java_code_analyzer.apps.JavaCodeAnalyzerConfig",
    "apps.ai_agents.prd_analyzer.apps.PrdAnalyzerConfig",
    "apps.ai_agents.test_case_generator.apps.TestCaseGeneratorConfig",
    "apps.ai_agents.test_case_reviewer.apps.TestCaseReviewerConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
# Defaults to SQLite for zero-setup local execution (no Docker or MySQL required).
# Set USE_MYSQL=true or provide MYSQL_HOST to use MySQL.
use_mysql = os.environ.get("USE_MYSQL", "false").lower() == "true" or bool(
    os.environ.get("MYSQL_HOST")
)
if (
    not use_mysql
    or os.environ.get("USE_SQLITE", "false").lower() == "true"
    or "test" in sys.argv
    or "pytest" in sys.modules
):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("MYSQL_DB", "code_brain_db"),
            "USER": os.environ.get("MYSQL_USER", "root"),
            "PASSWORD": os.environ.get("MYSQL_PASSWORD", ""),
            "HOST": os.environ.get("MYSQL_HOST", "localhost"),
            "PORT": os.environ.get("MYSQL_PORT", "3306"),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
USE_I18N = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# LLM Providers Configuration
LLM_PROVIDERS = {
    "default_provider": "deepseek",
    "asi1": {
        "name": "ASI:One",
        "model": os.getenv("ASI1_MODEL", "asi1-mini"),
        "base_url": os.getenv("ASI1_BASE_URL", "https://api.asi1.ai/v1"),
        # Bound agent turns when an upstream ASI:One response stalls.
        "timeout": float(os.getenv("ASI1_REQUEST_TIMEOUT", "60")),
        "temperature": 0.2,
        "max_tokens": 4096,
    },
    "deepseek": {
        "name": "DeepSeek",
        # 'model': 'deepseek-chat', # deepseek-reasoner for thinking mode
        # 'api_base': 'https://api.deepseek.com/v1', # official deepseek base_url
        "model": "deepseek-v3.1",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "temperature": 0.7,
        "max_tokens": 128000,
    },
    "qwen": {
        "name": "Qwen",
        "model": "qwen3-max-2025-09-23",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "temperature": 0.7,
        "max_tokens": 65000,
    },
    "openai": {
        "name": "OpenAI",
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "temperature": 0.7,
        "max_tokens": 4096,
    },
    "ollama": {
        "name": "Ollama (Local)",
        "model": os.getenv("OLLAMA_MODEL", "llama3"),
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        "temperature": 0.7,
        "max_tokens": 4096,
    },
    "groq": {
        "name": "Groq",
        "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "base_url": os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        "temperature": 0.7,
        "max_tokens": 4096,
    },
}

# AI Agent LLM provider configuration, customizable per Agent
AGENT_LLM_DEFAULTS = {
    "test_case_generator": {"provider": "deepseek"},
    "test_case_reviewer": {"provider": "deepseek"},
    "prd_analyzer": {"provider": "deepseek"},
    "java_code_analyzer": {"provider": "deepseek"},
    "iface_case_generator": {"provider": "deepseek"},
}

# Fetch-a-thon Release Guardian is isolated from the existing web defaults so the
# legacy platform remains configurable while the ACP agent clearly uses ASI:One.
RELEASE_GUARDIAN_LLM_PROVIDER = os.getenv("RELEASE_GUARDIAN_LLM_PROVIDER", "asi1")
# ASI:One chat needs a bounded first response. The result remains a QA signal,
# and deployments can raise this threshold if they prefer a longer refinement loop.
RELEASE_GUARDIAN_MIN_SCORE = float(os.getenv("RELEASE_GUARDIAN_MIN_SCORE", "60"))
RELEASE_GUARDIAN_ALLOWED_TARGETS = tuple(
    env_csv("RELEASE_GUARDIAN_ALLOWED_TARGETS", "configured_repository")
)
RELEASE_GUARDIAN_REPO_PATH = os.getenv("RELEASE_GUARDIAN_REPO_PATH", "").strip()
RELEASE_GUARDIAN_REPO_TEST_COMMAND = os.getenv(
    "RELEASE_GUARDIAN_REPO_TEST_COMMAND", "python -m pytest -q"
).strip()
RELEASE_GUARDIAN_REPO_TEST_TIMEOUT = int(
    os.getenv("RELEASE_GUARDIAN_REPO_TEST_TIMEOUT", "120")
)

# Vector Database Configuration
VECTOR_STORE_BACKEND = os.getenv("VECTOR_STORE_BACKEND", "chroma")
CHROMA_PERSIST_DIR = os.path.join(BASE_DIR, "data", "chroma_db")

VECTOR_DB_CONFIG = {
    "host": os.getenv("MILVUS_HOST", "172.16.50.57"),
    "port": os.getenv("MILVUS_PORT", "19530"),
    "db_name": "qa_knowledge",
    "collection_name": "vv_knowledge_collection",
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
    "username": "",
    "password": "",
}

# Hugging Face tokenizers parallelism setting
os.environ["TOKENIZERS_PARALLELISM"] = "false"


# Embedding Provider Configuration: "local" (local BGE-M3) | "aliyun" (Aliyun text-embedding-v4)
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "aliyun")
KNOWLEDGE_ENABLED = env_bool("CODEBRAIN_KNOWLEDGE_ENABLED", True)

# Aliyun Embedding Configuration
ALIYUN_EMBEDDING_CONFIG = {
    "api_key": os.getenv("QWEN_API_KEY", ""),
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings",
    "model": "text-embedding-v4",
    "batch_size": 10,
}
