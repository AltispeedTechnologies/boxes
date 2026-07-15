# Settings (generated)

Values from the loaded Django settings module. Secrets are redacted.

| Setting | Value |
|---------|-------|
| `ABSOLUTE_URL_OVERRIDES` | `{}` |
| `ADMINS` | `[]` |
| `ALLOWED_HOSTS` | `['boxes.tsimonq2.internal']` |
| `APPEND_SLASH` | `True` |
| `AUTHENTICATION_BACKENDS` | `['django.contrib.auth.backends.ModelBackend']` |
| `AUTH_PASSWORD_VALIDATORS` | `**[redacted]**` |
| `AUTH_USER_MODEL` | `'boxes.CustomUser'` |
| `BASE_DIR` | `'/var/www/mikes-boxes'` |
| `BROKER_HOST` | `'localhost'` |
| `BROKER_PASSWORD` | `**[redacted]**` |
| `BROKER_USER` | `'boxes'` |
| `BROKER_VHOST` | `'/'` |
| `CACHES` | `{'default': {'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache', 'LOCATION': '/var/tmp/django_cache'}}` |
| `CACHE_MIDDLEWARE_ALIAS` | `'default'` |
| `CACHE_MIDDLEWARE_KEY_PREFIX` | `''` |
| `CACHE_MIDDLEWARE_SECONDS` | `600` |
| `CELERY_BEAT_SCHEDULE` | `{'send_emails': {'task': 'boxes.tasks.emails.send_emails', 'schedule': <crontab: */10 * * * * (m/h/dM/MY/d)>}, 'regen...` |
| `CELERY_BROKER_URL` | `'amqp://boxes:changem3@localhost//'` |
| `CELERY_RESULT_BACKEND` | `'rpc://'` |
| `CSRF_COOKIE_AGE` | `31449600` |
| `CSRF_COOKIE_DOMAIN` | `None` |
| `CSRF_COOKIE_HTTPONLY` | `False` |
| `CSRF_COOKIE_NAME` | `'csrftoken'` |
| `CSRF_COOKIE_PATH` | `'/'` |
| `CSRF_COOKIE_SAMESITE` | `'Lax'` |
| `CSRF_COOKIE_SECURE` | `False` |
| `CSRF_FAILURE_VIEW` | `'django.views.csrf.csrf_failure'` |
| `CSRF_HEADER_NAME` | `'HTTP_X_CSRFTOKEN'` |
| `CSRF_TRUSTED_ORIGINS` | `[]` |
| `CSRF_USE_SESSIONS` | `False` |
| `DATABASES` | `{'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'boxes', 'USER': 'boxes', 'PASSWORD': 'changem3', 'HO...` |
| `DATABASE_ROUTERS` | `[]` |
| `DATA_UPLOAD_MAX_MEMORY_SIZE` | `2621440` |
| `DATA_UPLOAD_MAX_NUMBER_FIELDS` | `1000` |
| `DATA_UPLOAD_MAX_NUMBER_FILES` | `100` |
| `DATETIME_FORMAT` | `'N j, Y, P'` |
| `DATETIME_INPUT_FORMATS` | `['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S.%f', '%m/%d/%...` |
| `DATE_FORMAT` | `'N j, Y'` |
| `DATE_INPUT_FORMATS` | `['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%b %d %Y', '%b %d, %Y', '%d %b %Y', '%d %b, %Y', '%B %d %Y', '%B %d, %Y', '%d %...` |
| `DEBUG` | `True` |
| `DEBUG_PROPAGATE_EXCEPTIONS` | `False` |
| `DECIMAL_SEPARATOR` | `'.'` |
| `DEFAULT_AUTO_FIELD` | `'django.db.models.BigAutoField'` |
| `DEFAULT_CHARSET` | `'utf-8'` |
| `DEFAULT_EXCEPTION_REPORTER` | `'django.views.debug.ExceptionReporter'` |
| `DEFAULT_EXCEPTION_REPORTER_FILTER` | `'django.views.debug.SafeExceptionReporterFilter'` |
| `DEFAULT_FROM_EMAIL` | `'webmaster@localhost'` |
| `DEFAULT_INDEX_TABLESPACE` | `''` |
| `DEFAULT_TABLESPACE` | `''` |
| `DISALLOWED_USER_AGENTS` | `[]` |
| `EMAIL_BACKEND` | `'django.core.mail.backends.smtp.EmailBackend'` |
| `EMAIL_HOST` | `'localhost'` |
| `EMAIL_HOST_PASSWORD` | `**[redacted]**` |
| `EMAIL_HOST_USER` | `''` |
| `EMAIL_PORT` | `25` |
| `EMAIL_SSL_CERTFILE` | `None` |
| `EMAIL_SSL_KEYFILE` | `None` |
| `EMAIL_SUBJECT_PREFIX` | `'[Django] '` |
| `EMAIL_TIMEOUT` | `None` |
| `EMAIL_USE_LOCALTIME` | `True` |
| `EMAIL_USE_SSL` | `False` |
| `EMAIL_USE_TLS` | `False` |
| `FILE_UPLOAD_DIRECTORY_PERMISSIONS` | `None` |
| `FILE_UPLOAD_HANDLERS` | `['django.core.files.uploadhandler.MemoryFileUploadHandler', 'django.core.files.uploadhandler.TemporaryFileUploadHandl...` |
| `FILE_UPLOAD_MAX_MEMORY_SIZE` | `2621440` |
| `FILE_UPLOAD_PERMISSIONS` | `420` |
| `FILE_UPLOAD_TEMP_DIR` | `None` |
| `FIRST_DAY_OF_WEEK` | `0` |
| `FIXTURE_DIRS` | `[]` |
| `FORCE_SCRIPT_NAME` | `None` |
| `FORMAT_MODULE_PATH` | `None` |
| `FORMS_URLFIELD_ASSUME_HTTPS` | `False` |
| `FORM_RENDERER` | `'django.forms.renderers.DjangoTemplates'` |
| `IGNORABLE_404_URLS` | `[]` |
| `INSTALLED_APPS` | `['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.con...` |
| `INTERNAL_IPS` | `[]` |
| `LANGUAGES` | `[('en', 'English'), ('en-au', 'Australian English'), ('en-gb', 'British English')]` |
| `LANGUAGES_BIDI` | `[]` |
| `LANGUAGE_CODE` | `'en-us'` |
| `LANGUAGE_COOKIE_AGE` | `None` |
| `LANGUAGE_COOKIE_DOMAIN` | `None` |
| `LANGUAGE_COOKIE_HTTPONLY` | `False` |
| `LANGUAGE_COOKIE_NAME` | `'django_language'` |
| `LANGUAGE_COOKIE_PATH` | `'/'` |
| `LANGUAGE_COOKIE_SAMESITE` | `None` |
| `LANGUAGE_COOKIE_SECURE` | `False` |
| `LOCALE_PATHS` | `[]` |
| `LOGGING` | `{'version': 1, 'disable_existing_loggers': False, 'handlers': {'file': {'level': 'DEBUG', 'class': 'logging.FileHandl...` |
| `LOGGING_CONFIG` | `'logging.config.dictConfig'` |
| `LOGIN_REDIRECT_URL` | `'/profile/'` |
| `LOGIN_URL` | `'/login/'` |
| `LOGOUT_REDIRECT_URL` | `None` |
| `MANAGERS` | `[]` |
| `MEDIA_ROOT` | `'/var/www/mikes-boxes/public/media'` |
| `MEDIA_URL` | `'/media/'` |
| `MESSAGE_STORAGE` | `'django.contrib.messages.storage.fallback.FallbackStorage'` |
| `MIDDLEWARE` | `['django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.mid...` |
| `MIGRATION_MODULES` | `{}` |
| `MONTH_DAY_FORMAT` | `'F j'` |
| `NUMBER_GROUPING` | `0` |
| `PASSWORD_HASHERS` | `**[redacted]**` |
| `PASSWORD_RESET_TIMEOUT` | `**[redacted]**` |
| `PREPEND_WWW` | `False` |
| `ROOT_URLCONF` | `'boxes.urls'` |
| `SECRET_KEY` | `**[redacted]**` |
| `SECRET_KEY_FALLBACKS` | `**[redacted]**` |
| `SECURE_CONTENT_TYPE_NOSNIFF` | `True` |
| `SECURE_CROSS_ORIGIN_OPENER_POLICY` | `'None'` |
| `SECURE_CSP` | `{}` |
| `SECURE_CSP_REPORT_ONLY` | `{}` |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | `False` |
| `SECURE_HSTS_PRELOAD` | `False` |
| `SECURE_HSTS_SECONDS` | `0` |
| `SECURE_PROXY_SSL_HEADER` | `None` |
| `SECURE_REDIRECT_EXEMPT` | `[]` |
| `SECURE_REFERRER_POLICY` | `'no-referrer-when-downgrade'` |
| `SECURE_ROOT` | `'/var/www/mikes-boxes/.secure_storage'` |
| `SECURE_SSL_HOST` | `None` |
| `SECURE_SSL_REDIRECT` | `False` |
| `SERVER_EMAIL` | `'root@localhost'` |
| `SESSION_CACHE_ALIAS` | `'default'` |
| `SESSION_COOKIE_AGE` | `1209600` |
| `SESSION_COOKIE_DOMAIN` | `None` |
| `SESSION_COOKIE_HTTPONLY` | `True` |
| `SESSION_COOKIE_NAME` | `'sessionid'` |
| `SESSION_COOKIE_PATH` | `'/'` |
| `SESSION_COOKIE_SAMESITE` | `'Lax'` |
| `SESSION_COOKIE_SECURE` | `False` |
| `SESSION_ENGINE` | `'django.contrib.sessions.backends.db'` |
| `SESSION_EXPIRE_AT_BROWSER_CLOSE` | `False` |
| `SESSION_FILE_PATH` | `None` |
| `SESSION_SAVE_EVERY_REQUEST` | `False` |
| `SESSION_SERIALIZER` | `'django.contrib.sessions.serializers.JSONSerializer'` |
| `SETTINGS_MODULE` | `'boxes.settings'` |
| `SHORT_DATETIME_FORMAT` | `'m/d/Y P'` |
| `SHORT_DATE_FORMAT` | `'m/d/Y'` |
| `SIGNED_COOKIE_LEGACY_SALT_FALLBACK` | `True` |
| `SIGNING_BACKEND` | `'django.core.signing.TimestampSigner'` |
| `SILENCED_SYSTEM_CHECKS` | `[]` |
| `STATICFILES_DIRS` | `[]` |
| `STATICFILES_FINDERS` | `['django.contrib.staticfiles.finders.FileSystemFinder', 'django.contrib.staticfiles.finders.AppDirectoriesFinder']` |
| `STATIC_ROOT` | `'/var/www/mikes-boxes/public/static'` |
| `STATIC_URL` | `'/static/'` |
| `STORAGES` | `{'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'}, 'staticfiles': {'BACKEND': 'django.contrib.st...` |
| `STRIPE_API_KEY` | `**[redacted]**` |
| `STRIPE_ENDPOINT_SECRET` | `**[redacted]**` |
| `TASKS` | `{'default': {'BACKEND': 'django.tasks.backends.immediate.ImmediateBackend'}}` |
| `TEMPLATES` | `[{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': ['/var/www/mikes-boxes/boxes/templates'], 'AP...` |
| `TEST_NON_SERIALIZED_APPS` | `[]` |
| `TEST_RUNNER` | `'django.test.runner.DiscoverRunner'` |
| `THOUSAND_SEPARATOR` | `','` |
| `TIME_FORMAT` | `'P'` |
| `TIME_INPUT_FORMATS` | `['%H:%M:%S', '%H:%M:%S.%f', '%H:%M']` |
| `TIME_ZONE` | `'America/Chicago'` |
| `URLIZE_ASSUME_HTTPS` | `False` |
| `USE_I18N` | `True` |
| `USE_THOUSAND_SEPARATOR` | `False` |
| `USE_TZ` | `True` |
| `USE_X_FORWARDED_HOST` | `False` |
| `USE_X_FORWARDED_PORT` | `False` |
| `WSGI_APPLICATION` | `'boxes.wsgi.application'` |
| `X_FRAME_OPTIONS` | `'DENY'` |
| `YEAR_MONTH_FORMAT` | `'F Y'` |

Environment loading: `environ.Env.read_env(ENV_PATH or /etc/boxes.env)`. Business settings stored in PostgreSQL are documented in `docs/DATABASE_SETTINGS.md`.
