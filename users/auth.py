from ninja.security import HttpBearer
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()


class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            return User.objects.get(id=user_id)
        except Exception:
            return None


class JWTAuthQueryParam(JWTAuth):
    """
    Variante de JWTAuth qui accepte le token en query param (?token=...)
    en plus du header Authorization: Bearer.

    Nécessaire pour les endpoints déclenchés via page.launch_url() côté
    Flet : le navigateur fait une navigation GET classique, impossible
    d'y injecter un header. Utiliser UNIQUEMENT sur des endpoints de
    téléchargement (GET, effet de lecture seule) — jamais sur des routes
    qui modifient des données, pour ne pas traîner de token sensible
    dans les logs serveur / historique navigateur plus que nécessaire.
    """
    def __call__(self, request):
        token = request.GET.get("token")
        if token:
            return self.authenticate(request, token)
        return super().__call__(request)