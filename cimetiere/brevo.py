# cimetiere/brevo.py
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings

def send_brevo_email(to_email, subject, html_content, text_content=None):
    """
    Envoie un email via l'API Brevo
    
    Args:
        to_email (str): Email du destinataire
        subject (str): Sujet de l'email
        html_content (str): Contenu HTML de l'email
        text_content (str, optional): Contenu texte alternatif
    
    Returns:
        bool: True si l'email a été envoyé, False sinon
    """
    try:
        # Configuration de l'API
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = os.getenv('BREVO_API_KEY')
        
        # Création du client API
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
        
        # Construction de l'email
        sender = {
            "name": "Cimetière V2",
            "email": os.getenv('DEFAULT_FROM_EMAIL', 'noreply@cimetiere-v2.com')
        }
        
        to = [{"email": to_email}]
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            sender=sender,
            to=to,
            subject=subject,
            html_content=html_content,
            text_content=text_content or html_content
        )
        
        # Envoi
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(f"✅ Email envoyé à {to_email} - ID: {api_response.message_id}")
        return True
        
    except ApiException as e:
        print(f"❌ Erreur Brevo: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def send_mfa_code(user, code):
    """Envoie le code MFA à l'utilisateur"""
    subject = "🔐 Votre code de connexion - Cimetière V2"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .code {{ font-size: 32px; font-weight: bold; color: #1A56DB; text-align: center; padding: 20px; background: #f0f4ff; border-radius: 8px; margin: 20px 0; }}
            .footer {{ margin-top: 20px; font-size: 12px; color: #6B7280; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2 style="color: #1A56DB;">🔐 Connexion à votre compte</h2>
            <p>Bonjour <strong>{user.username}</strong>,</p>
            <p>Voici votre code de vérification à usage unique :</p>
            <div class="code">{code}</div>
            <p>Ce code expire dans <strong>10 minutes</strong>.</p>
            <p>Si vous n'êtes pas à l'origine de cette demande, ignorez simplement cet email.</p>
            <div class="footer">
                <p>© 2026 Cimetière V2 - Application de gestion de cimetière</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_brevo_email(user.email, subject, html_content)

def send_reservation_confirmation(user, reservation):
    """Envoie une confirmation de réservation"""
    subject = "✅ Réservation confirmée - Cimetière V2"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .info {{ background: #f0f4ff; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2 style="color: #1A56DB;">✅ Réservation confirmée</h2>
            <p>Bonjour <strong>{user.username}</strong>,</p>
            <p>Votre réservation a été confirmée avec succès !</p>
            <div class="info">
                <p><strong>Caveau :</strong> {reservation.caveau.reference}</p>
                <p><strong>Défunt :</strong> {reservation.nom_defunt}</p>
                <p><strong>Statut :</strong> {reservation.get_statut_display()}</p>
            </div>
            <p>Merci de votre confiance.</p>
            <div class="footer">
                <p>© 2026 Cimetière V2 - Application de gestion de cimetière</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_brevo_email(user.email, subject, html_content)