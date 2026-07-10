# exhumations/pdf.py
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
import io


def generate_authorization_pdf(exhumation):
    """Génère un PDF d'autorisation d'exhumation."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("AUTORISATION D'EXHUMATION", styles['Title']))
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph(f"Référence caveau : {exhumation.caveau.reference}", styles['Normal']))
    elements.append(Paragraph(f"Défunt : {exhumation.nom_defunt}", styles['Normal']))
    elements.append(Paragraph(f"Demandeur : {exhumation.demandeur.username}", styles['Normal']))
    elements.append(Paragraph(f"Motif : {exhumation.motif}", styles['Normal']))
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph(f"Date d'exhumation prévue : {exhumation.date_exhumation}", styles['Normal']))
    elements.append(Spacer(1, 0.5 * cm))

    if exhumation.observations:
        elements.append(Paragraph(f"Observations : {exhumation.observations}", styles['Normal']))

    elements.append(Spacer(1, 1 * cm))
    elements.append(Paragraph(f"Approuvé par : {exhumation.approuve_par.username if exhumation.approuve_par else ''}", styles['Normal']))
    elements.append(Spacer(1, 1 * cm))
    elements.append(Paragraph("Signature et cachet de l'administration", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer