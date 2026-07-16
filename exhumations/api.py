# exhumations/api.py
from ninja import Router
from exhumations.models import Exhumation
from exhumations.schemas import ExhumationCreateSchema, ExhumationUpdateSchema
from caveaux.models import Caveau
from users.auth import JWTAuth
from django.core.mail import send_mail, EmailMessage
from exhumations.pdf import generate_authorization_pdf
import io

router = Router()
auth = JWTAuth()


def _is_admin(user) -> bool:
    """Vérifie si l'utilisateur a un rôle administratif."""
    return user.role in ["ADMIN", "AGENT", "SECRETARIAT"]


def _notify_admins(subject: str, message: str):
    """Envoie une notification aux administrateurs."""
    send_mail(
        subject=subject,
        message=message,
        from_email='jeremykounkou@icloud.com',
        recipient_list=['jeremykounkou@icloud.com'],
    )


def _send_authorization_email(exhumation: Exhumation):
    """Envoie l'autorisation d'exhumation par email."""
    pdf_buffer = generate_authorization_pdf(exhumation)
    
    email = EmailMessage(
        subject="Autorisation d'exhumation",
        body=f"Bonjour {exhumation.demandeur.username},\n\nVotre demande d'exhumation a été approuvée.\nVeuillez trouver ci-joint l'autorisation officielle.",
        from_email='jeremykounkou@icloud.com',
        to=[exhumation.demandeur.email],
    )
    email.attach(
        f'autorisation_exhumation_{exhumation.id}.pdf',
        pdf_buffer.read(),
        'application/pdf'
    )
    email.send()


@router.post("/", auth=auth)
def create_new_exhumation(request, data: ExhumationCreateSchema):
    """Crée une nouvelle demande d'exhumation."""
    user = request.auth

    try:
        caveau = Caveau.objects.get(id=data.caveau_id)
    except Caveau.DoesNotExist:
        return {"success": False, "message": "Caveau introuvable"}

    exhumation = Exhumation.objects.create(
        demandeur=user,
        caveau=caveau,
        nom_defunt=data.nom_defunt,
        motif=data.motif,
        date_exhumation=data.date_exhumation
    )

    _notify_admins(
        subject="Nouvelle demande d'exhumation",
        message=f"Une demande d'exhumation a été soumise par {user.email} pour le caveau {caveau.reference}."
    )

    return {"success": True, "id": exhumation.id, "message": "Demande d'exhumation créée"}


@router.get("/", auth=auth, response=list)
def get_exhumations_list(request):
    """Récupère la liste des exhumations."""
    user = request.auth

    if _is_admin(user):
        return list(Exhumation.objects.all().values())
    return list(Exhumation.objects.filter(demandeur=user).values())


@router.get("/{exhumation_id}", auth=auth)
def get_exhumation_detail(request, exhumation_id: int):
    """Récupère les détails d'une exhumation."""
    user = request.auth

    try:
        if _is_admin(user):
            exhumation = Exhumation.objects.get(id=exhumation_id)
        else:
            exhumation = Exhumation.objects.get(id=exhumation_id, demandeur=user)
    except Exhumation.DoesNotExist:
        return {"success": False, "message": "Exhumation introuvable"}

    return {
        "id": exhumation.id,
        "caveau": exhumation.caveau.reference,
        "nom_defunt": exhumation.nom_defunt,
        "motif": exhumation.motif,
        "statut": exhumation.statut,
        "date_demande": str(exhumation.date_demande),
        "date_exhumation": str(exhumation.date_exhumation) if exhumation.date_exhumation else None,
        "observations": exhumation.observations,
    }


@router.post("/approuver/{exhumation_id}", auth=auth)
def approve_exhumation(request, exhumation_id: int, data: ExhumationUpdateSchema):
    """Approuve une demande d'exhumation."""
    user = request.auth

    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}

    try:
        exhumation = Exhumation.objects.get(id=exhumation_id)
    except Exhumation.DoesNotExist:
        return {"success": False, "message": "Exhumation introuvable"}

    exhumation.statut = "APPROUVEE"
    exhumation.approuve_par = user
    exhumation.observations = data.observations or ""
    if data.date_exhumation:
        exhumation.date_exhumation = data.date_exhumation
    exhumation.save()

    _send_authorization_email(exhumation)

    return {"success": True, "message": "Exhumation approuvée et autorisation envoyée"}


@router.post("/refuser/{exhumation_id}", auth=auth)
def reject_exhumation(request, exhumation_id: int):
    """Refuse une demande d'exhumation."""
    user = request.auth

    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}

    try:
        exhumation = Exhumation.objects.get(id=exhumation_id)
    except Exhumation.DoesNotExist:
        return {"success": False, "message": "Exhumation introuvable"}

    exhumation.statut = "REFUSEE"
    exhumation.save()

    send_mail(
        subject="Demande d'exhumation refusée",
        message=f"Bonjour {exhumation.demandeur.username},\n\nVotre demande d'exhumation pour le caveau {exhumation.caveau.reference} a été refusée.\n\nPour plus d'informations, contactez l'administration.",
        from_email='jeremykounkou@icloud.com',
        to=[exhumation.demandeur.email],
    )

    return {"success": True, "message": "Exhumation refusée"}


@router.post("/effectuee/{exhumation_id}", auth=auth)
def mark_exhumation_completed(request, exhumation_id: int):
    """Marque une exhumation comme effectuée."""
    user = request.auth

    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}

    try:
        exhumation = Exhumation.objects.get(id=exhumation_id)
    except Exhumation.DoesNotExist:
        return {"success": False, "message": "Exhumation introuvable"}

    exhumation.statut = "EFFECTUEE"
    exhumation.save()

    caveau = exhumation.caveau
    caveau.statut = "DISPONIBLE"
    caveau.save()

    return {"success": True, "message": "Exhumation marquée comme effectuée"}