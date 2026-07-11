# cimetiere/brevo.py
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

def send_brevo_email(to_email, subject, html_content, text_content=None):
    """
    Envoie un email via l'API Brevo (pas SMTP)
    """
    try:
        api_key = os.getenv('BREVO_API_KEY')
        
        if not api_key:
            print("❌ BREVO_API_KEY non définie")
            return False
        
        # Configuration de l'API
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = api_key
        
        # Création du client API
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
        
        # Construction de l'email
        sender = {
            "name": "Cimetière V2",
            "email": os.getenv('DEFAULT_FROM_EMAIL', 'jeremykounkou@icloud.com')
        }
        
        to = [{"email": to_email}]
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            sender=sender,
            to=to,
            subject=subject,
            html_content=html_content,
            text_content=text_content or html_content
        )
        
        # Envoi via l'API (pas SMTP)
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(f"✅ Email envoyé à {to_email} - ID: {api_response.message_id}")
        return True
        
    except ApiException as e:
        print(f"❌ Erreur Brevo API: {e}")
        print(f"   Status: {e.status if hasattr(e, 'status') else 'N/A'}")
        print(f"   Body: {e.body if hasattr(e, 'body') else 'N/A'}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False