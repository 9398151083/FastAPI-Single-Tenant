import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

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
