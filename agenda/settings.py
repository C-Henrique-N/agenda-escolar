"""
Django settings for agenda project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-@t0vmyn4k)-f%+wg91$+f!(b(-higlpbza0!rq23nkm&%k6ssf'
)

# Em desenvolvimento local (sem variável FLY_APP_NAME), DEBUG fica True por padrão.
# No Fly.io (onde FLY_APP_NAME existe), DEBUG fica False por padrão (a menos que DEBUG=True seja definido).
IS_FLY = bool(os.environ.get('FLY_APP_NAME'))
DEBUG = os.environ.get('DEBUG', 'False' if IS_FLY else 'True').lower() == 'true'

ALLOWED_HOSTS = [
    "agenda-escolar-y01w.onrender.com",
    ".onrender.com",
    'localhost',
    '127.0.0.1',
]

CSRF_TRUSTED_ORIGINS = [
    "https://agenda-escolar-y01w.onrender.com",
    "https://*.onrender.com",
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tarefas',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'agenda.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'agenda.wsgi.application'

# Se houver um volume montado em /data no Fly.io, usa /data/db.sqlite3 e /data/media para persistência
DATA_DIR = Path('/data') if (IS_FLY and Path('/data').exists()) else BASE_DIR

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DATA_DIR / 'db.sqlite3',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"

MEDIA_URL = '/media/'
MEDIA_ROOT = DATA_DIR / 'media'

# Uploads de banner (GIF e vídeos) — evita o 400 padrão do Django acima de 2,5 MB.
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024   # arquivos maiores vão para arquivo temporário


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
