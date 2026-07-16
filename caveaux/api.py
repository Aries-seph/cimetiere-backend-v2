# caveaux/api.py
from ninja import Router
from caveaux.models import Caveau, Bloc, Section
from caveaux.schemas import (
    CaveauCreateSchema, CaveauUpdateSchema, CaveauResponseSchema,
    BlocCreateSchema, SectionCreateSchema
)
from users.auth import JWTAuth
from typing import Optional, List, Dict, Any

router = Router()
auth = JWTAuth()


def _is_admin(user) -> bool:
    """Vérifie si l'utilisateur a un rôle administratif."""
    return user.role in ["ADMIN", "AGENT"]


# ============ CAVEAUX ============
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
            "id", "nom", "section__nom", "section_id"
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


# ============ SECTIONS ============
@router.get("/section", auth=auth, response=List[Dict[str, Any]])
def get_sections_list(request):
    """Récupère la liste de toutes les sections."""
    return list(
        Section.objects.values("id", "nom", "description")
    )


@router.post("/sections", auth=auth)
def create_new_section(request, data: SectionCreateSchema):
    """Crée une nouvelle section."""
    user = request.auth
    
    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}
    
    section = Section.objects.create(
        nom=data.nom,
        description=data.description or ""
    )
    
    return {"success": True, "id": section.id, "message": "Section créée avec succès"}


@router.delete("/sections/{section_id}", auth=auth)
def delete_section(request, section_id: int):
    """Supprime une section."""
    user = request.auth
    
    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}
    
    try:
        section = Section.objects.get(id=section_id)
    except Section.DoesNotExist:
        return {"success": False, "message": "Section introuvable"}
    
    # Vérifier si la section a des blocs
    if section.blocs.exists():
        return {"success": False, "message": "Cette section contient des blocs. Supprimez-les d'abord."}
    
    section.delete()
    return {"success": True, "message": "Section supprimée"}


# ============ BLOCS ============
@router.post("/blocs", auth=auth)
def create_new_bloc(request, data: BlocCreateSchema):
    """Crée un nouveau bloc."""
    user = request.auth
    
    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}
    
    try:
        section = Section.objects.get(id=data.section_id)
    except Section.DoesNotExist:
        return {"success": False, "message": "Section introuvable"}
    
    bloc = Bloc.objects.create(
        section=section,
        nom=data.nom
    )
    
    return {"success": True, "id": bloc.id, "message": "Bloc créé avec succès"}


@router.delete("/blocs/{bloc_id}", auth=auth)
def delete_bloc(request, bloc_id: int):
    """Supprime un bloc."""
    user = request.auth
    
    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}
    
    try:
        bloc = Bloc.objects.get(id=bloc_id)
    except Bloc.DoesNotExist:
        return {"success": False, "message": "Bloc introuvable"}
    
    # Vérifier si le bloc a des caveaux
    if bloc.caveaux.exists():
        return {"success": False, "message": "Ce bloc contient des caveaux. Supprimez-les d'abord."}
    
    bloc.delete()
    return {"success": True, "message": "Bloc supprimé"}