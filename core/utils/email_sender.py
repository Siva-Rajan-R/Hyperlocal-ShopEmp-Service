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
FRONTEND_BASE_URL = SETTINGS.FRONTEND_BASE_URL


async def send_verification_email(email: str, name: str, token: str, temp_password: str = None):
    verification_link = f"{BACKEND_BASE_URL}/employees/verify/token?token={token}"
    logger.info(f"VERIFICATION URL: {verification_link}")
    if temp_password:
        logger.info(f"TEMPORARY PASSWORD: {temp_password}")
    
    subject = "Verify Your Employee Account — RetailerPro"
    
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


async def send_employee_credentials_email(
    email: str,
    name: str,
    password: str = None,
    shop_name: str = "Retail Store",
    role: str = "STAFF",
    login_url: str = None
):
    target_login_url = login_url or f"{FRONTEND_BASE_URL}/login" if FRONTEND_BASE_URL else "http://localhost:5173/login"
    subject = f"Welcome to {shop_name} — Your Employee Login Credentials"

    password_display = password if password else "Use your existing account password"

    plain_body = f"""Hello {name},

Welcome to {shop_name}! Your employee account has been successfully verified and activated.

Here are your account login details:
---------------------------------------------
Portal Link: {target_login_url}
Email: {email}
Password: {password_display}
Role: {role}
---------------------------------------------

For security, please log in and change your password immediately.

Best regards,
{shop_name} & RetailerPro Team
"""

    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{subject}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; color: #1e293b; }}
    .container {{ max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }}
    .header {{ background: linear-gradient(135deg, #2563eb, #1d4ed8, #1e40af); padding: 28px 24px; text-align: center; color: #ffffff; }}
    .header h1 {{ margin: 0; font-size: 20px; font-weight: 800; letter-spacing: -0.5px; }}
    .header p {{ margin: 6px 0 0 0; font-size: 12px; color: #bfdbfe; text-transform: uppercase; font-weight: 700; letter-spacing: 1px; }}
    .content {{ padding: 28px 24px; }}
    .greeting {{ font-size: 15px; font-weight: 600; color: #0f172a; margin-bottom: 8px; }}
    .desc {{ font-size: 13px; line-height: 1.6; color: #475569; margin-bottom: 20px; }}
    .card {{ background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 12px; padding: 18px 20px; margin-bottom: 24px; }}
    .card-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e2e8f0; font-size: 13px; }}
    .card-row:last-child {{ border-bottom: none; }}
    .card-label {{ color: #64748b; font-weight: 600; }}
    .card-value {{ color: #0f172a; font-weight: 700; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
    .password-badge {{ background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 6px; font-weight: 800; }}
    .btn {{ display: block; text-align: center; background: #2563eb; color: #ffffff !important; text-decoration: none; font-weight: 700; font-size: 14px; padding: 12px 24px; border-radius: 10px; margin-top: 10px; }}
    .footer {{ padding: 18px 24px; background: #f1f5f9; text-align: center; font-size: 11px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>RetailerPro Hub</h1>
      <p>Employee Account Activated</p>
    </div>
    <div class="content">
      <div class="greeting">Hello {name},</div>
      <p class="desc">
        Welcome to <strong>{shop_name}</strong>! Your employee account has been successfully verified. You can now access your shop dashboard, counter billing, and inventory using the credentials below:
      </p>

      <div class="card">
        <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
          <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 8px 0; color: #64748b; font-weight: 600;">Store</td>
            <td style="padding: 8px 0; text-align: right; color: #0f172a; font-weight: 700;">{shop_name}</td>
          </tr>
          <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 8px 0; color: #64748b; font-weight: 600;">Role</td>
            <td style="padding: 8px 0; text-align: right; color: #2563eb; font-weight: 700;">{role}</td>
          </tr>
          <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 8px 0; color: #64748b; font-weight: 600;">Email (Username)</td>
            <td style="padding: 8px 0; text-align: right; color: #0f172a; font-weight: 700; font-family: monospace;">{email}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #64748b; font-weight: 600;">Password</td>
            <td style="padding: 8px 0; text-align: right; color: #1e40af; font-weight: 800; font-family: monospace; background: #eff6ff; border-radius: 4px; padding-right: 6px;">{password_display}</td>
          </tr>
        </table>
      </div>

      <a href="{target_login_url}" class="btn" target="_blank">Log In to Your Store Portal</a>

      <p style="font-size: 11px; color: #64748b; margin-top: 18px; line-height: 1.5;">
        🔒 <em>Security Tip: For your security, please update your password after your first login.</em>
      </p>
    </div>
    <div class="footer">
      This is an automated notification sent to {email}. If you have any questions, contact your shop administrator.
    </div>
  </div>
</body>
</html>
"""

    if SETTINGS.ENVIRONMENT.value == EnvironmentEnum.DEVELOPMENT.value or not SMTP_USER:
        ic("--- [DEV MODE] Sending Employee Credentials Email ---")
        ic(f"To: {email}")
        ic(f"Subject: {subject}")
        ic(f"Shop: {shop_name}")
        ic(f"Role: {role}")
        ic(f"Password: {password_display}")
        ic(f"Login URL: {target_login_url}")
        ic("-----------------------------------------------------")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = SMTP_USER
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(plain_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        ic(f"Employee credentials email sent to {email} successfully.")
        return True
    except Exception as e:
        ic(f"Failed to send credentials email to {email}: {e}")
        return False
