from .models import AuditLog


def log_action(user, action, modele="", objet_id="", objet_repr="", reservation=None, detail=""):
    AuditLog.objects.create(
        user=user,
        reservation=reservation,
        modele=modele,
        objet_id=str(objet_id) if objet_id else "",
        objet_repr=objet_repr,
        action=action,
        detail=detail,
    )