import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import secrets
from datetime import datetime, timedelta
import threading


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = os.environ.get("SMTP_USER", "")
        self.smtp_password = os.environ.get("SMTP_PASSWORD", "")
        self.from_email = os.environ.get("FROM_EMAIL", self.smtp_user)
        self.frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    
    def generate_verification_token(self) -> str:
        """Generate a secure verification token"""
        return secrets.token_urlsafe(32)
    
    def get_token_expiry(self, hours: int = 24) -> datetime:
        """Get token expiry datetime"""
        return datetime.utcnow() + timedelta(hours=hours)
    
    def _send_email_sync(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send an email synchronously (internal use)"""
        try:
            if not self.smtp_user or not self.smtp_password:
                print(f"⚠️ SMTP credentials not configured. Email would be sent to: {to_email}")
                print(f"   Subject: {subject}")
                return True  # Return True for development
            
            print(f"📤 Starting email send to: {to_email}")
            print(f"   SMTP: {self.smtp_host}:{self.smtp_port}")
            print(f"   From: {self.smtp_user}")
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                print(f"   → Connected to SMTP server")
                server.starttls()
                print(f"   → TLS started")
                server.login(self.smtp_user, self.smtp_password)
                print(f"   → Logged in successfully")
                server.sendmail(self.from_email, to_email, msg.as_string())
                print(f"   → Email sent!")
            
            print(f"✅ Email delivered to: {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP AUTH ERROR for {to_email}: {e}")
            print(f"   Check SMTP_USER and SMTP_PASSWORD in environment variables")
            return False
        except smtplib.SMTPException as e:
            print(f"❌ SMTP ERROR for {to_email}: {e}")
            return False
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def send_email(self, to_email: str, subject: str, html_content: str, background: bool = False) -> bool:
        """Send an email (synchronous by default for reliability on Railway)"""
        if background:
            # Send in background thread - don't block the request
            thread = threading.Thread(
                target=self._send_email_sync,
                args=(to_email, subject, html_content)
            )
            thread.daemon = True
            thread.start()
            print(f"📧 Email queued for: {to_email}")
            return True
        else:
            # Synchronous - more reliable on Railway/serverless
            print(f"📧 Sending email to: {to_email}")
            return self._send_email_sync(to_email, subject, html_content)
    
    def send_verification_email(self, to_email: str, first_name: str, token: str) -> bool:
        """Send account verification email"""
        verification_link = f"{self.frontend_url}/activate/{token}"
        year = datetime.now().year
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email - Class Pulse</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f8fafc; -webkit-font-smoothing: antialiased;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f8fafc;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 520px;">
                    
                    <!-- Logo & Header -->
                    <tr>
                        <td align="center" style="padding-bottom: 32px;">
                            <table role="presentation" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td style="background: linear-gradient(135deg, #059669 0%, #0d9488 100%); padding: 12px 24px; border-radius: 50px;">
                                        <span style="color: #ffffff; font-size: 20px; font-weight: 700; letter-spacing: -0.5px;">Class Pulse</span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Main Card -->
                    <tr>
                        <td style="background: #ffffff; border-radius: 16px; box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08); overflow: hidden;">
                            
                            <!-- Green Accent Bar -->
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td style="height: 4px; background: linear-gradient(90deg, #059669 0%, #0d9488 50%, #06b6d4 100%);"></td>
                                </tr>
                            </table>
                            
                            <!-- Content -->
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td style="padding: 48px 40px;">
                                        
                                        <!-- Icon -->
                                        <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                            <tr>
                                                <td align="center" style="padding-bottom: 24px;">
                                                    <div style="width: 64px; height: 64px; background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); border-radius: 50%; display: inline-block; line-height: 64px; text-align: center;">
                                                        <span style="font-size: 28px;">✉️</span>
                                                    </div>
                                                </td>
                                            </tr>
                                        </table>
                                        
                                        <!-- Greeting -->
                                        <h1 style="margin: 0 0 8px 0; font-size: 24px; font-weight: 700; color: #111827; text-align: center; letter-spacing: -0.5px;">
                                            Verify your email address
                                        </h1>
                                        <p style="margin: 0 0 32px 0; font-size: 15px; color: #6b7280; text-align: center; line-height: 1.5;">
                                            Hi {first_name}, thanks for signing up! Please confirm your email to get started.
                                        </p>
                                        
                                        <!-- CTA Button -->
                                        <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                            <tr>
                                                <td align="center" style="padding-bottom: 32px;">
                                                    <a href="{verification_link}" 
                                                       style="display: inline-block; background: linear-gradient(135deg, #059669 0%, #0d9488 100%); 
                                                              color: #ffffff; padding: 16px 40px; text-decoration: none; 
                                                              border-radius: 8px; font-weight: 600; font-size: 15px;
                                                              box-shadow: 0 4px 12px rgba(5, 150, 105, 0.35);
                                                              transition: all 0.2s ease;">
                                                        Verify Email Address
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                        
                                        <!-- Divider -->
                                        <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                            <tr>
                                                <td style="border-top: 1px solid #e5e7eb; padding-top: 24px;">
                                                    <p style="margin: 0 0 12px 0; font-size: 13px; color: #9ca3af; text-align: center;">
                                                        Or copy and paste this link in your browser:
                                                    </p>
                                                    <p style="margin: 0; font-size: 13px; color: #059669; text-align: center; word-break: break-all; background: #f0fdf4; padding: 12px 16px; border-radius: 8px; border: 1px solid #d1fae5;">
                                                        {verification_link}
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                        
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 32px 20px;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td align="center">
                                        <p style="margin: 0 0 8px 0; font-size: 13px; color: #9ca3af;">
                                            This link expires in 24 hours for security reasons.
                                        </p>
                                        <p style="margin: 0 0 16px 0; font-size: 13px; color: #9ca3af;">
                                            If you didn't create an account, you can safely ignore this email.
                                        </p>
                                        <p style="margin: 0; font-size: 12px; color: #d1d5db;">
                                            © {year} Class Pulse. All rights reserved.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        return self.send_email(to_email, "Verify your email - Class Pulse", html_content)
    
    def send_password_reset_email(self, to_email: str, first_name: str, token: str) -> bool:
        """Send password reset email"""
        reset_link = f"{self.frontend_url}/reset-password/{token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0fdf4;">
            <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                <div style="background: linear-gradient(135deg, #10b981, #14b8a6); padding: 40px; border-radius: 16px 16px 0 0; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">Password Reset Request 🔐</h1>
                </div>
                
                <div style="background: white; padding: 40px; border-radius: 0 0 16px 16px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <h2 style="color: #065f46; margin-top: 0;">Hi {first_name}!</h2>
                    
                    <p style="color: #374151; font-size: 16px; line-height: 1.6;">
                        We received a request to reset your password. Click the button below to create a new password:
                    </p>
                    
                    <div style="text-align: center; margin: 32px 0;">
                        <a href="{reset_link}" 
                           style="display: inline-block; background: linear-gradient(135deg, #10b981, #14b8a6); 
                                  color: white; padding: 16px 48px; text-decoration: none; 
                                  border-radius: 12px; font-weight: 600; font-size: 16px;
                                  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4);">
                            🔑 Reset Password
                        </a>
                    </div>
                    
                    <p style="color: #6b7280; font-size: 14px; line-height: 1.6;">
                        Or copy and paste this link into your browser:
                    </p>
                    <p style="color: #10b981; font-size: 14px; word-break: break-all;">
                        {reset_link}
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 32px 0;">
                    
                    <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                        This link will expire in 1 hour. If you didn't request a password reset, you can safely ignore this email.
                    </p>
                </div>
                
                <div style="text-align: center; margin-top: 24px;">
                    <p style="color: #6b7280; font-size: 12px;">
                        © {datetime.now().year} Class Pulse. All rights reserved.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, "Reset your Class Pulse password", html_content)


# Singleton instance
email_service = EmailService()

