import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

from typing import Optional

load_dotenv()


def send_otp_email(email: str, otp: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM_EMAIL")

    if not all([smtp_host, smtp_port, smtp_user, smtp_pass, from_email]):
        raise RuntimeError("SMTP configuration missing in .env")

    message = MIMEText(f"Your OTP is: {otp}")
    message["Subject"] = "Your OTP Code"
    message["From"] = from_email
    message["To"] = email

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(message)
        server.quit()
        print(f"✅ EMAIL SENT to {email}")
    except Exception as e:
        print("❌ EMAIL FAILED:", e)
        raise


def send_invite_email(email: str, invite_token: str, group_name: str, group_id: str):
    """Send professional invite email with registration link"""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM_EMAIL")

    if not all([smtp_host, smtp_port, smtp_user, smtp_pass, from_email]):
        print("⚠️ SMTP config missing - Skipping email")
        return False

    # Frontend invite link
    invite_link = (
        f"http://localhost:3000/register?token={invite_token}&group={group_id}"
    )

    # Professional HTML email
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">🎉 Invitation to Join '{group_name}'</h2>
            
            <p>You've been invited to join <strong>{group_name}</strong>!</p>
            
            <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>👋 Join Now:</h3>
                <a href="{invite_link}" 
                   style="background: #2563eb; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 6px; font-weight: bold;">
                   Register & Join Group
                </a>
            </div>
            
            <p><small>This invite expires in 7 days. Copy-paste this link if button doesn't work:<br>
            {invite_link}</small></p>
            
            <hr style="margin: 30px 0;">
            <p style="color: #64748b; font-size: 14px;">
                Need help? Reply to this email.
            </p>
        </body>
    </html>
    """

    message = MIMEText(html_message, "html")
    message["Subject"] = f"🎉 Join {group_name} - You're Invited!"
    message["From"] = from_email
    message["To"] = email

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(message)
        server.quit()
        print(f"✅ INVITE EMAIL SENT to {email} → {group_name}")
        return True

    except Exception as e:
        print(f"❌ INVITE EMAIL FAILED to {email}:", e)
        return False
