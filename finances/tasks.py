# finances/tasks.py
from django.core.mail import EmailMessage
from finances.pdf import generate_invoice_pdf
import logging

logger = logging.getLogger(__name__)

def send_invoice_email_task(paiement_id):
    """Tâche asynchrone exécutée par le worker pour générer et envoyer la facture."""
    # Import local pour éviter les imports circulaires au démarrage de Django
    from finances.models import Paiement

    try:
        logger.info(f"🔵 [Worker] Début traitement e-mail pour paiement ID: {paiement_id}")
        paiement = Paiement.objects.get(id=paiement_id)
        
        if not paiement.client or not paiement.client.email:
            logger.error(f"🔴 [Worker] Le paiement {paiement.reference} n'a pas de client ou d'email valide.")
            return

        # 1. Génération du PDF
        pdf_buffer = generate_invoice_pdf(paiement)
        logger.info(f"🔵 [Worker] PDF généré avec succès pour {paiement.reference}")

        # 2. Construction du mail
        email = EmailMessage(
            subject='Votre facture de paiement',
            body=f'Bonjour {paiement.client.username},\n\nVeuillez trouver ci-joint votre facture pour le paiement {paiement.reference}.\n\nMerci pour votre confiance.',
            from_email='jeremykounkou@icloud.com',
            to=[paiement.client.email],
            reply_to=['jeremykounkou@icloud.com'],
        )

        # 3. Attachement du fichier à partir du buffer
        email.attach(
            f'facture_{paiement.reference}.pdf',
            pdf_buffer.read(),
            'application/pdf'
        )

        # 4. Envoi SMTP
        email.send()
        logger.info(f"✅ [Worker] Email envoyé avec succès à {paiement.client.email}")

    except Paiement.DoesNotExist:
        logger.error(f"🔴 [Worker] Paiement avec l'ID {paiement_id} introuvable en BDD.")
    except Exception as e:
        logger.error(f"🔴 [Worker] Erreur critique lors de l'envoi de l'email : {e}")