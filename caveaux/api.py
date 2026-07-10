# caveaux/api.py
from ninja import Router
from caveaux.models import Caveau, Bloc, Section
from caveaux.schemas import CaveauCreateSchema, CaveauUpdateSchema, CaveauResponseSchema
from users.auth import JWTAuth
from typing import Optional, List, Dict, Any

router = Router()
auth = JWTAuth()


def _is_admin(user) -> bool:
    """Vérifie si l'utilisateur a un rôle administratif."""
    return user.role in ["ADMIN", "AGENT"]


@router.get("/", auth=auth, response=List[Dict[str, Any]])
def get_caveaux_list(request):
    """Récupère la liste de tous les caveaux."""
    return list(
        Caveau.objects.values(
            "id", "reference", "longueur", "largeur", "statut",
            "bloc_id", "latitude", "longitude"
        )
    )


@router.get("/blocs", auth=auth, response=List[Dict[str, Any]])
def get_blocs_list(request):
    """Récupère la liste de tous les blocs avec leur section."""
    return list(
        Bloc.objects.select_related('section').values(
            "id", "nom", "section__nom"
        )
    )


@router.get("/public-map", response=List[Dict[str, Any]])
def get_caveaux_for_public_map(request):
    """Récupère les caveaux avec coordonnées pour la carte publique."""
    return list(
        Caveau.objects
        .exclude(latitude__isnull=True)
        .exclude(longitude__isnull=True)
        .values(
            "id", "reference", "longueur", "largeur", 
            "statut", "latitude", "longitude"
        )
    )


@router.get("/{caveau_id}", auth=auth, response=Dict[str, Any])
def get_caveau_detail(request, caveau_id: int):
    """Récupère les détails d'un caveau spécifique."""
    caveau = Caveau.objects.filter(id=caveau_id).values().first()
    
    if not caveau:
        return {
            "success": False,
            "message": "Caveau introuvable"
        }
    
    return caveau


@router.post("/", auth=auth)
def create_new_caveau(request, data: CaveauCreateSchema):
    """Crée un nouveau caveau."""
    user = request.auth
    
    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}
    
    try:
        bloc = Bloc.objects.get(id=data.bloc_id)
    except Bloc.DoesNotExist:
        return {"success": False, "message": "Bloc introuvable"}
    
    caveau = Caveau.objects.create(
        bloc=bloc,
        reference=data.reference,
        longueur=data.longueur,
        largeur=data.largeur,
        latitude=data.latitude,
        longitude=data.longitude
    )
    
    return {"success": True, "id": caveau.id, "message": "Caveau créé avec succès"}


@router.patch("/{caveau_id}", auth=auth)
def update_existing_caveau(request, caveau_id: int, data: CaveauUpdateSchema):
    """Met à jour un caveau existant."""
    user = request.auth
    
    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}
    
    try:
        caveau = Caveau.objects.get(id=caveau_id)
    except Caveau.DoesNotExist:
        return {"success": False, "message": "Caveau introuvable"}
    
    update_data = data.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(caveau, key, value)
    
    caveau.save()
    
    return {"success": True, "message": "Caveau mis à jour"}


@router.delete("/{caveau_id}", auth=auth)
def delete_existing_caveau(request, caveau_id: int):
    """Supprime un caveau."""
    user = request.auth
    
    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}
    
    try:
        caveau = Caveau.objects.get(id=caveau_id)
    except Caveau.DoesNotExist:
        return {"success": False, "message": "Caveau introuvable"}
    
    caveau.delete()
    
    return {"success": True, "message": "Caveau supprimé"}


@router.post("/save-pick/", auth=auth)
def save_selected_location(request, data: dict):
    """Sauvegarde les coordonnées sélectionnées sur la carte."""
    user = request.auth
    
    user.pending_pick_lat = data.get("latitude")
    user.pending_pick_lng = data.get("longitude")
    user.pending_pick_caveau_id = data.get("caveau_id")
    user.save()
    
    return {"success": True}