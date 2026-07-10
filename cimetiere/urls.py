# cimetiere/urls.py
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from users.api import router as users_router
from reservations.api import router as reservations_router
from caveaux.api import router as caveaux_router
from finances.api import router as finances_router
from concessions.api import router as concessions_router
from exhumations.api import router as exhumations_router
from dashboard.api import router as dashboard_router
from caveaux.views import public_map_view, admin_pick_location_view

api = NinjaAPI()

api.add_router("/users/", users_router)
api.add_router("/reservations/", reservations_router)
api.add_router("/caveaux/", caveaux_router)
api.add_router("/finances/", finances_router)
api.add_router("/concessions/", concessions_router)
api.add_router("/exhumations/", exhumations_router)
api.add_router("/dashboard/", dashboard_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
    path('carte/', public_map_view, name='public_map'),
    path('carte/admin-pick/', admin_pick_location_view, name='admin_pick_location'),
]