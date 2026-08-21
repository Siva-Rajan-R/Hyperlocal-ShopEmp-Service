import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from icecream import ic
from core.configs.settings_config import SETTINGS
from hyperlocal_platform.core.enums.environment_enum import EnvironmentEnum

logger = logging.getLogger(__name__)

SMTP_HOST = SETTINGS.SMTP_HOST
SMTP_PORT = SETTINGS.SMTP_PORT
SMTP_USER = SETTINGS.SMTP_USER
SMTP_PASS = SETTINGS.SMTP_PASS
BACKEND_BASE_URL = SETTINGS.BACKEND_BASE_URL

async def send_verification_email(email: str, name: str, token: str, temp_password: str = None):
    verification_link = f"{BACKEND_BASE_URL}/employees/verify/token?token={token}"
    logger.info(f"VERIFICATION URL: {verification_link}")
    if temp_password:
        logger.info(f"TEMPORARY PASSWORD: {temp_password}")
    
    subject = "Verify Your Employee Account"
    
    password_text = f"\nYour temporary password is: {temp_password}\nPlease change it after logging in." if temp_password else ""

    body = f"""Hi {name},

You have been invited to join the shop. Please click the link below to accept the invitation and verify your account:
{verification_link}
{password_text}

If you did not request this, please ignore this email.
"""

    if SETTINGS.ENVIRONMENT.value == EnvironmentEnum.DEVELOPMENT.value or not SMTP_USER:
        ic("--- [DEV MODE] Sending Verification Email ---")
        ic(f"To: {email}")
        ic(f"Subject: {subject}")
        ic(f"Link: {verification_link}")
        ic("--------------------------------------------")
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        ic(f"Verification email sent to {email} successfully.")
        return True
    except Exception as e:
        ic(f"Failed to send email to {email}: {e}")
        return False
