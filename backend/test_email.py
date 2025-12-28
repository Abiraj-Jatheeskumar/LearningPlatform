"""
Test script to verify SMTP email configuration
Run: python test_email.py
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Load from .env file if exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Get SMTP settings
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", SMTP_USER)

# Email to test (change this to your email)
TEST_EMAIL = "stackhackers@gmail.com"

print("=" * 50)
print("SMTP Configuration Test")
print("=" * 50)
print(f"SMTP_HOST: {SMTP_HOST}")
print(f"SMTP_PORT: {SMTP_PORT}")
print(f"SMTP_USER: {SMTP_USER}")
print(f"SMTP_PASSWORD: {'*' * len(SMTP_PASSWORD) if SMTP_PASSWORD else '❌ NOT SET'}")
print(f"FROM_EMAIL: {FROM_EMAIL}")
print(f"TEST_EMAIL: {TEST_EMAIL}")
print("=" * 50)

if not SMTP_USER or not SMTP_PASSWORD:
    print("\n❌ ERROR: SMTP_USER or SMTP_PASSWORD not set!")
    print("\nPlease set these environment variables:")
    print("  - SMTP_USER=your-email@gmail.com")
    print("  - SMTP_PASSWORD=your-16-char-app-password")
    exit(1)

print("\n📧 Attempting to send test email...")

try:
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "🧪 Test Email from Class Pulse"
    msg['From'] = FROM_EMAIL
    msg['To'] = TEST_EMAIL
    
    html_content = """
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h1 style="color: #10b981;">✅ Email Configuration Works!</h1>
        <p>This is a test email from Class Pulse.</p>
        <p>If you see this, your SMTP settings are correct!</p>
    </body>
    </html>
    """
    
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)
    
    # Connect and send
    print(f"  → Connecting to {SMTP_HOST}:{SMTP_PORT}...")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        print("  → Starting TLS...")
        server.starttls()
        print(f"  → Logging in as {SMTP_USER}...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        print(f"  → Sending email to {TEST_EMAIL}...")
        server.sendmail(FROM_EMAIL, TEST_EMAIL, msg.as_string())
    
    print("\n✅ SUCCESS! Email sent!")
    print(f"   Check {TEST_EMAIL} inbox (and spam folder)")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ AUTHENTICATION ERROR!")
    print(f"   {e}")
    print("\n   Possible fixes:")
    print("   1. Make sure 2-Step Verification is ON in your Google account")
    print("   2. Create an App Password at: https://myaccount.google.com/apppasswords")
    print("   3. Use the 16-character App Password (not your regular Gmail password)")
    print("   4. Remove spaces from the App Password")
    
except smtplib.SMTPException as e:
    print(f"\n❌ SMTP ERROR: {e}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")

