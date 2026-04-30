from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'        # ← chemin Python complet pour import
    label = 'users'            # ← app_label utilisé par Django (AUTH_USER_MODEL, FK...)


