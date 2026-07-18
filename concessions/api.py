# concessions/api.py
from ninja import Router
from concessions.models import Concession
from concessions.schemas import ConcessionCreateSchema, ConcessionResponseSchema
from caveaux.models import Caveau
from users.auth import JWTAuth
from django.contrib.auth import get_user_model
from django.utils import timezone
from typing import List, Dict, Any

router = Router()
auth = JWTAuth()
User = get_user_model()


def _is_admin(user) -> bool:
    """Vérifie si l'utilisateur a un rôle administratif."""
    return user.role in ["ADMIN", "SECRETARIAT"]


@router.post("/", auth=auth)
def create_new_concession(request, data: ConcessionCreateSchema):
    """Crée une nouvelle concession."""
    user = request.auth
    
    print("🔵 ===== CREATE CONCESSION =====")
    print(f"🔵 Utilisateur: {user.email if user else 'inconnu'}")
    print(f"🔵 Rôle utilisateur: {user.role if user else 'inconnu'}")
    print(f"🔵 Données reçues: client_id={data.client_id}, caveau_id={data.caveau_id}, type={data.type_concession}, date_debut={data.date_debut}, date_fin={data.date_fin}")

    if not _is_admin(user):
        print("🔴 Accès refusé - rôle insuffisant")
        return {"success": False, "message": "Accès refusé"}

    try:
        client = User.objects.get(id=data.client_id)
        print(f"🔵 Client trouvé: {client.email}")
    except User.DoesNotExist:
        print(f"🔴 Client introuvable: ID {data.client_id}")
        return {"success": False, "message": "Client introuvable"}

    try:
        caveau = Caveau.objects.get(id=data.caveau_id)
        print(f"🔵 Caveau trouvé: {caveau.reference}")
    except Caveau.DoesNotExist:
        print(f"🔴 Caveau introuvable: ID {data.caveau_id}")
        return {"success": False, "message": "Caveau introuvable"}

    if data.type_concession == "TEMPORAIRE" and not data.date_fin:
        print("🔴 Erreur: Concession temporaire sans date de fin")
        return {"success": False, "message": "Une concession temporaire nécessite une date de fin"}

    try:
        concession = Concession.objects.create(
            client=client,
            caveau=caveau,
            type_concession=data.type_concession,
            date_debut=data.date_debut,
            date_fin=data.date_fin
        )
        print(f"✅ Concession créée avec l'ID {concession.id}")
        print("🔵 ===== FIN CREATE CONCESSION =====")
        return {"success": True, "id": concession.id, "message": "Concession créée"}
    except Exception as e:
        print(f"🔴 Erreur lors de la création en base: {e}")
        print("🔵 ===== FIN CREATE CONCESSION (ERREUR) =====")
        return {"success": False, "message": f"Erreur base de données: {str(e)}"}


@router.get("/", auth=auth, response=List[Dict[str, Any]])
def get_concessions_list(request):
    """Récupère la liste des concessions."""
    user = request.auth
    print(f"🔵 GET concessions par {user.email if user else 'inconnu'}")

    if _is_admin(user):
        concessions = Concession.objects.all().values()
    else:
        concessions = Concession.objects.filter(client=user).values()

    return list(concessions)


@router.get("/{concession_id}", auth=auth)
def get_concession_detail(request, concession_id: int):
    """Récupère les détails d'une concession."""
    user = request.auth
    print(f"🔵 GET concession {concession_id} par {user.email if user else 'inconnu'}")

    try:
        if _is_admin(user):
            concession = Concession.objects.get(id=concession_id)
        else:
            concession = Concession.objects.get(id=concession_id, client=user)
    except Concession.DoesNotExist:
        print(f"🔴 Concession {concession_id} introuvable")
        return {"success": False, "message": "Concession introuvable"}

    return {
        "id": concession.id,
        "client": concession.client.username,
        "caveau": concession.caveau.reference,
        "type_concession": concession.type_concession,
        "statut": concession.statut,
        "date_debut": str(concession.date_debut),
        "date_fin": str(concession.date_fin) if concession.date_fin else None,
    }


@router.post("/renouveler/{concession_id}", auth=auth)
def renew_concession(request, concession_id: int, nouvelle_date_fin: str):
    """Renouvelle une concession temporaire."""
    user = request.auth
    print(f"🔵 RENOUVELLEMENT concession {concession_id} par {user.email if user else 'inconnu'}")

    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}

    try:
        concession = Concession.objects.get(id=concession_id)
    except Concession.DoesNotExist:
        return {"success": False, "message": "Concession introuvable"}

    if concession.type_concession == "PERPETUELLE":
        return {"success": False, "message": "Une concession perpétuelle ne peut pas être renouvelée"}

    concession.date_fin = nouvelle_date_fin
    concession.statut = "ACTIVE"
    concession.save()
    
    print(f"✅ Concession {concession_id} renouvelée jusqu'au {nouvelle_date_fin}")

    return {"success": True, "message": "Concession renouvelée"}


@router.post("/resilier/{concession_id}", auth=auth)
def terminate_concession(request, concession_id: int):
    """Résilie une concession."""
    user = request.auth
    print(f"🔵 RÉSILIATION concession {concession_id} par {user.email if user else 'inconnu'}")

    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}

    try:
        concession = Concession.objects.get(id=concession_id)
    except Concession.DoesNotExist:
        return {"success": False, "message": "Concession introuvable"}

    concession.statut = "RESILIEE"
    concession.save()

    caveau = concession.caveau
    caveau.statut = "DISPONIBLE"
    caveau.save()
    
    print(f"✅ Concession {concession_id} résiliée")

    return {"success": True, "message": "Concession résiliée"}


@router.get("/expirees/liste", auth=auth, response=List[Dict[str, Any]])
def get_expired_concessions(request):
    """Récupère la liste des concessions expirées."""
    user = request.auth
    print(f"🔵 GET concessions expirées par {user.email if user else 'inconnu'}")

    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}

    today = timezone.now().date()
    expired = Concession.objects.filter(
        date_fin__lt=today,
        statut="ACTIVE"
    ).values()

    return list(expired)