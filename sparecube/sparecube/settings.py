from pathlib import Path
import os
import dotenv
import datetime

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Adding the secret variables here!
dotenv_file = os.path.join(BASE_DIR, ".env")
if os.path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']





# region | Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',

    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    
    'account',
    'locker',
]


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES' : [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES' : (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME' : datetime.timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': datetime.timedelta(days=1),
    'AUTH_HEADER_TYPES': ("Bearer",),
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME' : datetime.timedelta(days=1),
    'SLIDING_TOKEN_REFRESH_LIFETIME': datetime.timedelta(days=30),
    'ALGORITHM' : 'HS256',
    'SIGNING_KEY': os.environ['JWT_KEY'],
}




MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# endregion



# region | CORS
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
]

CORS_ALLOWED_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
)

CORS_ALLOWED_HEADERS = (
    'Access-Control-Allow-Origin',
    'accept',
    'authorization',
    'content-type',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
)

# endregion



# region | Urls and Templates

ROOT_URLCONF = 'sparecube.urls'

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

WSGI_APPLICATION = 'sparecube.wsgi.application'

# endregion



# region | Database Definition

DATABASES = {
    'default': {
        'ENGINE' : 'mssql',
        'NAME' : os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ['DB_ADDRESS'],
        'PORT': os.environ['DB_PORT'],
        'OPTIONS': {
            'driver': os.environ['DB_DRIVER'],
            'host_is_server' : True,
        },
    }
}

# endregion



# region | Authentication

AUTH_USER_MODEL = 'account.Utente'

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

# endregion


#region | MQTT Configurations
MQTT_CONFIG = {
    "BROKER_URL": os.getenv("MQTT_BROKER_URL"),
    "BROKER_PORT": int(os.getenv("MQTT_BROKER_PORT", 8883)),
    "CLIENT_ID": os.getenv("MQTT_CLIENT_ID"),
    "USERNAME": os.getenv("MQTT_USERNAME"),
    "PASSWORD": os.getenv("MQTT_PASSWORD"),
}
# endregion


# region | Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# endregion



# region | Static files (CSS, JavaScript, Images)

STATIC_URL = 'static/'

# endregion

# region | Default primary key field type

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# endregion
