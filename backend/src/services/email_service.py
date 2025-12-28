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
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, msg.as_string())
            
            print(f"✅ Email sent to: {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {e}")
            return False
    
    def send_email(self, to_email: str, subject: str, html_content: str, background: bool = True) -> bool:
        """Send an email (in background by default for faster response)"""
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
            return self._send_email_sync(to_email, subject, html_content)
    
    def send_verification_email(self, to_email: str, first_name: str, token: str) -> bool:
        """Send account verification email"""
        verification_link = f"{self.frontend_url}/activate/{token}"
        
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
                    <h1 style="color: white; margin: 0; font-size: 28px;">Welcome to Class Pulse! 🎓</h1>
                </div>
                
                <div style="background: white; padding: 40px; border-radius: 0 0 16px 16px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <h2 style="color: #065f46; margin-top: 0;">Hi {first_name}! 👋</h2>
                    
                    <p style="color: #374151; font-size: 16px; line-height: 1.6;">
                        Thank you for signing up for Class Pulse! We're excited to have you join our learning community.
                    </p>
                    
                    <p style="color: #374151; font-size: 16px; line-height: 1.6;">
                        Please verify your email address by clicking the button below:
                    </p>
                    
                    <div style="text-align: center; margin: 32px 0;">
                        <a href="{verification_link}" 
                           style="display: inline-block; background: linear-gradient(135deg, #10b981, #14b8a6); 
                                  color: white; padding: 16px 48px; text-decoration: none; 
                                  border-radius: 12px; font-weight: 600; font-size: 16px;
                                  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4);">
                            ✅ Verify My Email
                        </a>
                    </div>
                    
                    <p style="color: #6b7280; font-size: 14px; line-height: 1.6;">
                        Or copy and paste this link into your browser:
                    </p>
                    <p style="color: #10b981; font-size: 14px; word-break: break-all;">
                        {verification_link}
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 32px 0;">
                    
                    <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                        This link will expire in 24 hours. If you didn't create an account, you can safely ignore this email.
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
        
        return self.send_email(to_email, "Verify your Class Pulse account", html_content)
    
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

