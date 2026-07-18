# finances/pdf.py
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
import io

def generate_invoice_pdf(paiement):
    """Génère un PDF de facture pour un paiement."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Titre
    elements.append(Paragraph("FACTURE DE PAIEMENT", styles['Title']))
    elements.append(Spacer(1, 0.5 * cm))

    # Gestion sécurisée de la date
    date_str = "-"
    if paiement.created_at:
        try:
            date_str = paiement.created_at.strftime('%d/%m/%Y %H:%M')
        except AttributeError:
            date_str = str(paiement.created_at)

    # Infos facture
    elements.append(Paragraph(f"<b>Référence :</b> {paiement.reference}", styles['Normal']))
    elements.append(Paragraph(f"<b>Date :</b> {date_str}", styles['Normal']))
    elements.append(Spacer(1, 0.5 * cm))

    # Infos client
    elements.append(Paragraph("INFORMATIONS CLIENT", styles['Heading2']))
    elements.append(Paragraph(f"Nom : {paiement.client.username if paiement.client else '-'}", styles['Normal']))
    elements.append(Paragraph(f"Email : {paiement.client.email if paiement.client else '-'}", styles['Normal']))
    elements.append(Spacer(1, 0.5 * cm))

    # Infos réservation
    elements.append(Paragraph("DÉTAILS RÉSERVATION", styles['Heading2']))
    caveau_ref = "-"
    nom_defunt = "-"
    if paiement.reservation:
        nom_defunt = paiement.reservation.nom_defunt
        if paiement.reservation.caveau:
            caveau_ref = paiement.reservation.caveau.reference

    elements.append(Paragraph(f"Caveau : {caveau_ref}", styles['Normal']))
    elements.append(Paragraph(f"Défunt : {nom_defunt}", styles['Normal']))
    elements.append(Spacer(1, 0.5 * cm))

    # Résolution sécurisée du canal d'achat
    try:
        canal_str = paiement.get_canal_display()
    except AttributeError:
        canal_str = getattr(paiement, 'canal', '-')

    # Tableau paiement
    elements.append(Paragraph("DÉTAILS PAIEMENT", styles['Heading2']))
    data = [
        ["Description", "Canal", "Montant"],
        ["Paiement caveau", canal_str, f"{paiement.montant} FCFA"],
    ]

    table = Table(data, colWidths=[7 * cm, 5 * cm, 4 * cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph(f"<b>Total payé : {paiement.montant} FCFA</b>", styles['Normal']))
    elements.append(Spacer(1, 1 * cm))
    elements.append(Paragraph("Merci pour votre confiance.", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer