"""
Django settings for schedularos project.
"""

from pathlib import Path
import os
import sys
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent

# Add packages directory to Python path (repo_root/packages)
PACKAGES_DIR = BASE_DIR.parents[2] / 'packages'
if str(PACKAGES_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGES_DIR))

# Add apps directory to Python path (so apps can be imported as 'core', 'orchestration', etc.)
APPS_DIR = BASE_DIR.parent  # This is the api directory containing core, orchestration, etc.
if str(APPS_DIR) not in sys.path:
    sys.path.insert(0, str(APPS_DIR))

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-this-in-production')
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
    'channels',
    'drf_spectacular',
    
    # Local apps
    'core',
    'orchestration',
    'proposals',
    'leads',
    'conversations',
    'agents_api',
    'analytics',
    'tasks_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.OrganizationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'schedularos.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'schedularos.wsgi.application'
ASGI_APPLICATION = 'schedularos.asgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'SchedularOS2'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', '1234'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': os.environ.get('DB_SSLMODE', 'disable'),
        },
    }
}

# Override with DATABASE_URL if provided
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    try:
        import dj_database_url
        DATABASES['default'] = dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=False)
    except ImportError:
        pass

# Redis
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Celery Configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

# Celery Queues (4 queues, different priorities)
CELERY_TASK_QUEUES = {
    'realtime': {
        'exchange': 'realtime',
        'routing_key': 'realtime',
    },
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'bulk': {
        'exchange': 'bulk',
        'routing_key': 'bulk',
    },
    'executor': {
        'exchange': 'executor',
        'routing_key': 'executor',
    },
}

# Celery Beat Schedule
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

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
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DATETIME_FORMAT': 'iso-8601',
    'DATE_FORMAT': 'iso-8601',
    'TIME_FORMAT': 'iso-8601',
    'USE_ISO8601': True,
}

# drf-spectacular Configuration
SPECTACULAR_SETTINGS = {
    'TITLE': 'SchedularOS API',
    'DESCRIPTION': 'Agentic Marketing Automation Platform API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.environ.get('JWT_ACCESS_TOKEN_LIFETIME', 60))),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=int(os.environ.get('JWT_REFRESH_TOKEN_LIFETIME', 1440))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(',')
CORS_ALLOWED_ORIGIN_REGEXES = [r"^http://(localhost|127\.0\.0\.1)(:\d+)?$"]
CORS_ALLOW_CREDENTIALS = True

# Channels (WebSocket)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}

# Jev LLM Configuration
LLM_CONFIG = {
    'jev_api_key': os.environ.get('JEV_API_KEY', ''),
    'jev_api_endpoint': os.environ.get('JEV_API_ENDPOINT', 'https://api.jev.ai/v1'),
    'fast_model': os.environ.get('JEV_FAST_MODEL', 'jev-1.5-flash'),
    'balanced_model': os.environ.get('JEV_BALANCED_MODEL', 'jev-1.5-pro'),
    'deep_model': os.environ.get('JEV_DEEP_MODEL', 'jev-1.5-pro-deep'),
    'decision_model': os.environ.get('JEV_DECISION_MODEL', 'jev-decision-v1'),
    
    # Cache TTLs per tier
    'cache_ttl_fast': 300,      # 5 minutes
    'cache_ttl_balanced': 600,  # 10 minutes
    'cache_ttl_deep': 1800,     # 30 minutes
    
    # Fallback to OpenAI if Jev is not available
    'fallback_to_openai': True,
    'openai_api_key': os.environ.get('OPENAI_API_KEY', ''),
    'openai_fast_model': os.environ.get('OPENAI_FAST_MODEL', 'gpt-4o-mini'),
    'openai_balanced_model': os.environ.get('OPENAI_BALANCED_MODEL', 'gpt-4o'),
    'openai_deep_model': os.environ.get('OPENAI_DEEP_MODEL', 'gpt-4o'),
}

# External API Configuration
META_CONFIG = {
    'access_token': os.environ.get('META_ACCESS_TOKEN', ''),
    'ad_account_id': os.environ.get('META_AD_ACCOUNT_ID', ''),
    'app_id': os.environ.get('META_APP_ID', ''),
    'app_secret': os.environ.get('META_APP_SECRET', ''),
    'phone_number_id': os.environ.get('META_PHONE_NUMBER_ID', ''),
}

GOOGLE_ADS_CONFIG = {
    'developer_token': os.environ.get('GOOGLE_ADS_DEVELOPER_TOKEN', ''),
    'client_id': os.environ.get('GOOGLE_ADS_CLIENT_ID', ''),
    'client_secret': os.environ.get('GOOGLE_ADS_CLIENT_SECRET', ''),
    'refresh_token': os.environ.get('GOOGLE_ADS_REFRESH_TOKEN', ''),
    'customer_id': os.environ.get('GOOGLE_ADS_CUSTOMER_ID', ''),
}

CONTENT_GEN_CONFIG = {
    'api_key': os.environ.get('CONTENT_GEN_API_KEY', ''),
    'api_endpoint': os.environ.get('CONTENT_GEN_API_ENDPOINT', 'https://api.openai.com/v1'),
    'image_model': os.environ.get('CONTENT_GEN_IMAGE_MODEL', 'dall-e-3'),
    'video_model': os.environ.get('CONTENT_GEN_VIDEO_MODEL', 'runway-gen3'),
}

SEARCH_CONFIG = {
    'api_key': os.environ.get('SEARCH_API_KEY', ''),
}

EMAIL_CONFIG = {
    'aws_access_key_id': os.environ.get('AWS_ACCESS_KEY_ID', ''),
    'aws_secret_access_key': os.environ.get('AWS_SECRET_ACCESS_KEY', ''),
    'aws_ses_region': os.environ.get('AWS_SES_REGION', 'us-east-1'),
    'verified_sender': os.environ.get('AWS_SES_VERIFIED_SENDER', ''),
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'schedularos': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Create logs directory
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
