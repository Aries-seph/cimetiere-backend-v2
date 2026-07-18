# finances/api.py
from ninja import Router
from finances.models import Paiement
from finances.schemas import PaiementCreateSchema, PaiementResponseSchema
from reservations.models import Reservation
from users.auth import JWTAuth
import uuid
from django.core.mail import EmailMessage
from finances.pdf import generate_invoice_pdf
from typing import List, Dict, Any
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

router = Router()
auth = JWTAuth()


def _is_admin(user) -> bool:
    """Vérifie si l'utilisateur a un rôle administratif."""
    return user.role in ["ADMIN", "SECRETARIAT"]


def _generate_reference() -> str:
    """Génère une référence unique pour un paiement."""
    return f"PAY-{uuid.uuid4().hex[:8].upper()}"


def _send_invoice_email(paiement: Paiement):
    """Envoie la facture par email avec gestion d'erreurs."""
    try:
        print(f"🔵 Envoi de la facture pour le paiement {paiement.reference}")
        print(f"🔵 Destinataire: {paiement.client.email}")
        
        # Générer le PDF
        pdf_buffer = generate_invoice_pdf(paiement)
        print(f"🔵 PDF généré avec succès")
        
        # Créer l'email
        email = EmailMessage(
            subject='Votre facture de paiement',
            body=f'Bonjour {paiement.client.username},\n\nVeuillez trouver ci-joint votre facture pour le paiement {paiement.reference}.\n\nMerci.',
            from_email='jeremykounkou@icloud.com',
            to=[paiement.client.email],
            reply_to=['jeremykounkou@icloud.com'],  # ✅ AJOUTÉ
        )
        
        # Attacher le PDF
        email.attach(
            f'facture_{paiement.reference}.pdf',
            pdf_buffer.read(),
            'application/pdf'
        )
        
        # Envoyer l'email
        email.send()
        print(f"✅ Email envoyé avec succès à {paiement.client.email}")
        
    except Exception as e:
        print(f"🔴 Erreur lors de l'envoi de l'email: {e}")
        # Ne pas lever d'exception pour ne pas bloquer la validation du paiement


@router.post("/", auth=auth)
def create_new_paiement(request, data: PaiementCreateSchema):
    """Crée un nouveau paiement."""
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
    """Récupère les paiements de l'utilisateur connecté."""
    user = request.auth
    return list(Paiement.objects.filter(client=user).values())


@router.get("/admin", auth=auth, response=List[Dict[str, Any]])
def get_all_paiements_admin(request):
    """Récupère tous les paiements (admin uniquement)."""
    user = request.auth
    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}
    
    # Récupérer le paramètre de tri
    sort_by = request.GET.get('sort', '-created_at')
    
    # Validation des champs de tri autorisés
    allowed_sort_fields = ['created_at', '-created_at', 'montant', '-montant', 'statut', '-statut']
    
    if sort_by not in allowed_sort_fields:
        sort_by = '-created_at'
    
    return list(Paiement.objects.all().order_by(sort_by).values())


@router.post("/validate/{paiement_id}", auth=auth)
def validate_paiement_request(request, paiement_id: int):
    """Valide un paiement."""
    user = request.auth
    print(f"🔵 Validation du paiement {paiement_id} par {user.email}")
    
    if not _is_admin(user):
        print("🔴 Accès refusé - rôle insuffisant")
        return {"success": False, "message": "Accès refusé"}

    try:
        paiement = Paiement.objects.get(id=paiement_id)
        print(f"🔵 Paiement trouvé: {paiement.reference}")
    except Paiement.DoesNotExist:
        print(f"🔴 Paiement {paiement_id} introuvable")
        return {"success": False, "message": "Paiement introuvable"}

    paiement.statut = "VALIDE"
    paiement.save()
    print(f"✅ Paiement {paiement.reference} validé en base")

    # Envoyer la facture par email
    try:
        _send_invoice_email(paiement)
        print(f"✅ Email envoyé à {paiement.client.email}")
    except Exception as e:
        print(f"🔴 Erreur lors de l'envoi de l'email: {e}")
        # On continue même si l'email échoue

    return {"success": True, "message": "Paiement validé et facture envoyée"}


@router.post("/reject/{paiement_id}", auth=auth)
def reject_paiement_request(request, paiement_id: int):
    """Refuse un paiement."""
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
    """Récupère l'historique des paiements d'une réservation."""
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