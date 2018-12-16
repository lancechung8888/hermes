# coding:utf8
"""
Django settings for backend_python project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = (
    'hermes.apps.HermesConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'hermes.urls'

WSGI_APPLICATION = 'backend_python.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases
#

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }

DATABASES = {
    'local': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'hermes',
        'USER': 'maojingwen',
        'PASSWORD': 'maojingwen_passwd',
        'HOST': '172.16.3.114',
        'PORT': '3306',
    },
}
DATABASES['default'] = DATABASES['local']

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'

# TEMPLATE_DIRS = (os.path.join(BASE_DIR,  'templates'),)
# 请根据自己需要修改TEMPLATE_DIRS目录，默认会设置为settings同级的templates下，里面有默认的404和500页面
TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '../hermes/templates'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist'),
)

STATICFILES_DIRS = (
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist'),
)
STATIC_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist'))
# 这个是默认设置，Django 默认会在 STATICFILES_DIRS中的文件夹 和 各app下的static文件夹中找文件
# 注意有先后顺序，找到了就不再继续找了
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder"
)

# logging setting


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR + '/default.log',
        },

        # 'console':{
        #     'level':'DEBUG',
        #     'class':'logging.StreamHandler',
        #     'formatter': 'simple'
        # },
    },
    'loggers': {
        # 'django': {
        #     'handlers':['console'],
        #     'propagate': True,
        #     'level':'INFO',
        # },
        'backend_python': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

SECRET_KEY = 'bk=5-o+^bfdga*y$s4xt48%ju&v678(he!v930^oq3siq+f+35'

upload_path = None


