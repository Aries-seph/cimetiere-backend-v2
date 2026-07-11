# cimetiere/brevo.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_brevo_email(to_email, subject, html_content, text_content=None):
    """
    Envoie un email via SMTP Brevo
    """
    try:
        smtp_host = os.getenv('EMAIL_HOST', 'smtp-relay.brevo.com')
        smtp_port = int(os.getenv('EMAIL_PORT', 587))
        smtp_user = os.getenv('EMAIL_HOST_USER')
        smtp_password = os.getenv('EMAIL_HOST_PASSWORD')
        
        if not smtp_password:
            print("❌ EMAIL_HOST_PASSWORD non définie")
            return False
        
        # Créer le message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = os.getenv('DEFAULT_FROM_EMAIL', smtp_user)
        msg['To'] = to_email
        
        # Partie texte
        if text_content:
            part1 = MIMEText(text_content, 'plain')
            msg.attach(part1)
        
        # Partie HTML
        part2 = MIMEText(html_content, 'html')
        msg.attach(part2)
        
        # Envoyer via SMTP
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        print(f"✅ Email envoyé à {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur SMTP: {e}")
        return False