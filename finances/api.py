# finances/api.py
from ninja import Router
from finances.models import Paiement
from finances.schemas import PaiementCreateSchema, PaiementResponseSchema
from reservations.models import Reservation
from users.auth import JWTAuth
import uuid
from typing import List, Dict, Any
import logging

# ─── AJOUT DES IMPORTS POUR DJANGO-Q2 ───
from django_q.tasks import async_task
from finances.tasks import send_invoice_email_task

logger = logging.getLogger(__name__)

router = Router()
auth = JWTAuth()

def _is_admin(user) -> bool:
    return user.role in ["ADMIN", "SECRETARIAT"]

def _generate_reference() -> str:
    return f"PAY-{uuid.uuid4().hex[:8].upper()}"

# Note: La fonction synchrone _send_invoice_email a été supprimée d'ici 
# car elle est maintenant dans finances/tasks.py

@router.post("/", auth=auth)
def create_new_paiement(request, data: PaiementCreateSchema):
    user = request.auth
    try:
        reservation = Reservation.objects.get(id=data.reservation_id)
    except Reservation.DoesNotExist:
        return {"success": False, "message": "Réservation introuvable"}

    if reservation.client != user and not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}

    reference = _generate_reference()
    paiement = Paiement.objects.create(
        reservation=reservation,
        client=user,
        montant=data.montant,
        canal=data.canal,
        reference=reference
    )
    return {
        "success": True,
        "message": "Paiement enregistré",
        "reference": paiement.reference,
        "statut": paiement.statut
    }

@router.get("/mes-paiements", auth=auth, response=List[Dict[str, Any]])
def get_my_paiements(request):
    user = request.auth
    return list(Paiement.objects.filter(client=user).values())

@router.get("/admin", auth=auth, response=List[Dict[str, Any]])
def get_all_paiements_admin(request):
    user = request.auth
    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}
    sort_by = request.GET.get('sort', '-created_at')
    allowed_sort_fields = ['created_at', '-created_at', 'montant', '-montant', 'statut', '-statut']
    if sort_by not in allowed_sort_fields:
        sort_by = '-created_at'
    return list(Paiement.objects.all().order_by(sort_by).values())

@router.post("/validate/{paiement_id}", auth=auth)
def validate_paiement_request(request, paiement_id: int):
    """Valide un paiement et déclenche l'envoi asynchrone du reçu."""
    user = request.auth
    print(f"🔵 Validation du paiement {paiement_id} par {user.email}")
    
    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}

    try:
        paiement = Paiement.objects.get(id=paiement_id)
    except Paiement.DoesNotExist:
        return {"success": False, "message": "Paiement introuvable"}

    paiement.statut = "VALIDE"
    paiement.save()
    print(f"✅ Paiement {paiement.reference} validé en base")

    # ─── DISPATCH DE LA TÂCHE ASYNCHRONE ICI ───
    try:
        # async_task prend le chemin de la fonction en chaîne de caractères, 
        # suivi des arguments nécessaires (ici l'ID du paiement)
        async_task('finances.tasks.send_invoice_email_task', paiement.id)
        print("🚀 Tâche d'envoi d'email enregistrée en arrière-plan avec succès.")
    except Exception as e:
        print(f"🔴 Impossible de planifier la tâche en arrière-plan : {e}")

    return {"success": True, "message": "Paiement validé. La facture est en cours d'envoi."}

@router.post("/reject/{paiement_id}", auth=auth)
def reject_paiement_request(request, paiement_id: int):
    user = request.auth
    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}
    try:
        paiement = Paiement.objects.get(id=paiement_id)
    except Paiement.DoesNotExist:
        return {"success": False, "message": "Paiement introuvable"}
    paiement.statut = "REFUSE"
    paiement.save()
    return {"success": True, "message": "Paiement refusé"}

@router.get("/historique/{reservation_id}", auth=auth)
def get_paiement_history(request, reservation_id: int):
    user = request.auth
    try:
        reservation = Reservation.objects.get(id=reservation_id)
    except Reservation.DoesNotExist:
        return {"success": False, "message": "Réservation introuvable"}
    if reservation.client != user and not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}
    paiements = Paiement.objects.filter(reservation_id=reservation_id).values()
    total_paid = sum(p["montant"] for p in paiements)
    return {
        "paiements": list(paiements),
        "total_paye": float(total_paid)
    }