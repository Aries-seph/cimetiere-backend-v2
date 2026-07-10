# caveaux/views.py
from django.http import HttpResponse


def public_map_view(request):
    """Vue de la carte publique pour les clients."""
    html = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Carte des caveaux - Cimetière</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { margin: 0; font-family: Arial, sans-serif; background: #0F0F1A; }
        #map { height: 100vh; width: 100%; }
        .legend {
            position: absolute; top: 10px; right: 10px; z-index: 1000;
            background: #1A1A2E; color: #fff; padding: 10px 14px;
            border-radius: 10px; font-size: 13px; border: 1px solid #2D2D44;
        }
        .legend div { margin: 4px 0; display: flex; align-items: center; gap: 8px; }
        .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
        .popup-btn {
            background: #7C3AED; color: white; border: none; padding: 8px 14px;
            border-radius: 6px; cursor: pointer; font-size: 13px; margin-top: 6px;
        }
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="legend">
        <div><span class="dot" style="background:#10B981"></span> Disponible</div>
        <div><span class="dot" style="background:#F59E0B"></span> Réservé</div>
        <div><span class="dot" style="background:#EF4444"></span> Occupé</div>
        <div><span class="dot" style="background:#6B7280"></span> Inexploitable</div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const STATUT_COLORS = {
            "DISPONIBLE": "#10B981",
            "RESERVE": "#F59E0B",
            "OCCUPE": "#EF4444",
            "INEXPLOITABLE": "#6B7280",
        };
        const STATUT_LABELS = {
            "DISPONIBLE": "Disponible",
            "RESERVE": "Réservé",
            "OCCUPE": "Occupé",
            "INEXPLOITABLE": "Inexploitable",
        };

        const APP_URL = "http://127.0.0.1:8550";

        const map = L.map('map').setView([-4.7761, 11.8635], 13);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors',
            maxZoom: 19,
        }).addTo(map);

        fetch('/api/caveaux/public-map')
            .then(res => res.json())
            .then(caveaux => {
                if (!Array.isArray(caveaux) || caveaux.length === 0) return;

                const bounds = [];

                caveaux.forEach(c => {
                    const color = STATUT_COLORS[c.statut] || "#6B7280";
                    const marker = L.circleMarker([c.latitude, c.longitude], {
                        radius: 10,
                        fillColor: color,
                        color: "#fff",
                        weight: 2,
                        fillOpacity: 1,
                    }).addTo(map);

                    bounds.push([c.latitude, c.longitude]);

                    let popupContent = `
                        <b>${c.reference}</b><br>
                        Statut : ${STATUT_LABELS[c.statut] || c.statut}<br>
                        Dimensions : ${c.longueur}m x ${c.largeur}m<br>
                    `;

                    if (c.statut === "DISPONIBLE") {
                        popupContent += `<button class="popup-btn" onclick="reserver(${c.id})">Réserver ce caveau</button>`;
                    }

                    marker.bindPopup(popupContent);
                });

                if (bounds.length > 0) {
                    map.fitBounds(bounds, { padding: [40, 40] });
                }
            });

        function reserver(caveauId) {
            window.location.href = APP_URL + "/?caveau_id=" + caveauId;
        }
    </script>
</body>
</html>
    """
    return HttpResponse(html)


def admin_pick_location_view(request):
    """Vue de sélection d'emplacement pour l'admin."""
    token = request.GET.get("token", "")
    caveau_id = request.GET.get("caveau_id", "")
    
    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Sélectionner un emplacement</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body {{ margin: 0; font-family: Arial, sans-serif; background: #0F0F1A; }}
        #map {{ height: 100vh; width: 100%; cursor: crosshair; }}
        #info {{
            position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
            z-index: 1000; background: #1A1A2E; color: #fff;
            padding: 14px 20px; border-radius: 10px; font-size: 14px;
            border: 1px solid #2D2D44; text-align: center; min-width: 320px;
        }}
        #coords {{ font-weight: bold; color: #A78BFA; margin: 6px 0; }}
        #confirm-btn {{
            background: #7C3AED; color: white; border: none;
            padding: 10px 20px; border-radius: 6px; cursor: pointer;
            font-size: 14px; margin-top: 8px; display: none;
        }}
        #status {{ color: #10B981; margin-top: 6px; display: none; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div id="info">
        <div>Cliquez sur la carte pour sélectionner l'emplacement du caveau</div>
        <div id="coords"></div>
        <button id="confirm-btn" onclick="confirmLocation()">✓ Confirmer cet emplacement</button>
        <div id="status">Coordonnées enregistrées, retour à l'application...</div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const TOKEN = "{token}";
        const CAVEAU_ID = "{caveau_id}";
        const APP_URL = "http://127.0.0.1:8550";

        const map = L.map('map').setView([-4.7761, 11.8635], 14);

        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; OpenStreetMap contributors',
            maxZoom: 19,
        }}).addTo(map);

        let marker = null;
        let selectedLat = null;
        let selectedLng = null;

        map.on('click', function(e) {{
            selectedLat = e.latlng.lat.toFixed(7);
            selectedLng = e.latlng.lng.toFixed(7);

            if (marker) {{
                marker.setLatLng(e.latlng);
            }} else {{
                marker = L.marker(e.latlng).addTo(map);
            }}

            document.getElementById('coords').innerHTML =
                'Latitude : ' + selectedLat + '<br>Longitude : ' + selectedLng;
            document.getElementById('confirm-btn').style.display = 'inline-block';
        }});

        async function confirmLocation() {{
            if (!selectedLat || !selectedLng) return;

            document.getElementById('confirm-btn').disabled = true;

            const pickData = {{
                latitude: parseFloat(selectedLat),
                longitude: parseFloat(selectedLng),
                caveau_id: CAVEAU_ID ? parseInt(CAVEAU_ID) : null
            }};
            
            sessionStorage.setItem('pending_pick_data', JSON.stringify(pickData));

            const response = await fetch('/api/caveaux/save-pick/', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + TOKEN,
                }},
                body: JSON.stringify(pickData),
            }});

            const data = await response.json();
            if (data.success) {{
                document.getElementById('status').style.display = 'block';
                setTimeout(() => {{
                    window.location.href = APP_URL + 
                        '?pick_lat=' + selectedLat + 
                        '&pick_lng=' + selectedLng +
                        (CAVEAU_ID ? '&pick_caveau_id=' + CAVEAU_ID : '');
                }}, 1000);
            }}
        }}
    </script>
</body>
</html>
    """
    return HttpResponse(html)