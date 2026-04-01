from django.apps import AppConfig


class CrmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm'
    
    def ready(self):
        """Import signal handlers when app is ready"""
        import crm.cache_utils  # noqa: F401

        # SQLite: WAL + busy timeout reduce "database is locked" / 500s under concurrent requests.
        from django.db.backends.signals import connection_created

        def _sqlite_concurrency_pragmas(sender, connection, **kwargs):
            if connection.vendor != 'sqlite':
                return
            with connection.cursor() as cursor:
                cursor.execute('PRAGMA journal_mode=WAL;')
                cursor.execute('PRAGMA busy_timeout=5000;')

        connection_created.connect(_sqlite_concurrency_pragmas)