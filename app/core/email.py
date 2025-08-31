"""
Email module for sending notifications to users.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import List, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Ensure INFO logs are visible

class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        """Initialize the email service with environment variables"""
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587")) # Default to 587 if not set
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@cancer-genix.com")
        
        # More robust boolean check for EMAIL_ENABLED
        email_enabled_str = os.getenv("EMAIL_ENABLED", "false").lower()
        self.enabled = email_enabled_str in ["true", "1", "t"]
        
        logger.info(f"EmailService initialized. SMTP Server: {self.smtp_server}, Port: {self.smtp_port}, Enabled: {self.enabled}")
        
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        cc_emails: Optional[List[str]] = None,
        plain_text: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Send an email to a recipient
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            cc_emails: Optional list of CC recipients
            plain_text: Optional plain text version of the email
            from_email: Optional custom from email (defaults to configured from_email)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        print(f"DEBUG: EmailService.send_email called with to_email: {to_email}, subject: {subject}")
        print(f"DEBUG: HTML content length: {len(html_content)} characters")
        print(f"DEBUG: HTML content preview: {html_content[:200]}...")
        print(f"DEBUG: EmailService status - Enabled: {self.enabled}, SMTP Server: {self.smtp_server}, Port: {self.smtp_port}")
        
        if not self.enabled:
            logger.info(f"Email sending disabled. Would have sent email to {to_email}")
            logger.debug(f"Subject: {subject}")
            logger.debug(f"Content: {html_content[:100]}...")
            print(f"DEBUG: Email sending disabled. Would have sent email to {to_email}")
            return True
            
        try:
            print(f"DEBUG: Creating email message to {to_email}")
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email or self.from_email  # Use custom from_email if provided
            msg['To'] = to_email
            
            if cc_emails:
                msg['Cc'] = ", ".join(cc_emails)
                
            # Add plain text if provided, otherwise create basic version from HTML
            if not plain_text:
                # Simple HTML stripping for plain text version
                plain_text = html_content.replace('<br>', '\n').replace('</p>', '\n\n').replace('</div>', '\n')
                plain_text = ''.join(c for c in plain_text if c not in '<>{}[]')
                
            # Attach parts
            part1 = MIMEText(plain_text, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            print(f"DEBUG: Connecting to SMTP server {self.smtp_server}:{self.smtp_port}")
            # Connect and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                print(f"DEBUG: Connected to SMTP server")
                
                # Only use STARTTLS if not using maildev (which doesn't support it)
                if 'maildev' not in self.smtp_server.lower() and 'mailhog' not in self.smtp_server.lower():
                    print(f"DEBUG: Starting TLS")
                    server.starttls()
                else:
                    print(f"DEBUG: Skipping STARTTLS for {self.smtp_server}")
                
                if self.smtp_username and self.smtp_password:
                    print(f"DEBUG: Logging in to SMTP server as {self.smtp_username}")
                    server.login(self.smtp_username, self.smtp_password)
                
                recipients = [to_email]
                if cc_emails:
                    recipients.extend(cc_emails)
                    
                print(f"DEBUG: Sending email from {self.from_email} to {recipients}")
                server.sendmail(self.from_email, recipients, msg.as_string())
                print(f"DEBUG: Email sent successfully")
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to send email to {to_email}: {str(e)}")
            import traceback
            print(f"ERROR: Traceback: {traceback.format_exc()}")
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_invite_email(self, to_email: str, patient_name: str, invite_url: str, 
                         provider_name: str = "Healthcare Provider", 
                         custom_message: str = None, organization_name: str = "Cancer-Genix",
                         clinician_name: str = None, expires_at: str = None, 
                         organization_domain: str = None) -> bool:
        """Send an email invitation to a patient"""
        try:
            # Generate organization-specific from email
            if organization_domain:
                org_from_email = f"noreply@{organization_domain}"
                print(f"DEBUG: Using organization domain email: {org_from_email}")
            else:
                org_from_email = self.from_email  # fallback to default
                print(f"DEBUG: Using default email: {org_from_email}")
            
            # Use organization name in both subject and from display name
            subject = f"{organization_name}: Your Invitation to Register"
            from_display = f"{organization_name} <{org_from_email}>"
            print(f"DEBUG: Email from display: {from_display}")
            print(f"DEBUG: Email subject: {subject}")
            
            # Use provided expiration date or calculate default
            if not expires_at:
                from datetime import datetime, timedelta
                expires_at = (datetime.now() + timedelta(days=14)).strftime("%B %d, %Y")
            
            # Use provided clinician name or default provider name
            doctor_name = clinician_name or provider_name
            
            # Build HTML email content
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2>{organization_name} Patient Portal Invitation</h2>
                <p>Hello {patient_name},</p>
                <p>You have been invited by {doctor_name} to join the {organization_name} Patient Portal.</p>
                
                <p>To complete your registration, please click the link below:</p>
                <p><a href="{invite_url}" style="display: inline-block; background-color: #4a90e2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Complete Registration</a></p>
                <p>Or copy and paste this URL into your browser: <br>{invite_url}</p>
                
                <p>This invitation link will expire on {expires_at}.</p>
            """
            
            if custom_message:
                html_content += f"""
                <div style="margin: 20px 0; padding: 15px; border-left: 4px solid #4a90e2; background-color: #f8f9fa;">
                    <p><strong>Message from {doctor_name}:</strong></p>
                    <p>{custom_message}</p>
                </div>
                """
                
            html_content += f"""
                <p>Thank you,</p>
                <p>The {organization_name} Team</p>
            </div>
            """
            
            result = self.send_email(to_email, subject, html_content, from_email=from_display)
            logger.debug(f"EmailService.send_invite_email result: {result}")
            return result
        
        except Exception as e:
            logger.error(f"Failed to send invite email to {to_email}: {str(e)}")
            return False

# Create global instance
email_service = EmailService()
