import environ
import os
from celery.schedules import crontab

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['127.0.0.1',]),
    TIME_ZONE=(str, "UTC"),
    SERVER_EMAIL=(str, "root@localhost"),
    DB_ENGINE=(str, "django.db.backends.sqlite3"),
    DB_NAME=(str, "db.sqlite3"),
    DB_USER=(str, ""),
    DB_PASSWORD=(str, ""),
    DB_HOST=(str, ""),
    DB_PORT=(int, ""),
    CELERY_BROKER_HOST=(str, "localhost"),
    EMAIL_HOST=(str, "localhost"),
    EMAIL_PORT=(int, 25),
    EMAIL_HOST_USER=(str, ""),
    EMAIL_HOST_PASSWORD=(str, ""),
    EMAIL_USE_TLS=(bool, False),
    EMAIL_USE_SSL=(bool, False),
    EMAIL_SSL_CERTFILE=(str, None),
    EMAIL_SSL_KEYFILE=(str, None),
    EMAIL_TIMEOUT=(str, None),
    DEFAULT_FROM_EMAIL=(str, "webmaster@localhost"),
    EMAIL_SUBJECT_PREFIX=(str, "[Django] "),
    SECURE_PROXY_SSL_HEADER=(str, None),
    LOGGING_FILE=(str, "boxes.log"),
    LOGGING_LEVEL=(str, "DEBUG"),
    SESSION_COOKIE_SECURE=(bool, True),
    CSRF_COOKIE_SECURE=(bool, True),
    SECURE_CONTENT_TYPE_NOSNIFF=(bool, True),
    SECURE_CROSS_ORIGIN_OPENER_POLICY=(str, "same-origin"),
    SECURE_HSTS_INCLUDE_SUBDOMAINS=(bool, True),
    SECURE_HSTS_PRELOAD=(bool, True),
    SECURE_HSTS_SECONDS=(int, 60),
    SECURE_REDIRECT_EXEMPT=(list, []),
    SECURE_REFERRER_POLICY=(str, "same-origin"),
    SECURE_SSL_HOST=(str, None),
    SECURE_SSL_REDIRECT=(bool, True),
    STRIPE_API_KEY=(str, None),
)

# Set the project base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Take environment variables from .env file
environ.Env.read_env(env.str('ENV_PATH', '/etc/boxes.env'))


# This is defined here as a do-nothing function because we can't import
# django.utils.translation -- that module depends on the settings.
def gettext_noop(s):
    return s

####################
# CORE             #
####################

# False if not in os.environ because of casting above
DEBUG = env('DEBUG')

# Whether the framework should propagate raw exceptions rather than catching
# them. This is useful under some testing situations and should never be used
# on a live site.
DEBUG_PROPAGATE_EXCEPTIONS = False

# People who get code error notifications. In the format
# [('Full Name', 'email@example.com'), ('Full Name', 'anotheremail@example.com')]
ADMINS = []

# List of IP addresses, as strings, that:
#   * See debug comments, when DEBUG is true
#   * Receive x-headers
INTERNAL_IPS = []

# Hosts/domain names that are valid for this site.
# "*" matches anything, ".example.com" matches example.com and all subdomains
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# Local time zone for this installation. All choices can be found here:
# https://en.wikipedia.org/wiki/List_of_tz_zones_by_name (although not all
# systems may support all possibilities). When USE_TZ is True, this is
# interpreted as the default user time zone.
TIME_ZONE = env('TIME_ZONE')

# If you set this to True, Django will use timezone-aware datetimes.
USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en-us"

# Languages we provide translations for, out of the box.
LANGUAGES = [
    ("en", gettext_noop("English")),
    ("en-au", gettext_noop("Australian English")),
    ("en-gb", gettext_noop("British English")),
]

# Languages using BiDi (right-to-left) layout
LANGUAGES_BIDI = []

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
LOCALE_PATHS = []

# Settings for language cookie
LANGUAGE_COOKIE_NAME = "django_language"
LANGUAGE_COOKIE_AGE = None
LANGUAGE_COOKIE_DOMAIN = None
LANGUAGE_COOKIE_PATH = "/"
LANGUAGE_COOKIE_SECURE = False
LANGUAGE_COOKIE_HTTPONLY = False
LANGUAGE_COOKIE_SAMESITE = None

# Not-necessarily-technical managers of the site. They get broken link
# notifications and other various emails.
MANAGERS = ADMINS

# Default charset to use for all HttpResponse objects, if a MIME type isn't
# manually specified. It's used to construct the Content-Type header.
DEFAULT_CHARSET = "utf-8"

# Email address that error messages come from.
SERVER_EMAIL = env('SERVER_EMAIL')

# Database connection info. If left empty, will default to the dummy backend.
DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE"),
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
    }
}

# Classes used to implement DB routing behavior.
DATABASE_ROUTERS = []

# The email backend to use. For possible shortcuts see django.core.mail.
# The default is to use the SMTP backend.
# Third-party backends can be specified by providing a Python path
# to a module that defines an EmailBackend class.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Host for sending email.
EMAIL_HOST = env('EMAIL_HOST')

# Port for sending email.
EMAIL_PORT = env('EMAIL_PORT')

# Whether to send SMTP 'Date' header in the local time zone or in UTC.
EMAIL_USE_LOCALTIME = True

# Optional SMTP authentication information for EMAIL_HOST.
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = env('EMAIL_USE_TLS')
EMAIL_USE_SSL = env('EMAIL_USE_SSL')
EMAIL_SSL_CERTFILE = env('EMAIL_SSL_CERTFILE')
EMAIL_SSL_KEYFILE = env('EMAIL_SSL_KEYFILE')
EMAIL_TIMEOUT = env('EMAIL_TIMEOUT')

# List of strings representing installed apps.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "boxes",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'boxes/templates')],
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

# Default form rendering class.
FORM_RENDERER = "django.forms.renderers.DjangoTemplates"

# RemovedInDjango60Warning: It's a transitional setting helpful in early
# adoption of "https" as the new default value of forms.URLField.assume_scheme.
# Set to True to assume "https" during the Django 5.x release cycle.
FORMS_URLFIELD_ASSUME_HTTPS = False

# Default email address to use for various automated correspondence from
# the site managers.
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')

# Subject-line prefix for email messages send with django.core.mail.mail_admins
# or ...mail_managers.  Make sure to include the trailing space.
EMAIL_SUBJECT_PREFIX = env('EMAIL_SUBJECT_PREFIX')

# Whether to append trailing slashes to URLs.
APPEND_SLASH = True

# Whether to prepend the "www." subdomain to URLs that don't have it.
PREPEND_WWW = False

# Override the server-derived value of SCRIPT_NAME
FORCE_SCRIPT_NAME = None

# List of compiled regular expression objects representing User-Agent strings
# that are not allowed to visit any page, systemwide. Use this for bad
# robots/crawlers. Here are a few examples:
#     import re
#     DISALLOWED_USER_AGENTS = [
#         re.compile(r'^NaverBot.*'),
#         re.compile(r'^EmailSiphon.*'),
#         re.compile(r'^SiteSucker.*'),
#         re.compile(r'^sohu-search'),
#     ]
DISALLOWED_USER_AGENTS = []

ABSOLUTE_URL_OVERRIDES = {}

# List of compiled regular expression objects representing URLs that need not
# be reported by BrokenLinkEmailsMiddleware. Here are a few examples:
#    import re
#    IGNORABLE_404_URLS = [
#        re.compile(r'^/apple-touch-icon.*\.png$'),
#        re.compile(r'^/favicon.ico$'),
#        re.compile(r'^/robots.txt$'),
#        re.compile(r'^/phpmyadmin/'),
#        re.compile(r'\.(cgi|php|pl)$'),
#    ]
IGNORABLE_404_URLS = []

# A secret key for this particular Django installation. Used in secret-key
# hashing algorithms. Set this in your settings, or Django will complain
# loudly.
SECRET_KEY = env('SECRET_KEY')

# List of secret keys used to verify the validity of signatures. This allows
# secret key rotation.
SECRET_KEY_FALLBACKS = []

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
}

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "public/media")

# URL that handles the media served from MEDIA_ROOT.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = "/media/"

# Absolute path to the directory static files should be collected to.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "public/static")

# URL that handles the static files served from STATIC_ROOT.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = "/static/"

# Custom path, for non-public files we'd like to serve
SECURE_ROOT = os.path.join(BASE_DIR, ".secure_storage")

# List of upload handler classes to be applied in order.
FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
]

# Maximum size, in bytes, of a request before it will be streamed to the
# file system instead of into memory.
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # i.e. 2.5 MB

# Maximum size in bytes of request data (excluding file uploads) that will be
# read before a SuspiciousOperation (RequestDataTooBig) is raised.
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # i.e. 2.5 MB

# Maximum number of GET/POST parameters that will be read before a
# SuspiciousOperation (TooManyFieldsSent) is raised.
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Maximum number of files encoded in a multipart upload that will be read
# before a SuspiciousOperation (TooManyFilesSent) is raised.
DATA_UPLOAD_MAX_NUMBER_FILES = 100

# Directory in which upload streamed files will be temporarily saved. A value of
# `None` will make Django use the operating system's default temporary directory
# (i.e. "/tmp" on *nix systems).
FILE_UPLOAD_TEMP_DIR = None

# The numeric mode to set newly-uploaded files to. The value should be a mode
# you'd pass directly to os.chmod; see
# https://docs.python.org/library/os.html#files-and-directories.
FILE_UPLOAD_PERMISSIONS = 0o644

# The numeric mode to assign to newly-created directories, when uploading files.
# The value should be a mode as you'd pass to os.chmod;
# see https://docs.python.org/library/os.html#files-and-directories.
FILE_UPLOAD_DIRECTORY_PERMISSIONS = None

# Python module path where user will place custom format definition.
# The directory where this setting is pointing should contain subdirectories
# named as the locales, containing a formats.py file
# (i.e. "myproject.locale" for myproject/locale/en/formats.py etc. use)
FORMAT_MODULE_PATH = None

# Default formatting for date objects. See all available format strings here:
# https://docs.djangoproject.com/en/dev/ref/templates/builtins/#date
DATE_FORMAT = "N j, Y"

# Default formatting for datetime objects. See all available format strings here:
# https://docs.djangoproject.com/en/dev/ref/templates/builtins/#date
DATETIME_FORMAT = "N j, Y, P"

# Default formatting for time objects. See all available format strings here:
# https://docs.djangoproject.com/en/dev/ref/templates/builtins/#date
TIME_FORMAT = "P"

# Default formatting for date objects when only the year and month are relevant.
# See all available format strings here:
# https://docs.djangoproject.com/en/dev/ref/templates/builtins/#date
YEAR_MONTH_FORMAT = "F Y"

# Default formatting for date objects when only the month and day are relevant.
# See all available format strings here:
# https://docs.djangoproject.com/en/dev/ref/templates/builtins/#date
MONTH_DAY_FORMAT = "F j"

# Default short formatting for date objects. See all available format strings here:
# https://docs.djangoproject.com/en/dev/ref/templates/builtins/#date
SHORT_DATE_FORMAT = "m/d/Y"

# Default short formatting for datetime objects.
# See all available format strings here:
# https://docs.djangoproject.com/en/dev/ref/templates/builtins/#date
SHORT_DATETIME_FORMAT = "m/d/Y P"

# Default formats to be used when parsing dates from input boxes, in order
# See all available format string here:
# https://docs.python.org/library/datetime.html#strftime-behavior
# * Note that these format strings are different from the ones to display dates
DATE_INPUT_FORMATS = [
    "%Y-%m-%d",  # '2006-10-25'
    "%m/%d/%Y",  # '10/25/2006'
    "%m/%d/%y",  # '10/25/06'
    "%b %d %Y",  # 'Oct 25 2006'
    "%b %d, %Y",  # 'Oct 25, 2006'
    "%d %b %Y",  # '25 Oct 2006'
    "%d %b, %Y",  # '25 Oct, 2006'
    "%B %d %Y",  # 'October 25 2006'
    "%B %d, %Y",  # 'October 25, 2006'
    "%d %B %Y",  # '25 October 2006'
    "%d %B, %Y",  # '25 October, 2006'
]

# Default formats to be used when parsing times from input boxes, in order
# See all available format string here:
# https://docs.python.org/library/datetime.html#strftime-behavior
# * Note that these format strings are different from the ones to display dates
TIME_INPUT_FORMATS = [
    "%H:%M:%S",  # '14:30:59'
    "%H:%M:%S.%f",  # '14:30:59.000200'
    "%H:%M",  # '14:30'
]

# Default formats to be used when parsing dates and times from input boxes,
# in order
# See all available format string here:
# https://docs.python.org/library/datetime.html#strftime-behavior
# * Note that these format strings are different from the ones to display dates
DATETIME_INPUT_FORMATS = [
    "%Y-%m-%d %H:%M:%S",  # '2006-10-25 14:30:59'
    "%Y-%m-%d %H:%M:%S.%f",  # '2006-10-25 14:30:59.000200'
    "%Y-%m-%d %H:%M",  # '2006-10-25 14:30'
    "%m/%d/%Y %H:%M:%S",  # '10/25/2006 14:30:59'
    "%m/%d/%Y %H:%M:%S.%f",  # '10/25/2006 14:30:59.000200'
    "%m/%d/%Y %H:%M",  # '10/25/2006 14:30'
    "%m/%d/%y %H:%M:%S",  # '10/25/06 14:30:59'
    "%m/%d/%y %H:%M:%S.%f",  # '10/25/06 14:30:59.000200'
    "%m/%d/%y %H:%M",  # '10/25/06 14:30'
]

# First day of week, to be used on calendars
# 0 means Sunday, 1 means Monday...
FIRST_DAY_OF_WEEK = 0

# Decimal separator symbol
DECIMAL_SEPARATOR = "."

# Boolean that sets whether to add thousand separator when formatting numbers
USE_THOUSAND_SEPARATOR = False

# Number of digits that will be together, when splitting them by
# THOUSAND_SEPARATOR. 0 means no grouping, 3 means splitting by thousands...
NUMBER_GROUPING = 0

# Thousand separator symbol
THOUSAND_SEPARATOR = ","

# The tablespaces to use for each model when not specified otherwise.
DEFAULT_TABLESPACE = ""
DEFAULT_INDEX_TABLESPACE = ""

# Default primary key field type.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Default X-Frame-Options header value
X_FRAME_OPTIONS = "DENY"

USE_X_FORWARDED_HOST = False
USE_X_FORWARDED_PORT = False

# The Python dotted path to the WSGI application that Django's internal server
# (runserver) will use. If `None`, the return value of
# 'django.core.wsgi.get_wsgi_application' is used, thus preserving the same
# behavior as previous versions of Django. Otherwise this should point to an
# actual WSGI application object.
WSGI_APPLICATION = "boxes.wsgi.application"

# If your Django app is behind a proxy that sets a header to specify secure
# connections, AND that proxy ensures that user-submitted headers with the
# same name are ignored (so that people can't spoof it), set this value to
# a tuple of (header_name, header_value). For any requests that come in with
# that header/value, request.is_secure() will return True.
# WARNING! Only set this if you fully understand what you're doing. Otherwise,
# you may be opening yourself up to a security risk.
SECURE_PROXY_SSL_HEADER = env('SECURE_PROXY_SSL_HEADER')

##############
# MIDDLEWARE #
##############

# List of middleware to use. Order is important; in the request phase, these
# middleware will be applied in the order given, and in the response
# phase the middleware will be applied in reverse order.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

###################
# BACKGROUND JOBS #
###################
BROKER_USER = env("CELERY_BROKER_USER")
BROKER_PASSWORD = env("CELERY_BROKER_PASSWORD")
BROKER_VHOST = env("CELERY_BROKER_VHOST")
BROKER_HOST = env("CELERY_BROKER_HOST")
CELERY_BROKER_URL = f'amqp://{BROKER_USER}:{BROKER_PASSWORD}@{BROKER_HOST}/{BROKER_VHOST}'
CELERY_RESULT_BACKEND = "rpc://"
CELERY_BEAT_SCHEDULE = {
    "send_emails": {
        "task": "boxes.tasks.emails.send_emails",
        "schedule": crontab(minute="*/10"),
    },
    "regenerate_report_data": {
        "task": "boxes.tasks.maintenance.regenerate_report_data",
        "schedule": crontab(minute="*/30"),
    },
    "age_picklists": {
        "task": "boxes.tasks.maintenance.age_picklists",
        "schedule": crontab(hour=3, minute=0),
    },
    "age_charges": {
        "task": "boxes.tasks.charges.age_charges",
        "schedule": crontab(minute=1),
    },
    "total_accounts": {
        "task": "boxes.tasks.maintenance.total_accounts",
        "schedule": crontab(minute=2),
    },
}

##########
# STRIPE #
##########
STRIPE_API_KEY = env("STRIPE_API_KEY")

############
# SESSIONS #
############

# Cache to store session data if using the cache session backend.
SESSION_CACHE_ALIAS = "default"
# Cookie name. This can be whatever you want.
SESSION_COOKIE_NAME = "sessionid"
# Age of cookie, in seconds (default: 2 weeks).
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7 * 2
# A string like "example.com", or None for standard domain cookie.
SESSION_COOKIE_DOMAIN = None
# Whether the session cookie should be secure (https:// only).
SESSION_COOKIE_SECURE = env('SESSION_COOKIE_SECURE')
# The path of the session cookie.
SESSION_COOKIE_PATH = "/"
# Whether to use the HttpOnly flag.
SESSION_COOKIE_HTTPONLY = True
# Whether to set the flag restricting cookie leaks on cross-site requests.
# This can be 'Lax', 'Strict', 'None', or False to disable the flag.
SESSION_COOKIE_SAMESITE = "Lax"
# Whether to save the session data on every request.
SESSION_SAVE_EVERY_REQUEST = False
# Whether a user's session cookie expires when the web browser is closed.
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
# The module to store session data
SESSION_ENGINE = "django.contrib.sessions.backends.db"
# Directory to store session files if using the file session module. If None,
# the backend will use a sensible default.
SESSION_FILE_PATH = None
# class to serialize session data
SESSION_SERIALIZER = "django.contrib.sessions.serializers.JSONSerializer"

#########
# CACHE #
#########

# The cache backends to use.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": "/var/tmp/django_cache",
    }
}
CACHE_MIDDLEWARE_KEY_PREFIX = ""
CACHE_MIDDLEWARE_SECONDS = 600
CACHE_MIDDLEWARE_ALIAS = "default"

##################
# AUTHENTICATION #
##################

AUTH_USER_MODEL = "boxes.CustomUser"

AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

ROOT_URLCONF = "boxes.urls"

LOGIN_URL = "/login/"

LOGIN_REDIRECT_URL = "/accounts/profile/"

LOGOUT_REDIRECT_URL = None

# The number of seconds a password reset link is valid for (default: 3 days).
PASSWORD_RESET_TIMEOUT = 60 * 60 * 24 * 3

# the first hasher in this list is the preferred algorithm.  any
# password using different algorithms will be converted automatically
# upon login
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = []

###########
# SIGNING #
###########

SIGNING_BACKEND = "django.core.signing.TimestampSigner"

########
# CSRF #
########

# Dotted path to callable to be used as view when a request is
# rejected by the CSRF middleware.
CSRF_FAILURE_VIEW = "django.views.csrf.csrf_failure"

# Settings for CSRF cookie.
CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_AGE = 60 * 60 * 24 * 7 * 52
CSRF_COOKIE_DOMAIN = None
CSRF_COOKIE_PATH = "/"
CSRF_COOKIE_SECURE = env('CSRF_COOKIE_SECURE')
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"
CSRF_TRUSTED_ORIGINS = []
CSRF_USE_SESSIONS = False

############
# MESSAGES #
############

# Class to use as messages backend
MESSAGE_STORAGE = "django.contrib.messages.storage.fallback.FallbackStorage"

# Default values of MESSAGE_LEVEL and MESSAGE_TAGS are defined within
# django.contrib.messages to avoid imports in this settings file.

###########
# LOGGING #
###########

# The callable to use to configure logging
LOGGING_CONFIG = "logging.config.dictConfig"

# Custom logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
           'level': env('LOGGING_LEVEL'),
           'class': 'logging.FileHandler',
           'filename': env('LOGGING_FILE'),
           "formatter": "app",
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': env('LOGGING_LEVEL'),  # Set the level as per your preference (DEBUG, INFO, etc.)
            'handlers': ['file'],
        },
    },
    "formatters": {
        "app": {
            "format": (
                u"%(asctime)s [%(levelname)-8s] "
                "(%(module)s.%(funcName)s) %(message)s"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
}

# Default exception reporter class used in case none has been
# specifically assigned to the HttpRequest instance.
DEFAULT_EXCEPTION_REPORTER = "django.views.debug.ExceptionReporter"

# Default exception reporter filter class used in case none has been
# specifically assigned to the HttpRequest instance.
DEFAULT_EXCEPTION_REPORTER_FILTER = "django.views.debug.SafeExceptionReporterFilter"

###########
# TESTING #
###########

# The name of the class to use to run the test suite
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Apps that don't need to be serialized at test database creation time
# (only apps with migrations are to start with)
TEST_NON_SERIALIZED_APPS = []

############
# FIXTURES #
############

# The list of directories to search for fixtures
FIXTURE_DIRS = []

###############
# STATICFILES #
###############

# A list of locations of additional static files
STATICFILES_DIRS = []

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
]

##############
# MIGRATIONS #
##############

# Migration module overrides for apps, by app label.
MIGRATION_MODULES = {}

#################
# SYSTEM CHECKS #
#################

# List of all issues generated by system checks that should be silenced. Light
# issues like warnings, infos or debugs will not generate a message. Silencing
# serious issues like errors and criticals does not result in hiding the
# message, but Django will not stop you from e.g. running server.
SILENCED_SYSTEM_CHECKS = []

#######################
# SECURITY MIDDLEWARE #
#######################
SECURE_CONTENT_TYPE_NOSNIFF = env('SECURE_CONTENT_TYPE_NOSNIFF')
SECURE_CROSS_ORIGIN_OPENER_POLICY = env('SECURE_CROSS_ORIGIN_OPENER_POLICY')
SECURE_HSTS_INCLUDE_SUBDOMAINS = env('SECURE_HSTS_INCLUDE_SUBDOMAINS')
SECURE_HSTS_PRELOAD = env('SECURE_HSTS_PRELOAD')
SECURE_HSTS_SECONDS = env('SECURE_HSTS_SECONDS')
SECURE_REDIRECT_EXEMPT = env('SECURE_REDIRECT_EXEMPT')
SECURE_REFERRER_POLICY = env('SECURE_REFERRER_POLICY')
SECURE_SSL_HOST = env('SECURE_SSL_HOST')
SECURE_SSL_REDIRECT = env('SECURE_SSL_REDIRECT')
