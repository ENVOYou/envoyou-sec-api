import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import Optional
from datetime import datetime

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SMTP_USERNAME", "noreply@envoyou.com")
        self.sender_password = os.getenv("SMTP_PASSWORD", "")
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        # Check if we're in offline mode (for Railway deployment)
        self.offline_mode = os.getenv("EMAIL_OFFLINE_MODE", "false").lower() == "true"
        
        # Alternative SMTP configurations for cloud deployments
        self.alternative_configs = []
        
        if self.offline_mode:
            print("Email service running in offline mode - emails will be logged only")
    
    def send_verification_email(self, to_email: str, verification_token: str) -> bool:
        """Send email verification with OTP/token"""
        subject = "Verify Your Email - Envoyou"
        verification_url = f"https://api.envoyou.com/auth/verify-email?token={verification_token}"
        
        html_content = f"""
        <html>
        <body>
            <h2>Welcome to Envoyou!</h2>
            <p>Please verify your email address by clicking the link below:</p>
            <a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a>
            <p>Or copy and paste this link into your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account, please ignore this email.</p>
        </body>
        </html>
        """
        
        return self._send_email(to_email, subject, html_content)
    
    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset email"""
        subject = "Reset Your Password - Envoyou"
        reset_url = f"https://api.envoyou.com/auth/reset-password?token={reset_token}"
        
        html_content = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You requested a password reset. Click the link below to reset your password:</p>
            <a href="{reset_url}" style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a>
            <p>Or copy and paste this link into your browser:</p>
            <p>{reset_url}</p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this reset, please ignore this email.</p>
        </body>
        </html>
        """
        
        return self._send_email(to_email, subject, html_content)
    
    def send_welcome_email(self, to_email: str, user_name: str) -> bool:
        """Send welcome email after successful registration"""
        subject = "Welcome to Envoyou! 🎉"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">Welcome to Envoyou!</h1>
                <p style="color: #e8e8e8; margin: 10px 0 0 0; font-size: 16px;">Your environmental data journey begins here</p>
            </div>
            <div style="background: white; padding: 40px 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h2 style="color: #333; margin-top: 0;">Hi {user_name}! 👋</h2>
                <p style="color: #666; line-height: 1.6; font-size: 16px;">
                    Thank you for joining Envoyou! We're excited to have you as part of our community 
                    dedicated to environmental data verification and compliance.
                </p>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #333; margin-top: 0;">What's Next?</h3>
                    <ul style="color: #666; padding-left: 20px;">
                        <li>Complete your email verification</li>
                        <li>Explore our comprehensive environmental data APIs</li>
                        <li>Generate your first API key for data access</li>
                        <li>Set up two-factor authentication for enhanced security</li>
                    </ul>
                </div>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://api.envoyou.com/docs" style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">Explore API Documentation</a>
                </div>
                <p style="color: #999; font-size: 14px; text-align: center; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                    Need help? Contact our support team at <a href="mailto:support@envoyou.com" style="color: #667eea;">support@envoyou.com</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(to_email, subject, html_content)
    
    def send_login_notification(self, to_email: str, user_name: str, login_time: str, ip_address: str, user_agent: str) -> bool:
        """Send login notification email for security"""
        subject = "🔐 New Login to Your Envoyou Account"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h2 style="color: #856404; margin: 0;">🔔 Login Notification</h2>
            </div>
            <div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="color: #333;">Hi {user_name},</h3>
                <p style="color: #666; line-height: 1.6;">
                    We detected a new login to your Envoyou account. If this was you, no action is needed.
                </p>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong>Login Details:</strong><br>
                    📅 Time: {login_time}<br>
                    🌐 IP Address: {ip_address}<br>
                    💻 Device: {user_agent[:100]}{'...' if len(user_agent) > 100 else ''}
                </div>
                <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong style="color: #721c24;">⚠️ Wasn't you?</strong><br>
                    <span style="color: #721c24;">If you didn't log in recently, please change your password immediately and contact our security team.</span>
                </div>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://api.envoyou.com/auth/change-password" style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Change Password</a>
                    <a href="https://api.envoyou.com/user/sessions" style="background-color: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">View Sessions</a>
                </div>
                <p style="color: #999; font-size: 12px; text-align: center;">
                    This is an automated security notification. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(to_email, subject, html_content)
    
    def send_api_key_created_notification(self, to_email: str, user_name: str, api_key_name: str, api_key_preview: str) -> bool:
        """Send notification when API key is created"""
        subject = "🔑 New API Key Created - Envoyou"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h2 style="color: #155724; margin: 0;">✅ API Key Created Successfully</h2>
            </div>
            <div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="color: #333;">Hi {user_name},</h3>
                <p style="color: #666; line-height: 1.6;">
                    A new API key has been created for your Envoyou account. Keep this key secure and never share it publicly.
                </p>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #28a745;">
                    <strong>API Key Details:</strong><br>
                    📝 Name: {api_key_name}<br>
                    🔑 Key: {api_key_preview}<br>
                    📅 Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong style="color: #856404;">🔒 Security Reminder:</strong><br>
                    <span style="color: #856404;">Store this API key securely. You can regenerate it anytime from your dashboard if compromised.</span>
                </div>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://api.envoyou.com/user/api-keys" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Manage API Keys</a>
                    <a href="https://api.envoyou.com/docs" style="background-color: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">API Documentation</a>
                </div>
                <p style="color: #999; font-size: 12px; text-align: center;">
                    This is an automated notification. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(to_email, subject, html_content)
    
    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email using SMTP with fallback configurations"""
        
        # If offline mode, just log the email
        if self.offline_mode:
            self._log_email(to_email, subject, html_content)
            return True
        
        # Try primary configuration first
        if self._try_send_email(to_email, subject, html_content, 
                               self.smtp_server, self.smtp_port, 
                               self.sender_email, self.sender_password):
            return True
        
        # Try alternative configurations
        for config in self.alternative_configs:
            if config.get("username") and config.get("password"):
                if self._try_send_email(to_email, subject, html_content,
                                       config["server"], config["port"],
                                       config["username"], config["password"]):
                    print(f"Email sent using alternative config: {config['server']}")
                    return True
        
        print("All email sending attempts failed")
        return False
    
    def _log_email(self, to_email: str, subject: str, content: str):
        """Log email content when in offline mode"""
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        log_entry = f"""
[{timestamp}] EMAIL LOG (OFFLINE MODE)
To: {to_email}
Subject: {subject}
Content: {content[:500]}...
{'(truncated)' if len(content) > 500 else ''}
"""
        print(log_entry)
        
        # Optionally save to file
        try:
            with open("email_log.txt", "a") as f:
                f.write(log_entry + "\n")
        except:
            pass
    
    def _try_send_email(self, to_email: str, subject: str, html_content: str, 
                       server: str, port: int, username: str, password: str) -> bool:
        """Try to send email with specific SMTP configuration"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email with timeout
            smtp_server = smtplib.SMTP(server, port, timeout=30)
            if self.use_tls:
                smtp_server.starttls()
            
            if password:
                smtp_server.login(username, password)
            
            smtp_server.sendmail(username, to_email, msg.as_string())
            smtp_server.quit()
            
            return True
            
        except smtplib.SMTPConnectError as e:
            print(f"SMTP connection failed to {server}:{port}: {e}")
            return False
        except smtplib.SMTPAuthenticationError as e:
            print(f"SMTP authentication failed for {username}: {e}")
            return False
        except smtplib.SMTPException as e:
            print(f"SMTP error: {e}")
            return False
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False
    
    def send_free_api_key_notification(self, to_email: str, user_name: str, api_key: str, key_prefix: str) -> bool:
        """Send free API key notification email"""
        try:
            subject = "Your Free API Key - Environmental Data API"
            
            html_content = f"""
            <html>
            <body>
                <h2>Welcome to Environmental Data Verification API!</h2>
                <p>Hi {user_name},</p>
                <p>Thank you for requesting a free API key! Here are your access details:</p>
                
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>Your API Key:</h3>
                    <p style="font-family: monospace; font-size: 14px; background-color: #e8e8e8; padding: 10px; border-radius: 3px;">
                        {api_key}
                    </p>
                    <p><strong>Key Prefix:</strong> {key_prefix}</p>
                </div>
                
                <p><strong>Important:</strong> Save this key securely. You won't be able to see it again.</p>
                
                <h3>How to use your API key:</h3>
                <ul>
                    <li>Include the key in your request headers: <code>Authorization: Bearer {api_key}</code></li>
                    <li>Or use query parameter: <code>?api_key={api_key}</code></li>
                </ul>
                
                <h3>Available endpoints:</h3>
                <ul>
                    <li><code>GET /permits</code> - Get all environmental permits</li>
                    <li><code>GET /global/emissions</code> - EPA emissions data</li>
                    <li><code>GET /global/eea</code> - EEA environmental indicators</li>
                    <li><code>GET /global/iso</code> - ISO 14001 certifications</li>
                </ul>
                
                <p>For complete documentation, visit: <a href="http://localhost:10000/docs">API Documentation</a></p>
                
                <p>If you have any questions, feel free to contact our support team.</p>
                
                <p>Best regards,<br>
                Environmental Data API Team</p>
            </body>
            </html>
            """
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            
            if self.sender_password:
                server.login(self.sender_email, self.sender_password)
            
            server.sendmail(self.sender_email, to_email, msg.as_string())
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Free API key email sending failed: {e}")
            return False

# Global email service instance
email_service = EmailService()
