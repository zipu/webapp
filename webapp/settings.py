"""
Django settings for webapp project.

Generated by 'django-admin startproject' using Django 2.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
""" 

import json
import os
from django.core.exceptions import ImproperlyConfigured
#from google.oauth2 import service_account

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_secret(setting):
    """Get secret setting or fail with ImproperlyConfigured"""
    
    with open(os.path.join(BASE_DIR, 'secrets.json')) as secrets_file:
        secrets = json.load(secrets_file)
    
    try:
        return secrets[setting]
    except KeyError:
        raise ImproperlyConfigured("Set the {} setting".format(setting))



# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/


# Modifications after upgraded to django 4
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY") if os.getenv("ON_CLOUD") else get_secret("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 60 * 60 * 24 #* 7 

if os.getenv('ON_CLOUD', None) == 'true':
    DEBUG = False
else:
    DEBUG = True

#DEBUG = False

if DEBUG == False:
    #SECURE_SSL_REDIRECT = True
    #SECURE_HSTS_SECONDS = 3600
    #SESSION_COOKIE_SECURE = True
    #SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')
    #CSRF_COOKIE_SECURE = True
    #SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    #SECURE_CONTENT_TYPE_NOSNIFF = True
    #SECURE_BROWSER_XSS_FILTER = True    
    #X_FRAME_OPTIONS = 'DENY'
    #SECURE_HSTS_PRELOAD = True
    pass

CSRF_TRUSTED_ORIGINS = [
        'https://*.azurewebsites.net',
    ]
ALLOWED_HOSTS = ['*']


# Application definition
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    )
}


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize', #humanize app like 'intcomma'
    'maths.apps.MathsConfig', #수학자료
    'tutoring.apps.TutoringConfig', # 과외 
    'trading.apps.TradingConfig', #트레이딩 ,
    'aops.apps.AopsConfig' #수학문제, art of problem solving
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
    'webapp.middleware.LoginRequiredMiddleware', #custom login middleware
]

ROOT_URLCONF = 'webapp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'webapp/templates/webapp'),
            #os.path.join(BASE_DIR, 'maths/templates'),
           # os.path.join(BASE_DIR, 'trading/templates'),
            #os.path.join(BASE_DIR, 'aops/templates'),

        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'webapp.context_processors.constants'
            ],
        },
    },
]

WSGI_APPLICATION = 'webapp.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
DATABASE_ROUTERS = [
    'maths.dbRouter.MathsDBRouter',
    'trading.dbRouter.TradingDBRouter',
    'aops.dbRouter.AopsDBRouter',
    'tutoring.dbRouter.TutoringDBRouter',
]



# [START db_setup]
REMOTE = True
PORT = '3306' 

if os.getenv('ON_CLOUD', None):
    # Running on production App Engine, so connect to Google Cloud SQL using
    # the unix socket at /cloudsql/<your-cloudsql-connection string>
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'PORT': PORT,
            'HOST': os.getenv('DB_HOST'),
            'USER': os.getenv('DB_USERNAME'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'NAME': 'webapp',
        },
        'maths': {
            'ENGINE': 'django.db.backends.mysql',
            'PORT': PORT,
            'HOST': os.getenv('DB_HOST'),
            'USER': os.getenv('DB_USERNAME'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'NAME': 'maths',
        },
        'trading' : {
            'ENGINE': 'django.db.backends.mysql',
            'PORT': PORT,
            'HOST': os.getenv('DB_HOST'),
            'USER': os.getenv('DB_USERNAME'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'NAME': 'trading'
        },
        'aops' : {
            'ENGINE': 'django.db.backends.mysql',
            'PORT': PORT,
            'HOST': os.getenv('DB_HOST'),
            'USER': os.getenv('DB_USERNAME'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'NAME': 'aops'
        },
        'tutoring' : {
            'ENGINE': 'django.db.backends.mysql',
            'PORT': PORT,
            'HOST': os.getenv('DB_HOST'),
            'USER': os.getenv('DB_USERNAME'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'NAME': 'tutoring'
        }
    }
elif REMOTE:
    # Running locally so connect to either a local MySQL instance or connect to
    # Cloud SQL via the proxy. To start the proxy via command line:
    #
    #     $ cloud_sql_proxy -instances=[INSTANCE_CONNECTION_NAME]=tcp:3306
    #
    # See https://cloud.google.com/sql/docs/mysql-connect-proxy
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': get_secret('REMOTE_HOST'),
            'PORT': PORT,
            'NAME': 'webapp',
            'USER': get_secret('DB_USERNAME'),
            'PASSWORD': get_secret('REMOTE_PASSWORD'),
        },
        'maths' :{
            'ENGINE': 'django.db.backends.mysql',
            'HOST': get_secret('REMOTE_HOST'),
            'PORT': PORT,
            'NAME': 'maths',
            'USER': get_secret('DB_USERNAME'),
            'PASSWORD': get_secret('REMOTE_PASSWORD'),
        },
        'trading' : {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': get_secret('REMOTE_HOST'),
            'PORT': PORT,
            'NAME': 'trading',
            'USER': get_secret('DB_USERNAME'),
            'PASSWORD': get_secret('REMOTE_PASSWORD'),
        },
        'aops' : {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': get_secret('REMOTE_HOST'),
            'PORT': PORT,
            'NAME': 'aops',
            'USER': get_secret('DB_USERNAME'),
            'PASSWORD': get_secret('REMOTE_PASSWORD'),
        },
        'tutoring' : {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': get_secret('REMOTE_HOST'),
            'PORT': PORT,
            'NAME': 'tutoring',
            'USER': get_secret('DB_USERNAME'),
            'PASSWORD': get_secret('REMOTE_PASSWORD'),
        }
    }

else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': '127.0.0.1',
            'PORT': PORT,
            'NAME': 'webapp',
            'USER': get_secret('DB_USERNAME'),
            'PASSWORD': get_secret('DB_PASSWORD'),
        },
        'maths' :{
            'ENGINE': 'django.db.backends.mysql',
            'HOST': '127.0.0.1',
            'PORT': PORT,
            'NAME': 'maths',
            'USER': get_secret('DB_USERNAME'),
            'PASSWORD': get_secret('DB_PASSWORD'),
        },
        'trading' : {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': '127.0.0.1',
            'PORT': PORT,
            'NAME': 'trading',
            'USER': get_secret('DB_USERNAME'),
            'PASSWORD': get_secret('DB_PASSWORD'),
        },
        'aops' : {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': '127.0.0.1',
            'PORT': PORT,
            'NAME': 'aops',
            'USER': get_secret('DB_USERNAME'),
            'PASSWORD': get_secret('DB_PASSWORD'),
        },
        'tutoring' : {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': '127.0.0.1',
            'PORT': PORT,
            'NAME': 'tutoring',
            'USER': get_secret('DB_USERNAME'),
            'PASSWORD': get_secret('DB_PASSWORD'),
        }
    }


# [END db_setup]


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'#'UTC'
USE_TZ = False

USE_I18N = True

USE_L10N = True




# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_ROOT = './static/' #if os.getenv('ON_CLOUD') else 'static' #os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'


STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "webapp/static"),
    os.path.join(BASE_DIR, "maths/static"),
    os.path.join(BASE_DIR, "tutoring/static"),
]

# Media files (유저 업로드 파일들)


if os.getenv('ON_CLOUD', None):
    DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    AZURE_ACCOUNT_NAME = os.getenv('STORAGE_ACCOUNT_NAME')
    AZURE_ACCOUNT_KEY = os.getenv('STORAGE_ACCOUNT_KEY')
    AZURE_CONTAINER = "webapp"
    AZURE_SSL = False
    
    MEDIA_URL = f'https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/webapp/'

else:
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
    MEDIA_URL = '/media/'


#login
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

#version
MATH_APP_VERSION = '1.23' 