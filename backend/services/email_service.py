"""
Email notification service
"""
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    """Email notification service using SMTP"""

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.from_name = os.getenv("FROM_NAME", "EnerSight Alerts")

        # Check if email is configured
        self.is_configured = bool(self.smtp_username and self.smtp_password)
        if not self.is_configured:
            logger.warning(
                "Email alerts disabled: SMTP_USERNAME and SMTP_PASSWORD are not set in .env"
            )
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None
    ) -> bool:
        """
        Send an email notification
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_text: Plain text email body
            body_html: HTML email body (optional)
        
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.is_configured:
            logger.warning(
                "Email not configured (SMTP_USERNAME/SMTP_PASSWORD missing) — "
                f"dropped email to {to_email}: {subject}"
            )
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Date'] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
            
            # Attach text and HTML parts
            part1 = MIMEText(body_text, 'plain')
            msg.attach(part1)
            
            if body_html:
                part2 = MIMEText(body_html, 'html')
                msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_threshold_alert(
        self,
        to_email: str,
        username: str,
        current_value: float,
        threshold_value: float,
        timestamp: datetime
    ) -> bool:
        """Send threshold exceeded alert email"""
        subject = "⚠️ Energy Consumption Alert - Threshold Exceeded"
        
        body_text = f"""
Hello {username},

Your energy consumption has exceeded the configured threshold.

Current Consumption: {current_value:.2f} kWh
Threshold: {threshold_value:.2f} kWh
Exceeded by: {(current_value - threshold_value):.2f} kWh ({((current_value - threshold_value) / threshold_value * 100):.1f}%)
Time: {timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}

Please review your energy usage in the EnerSight dashboard to identify high consumption sources.

Best regards,
EnerSight Team
        """.strip()
        
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-top: none; }}
        .alert-box {{ background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .metrics {{ background: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
        .metric-label {{ font-size: 12px; color: #666; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
        .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
        .btn {{ background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0;">⚠️ Energy Alert</h2>
            <p style="margin: 5px 0 0 0;">Threshold Exceeded</p>
        </div>
        <div class="content">
            <p>Hello <strong>{username}</strong>,</p>
            
            <div class="alert-box">
                <strong>⚠️ Your energy consumption has exceeded the configured threshold.</strong>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">Current Consumption</div>
                    <div class="metric-value">{current_value:.2f} kWh</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Threshold</div>
                    <div class="metric-value">{threshold_value:.2f} kWh</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Exceeded By</div>
                    <div class="metric-value" style="color: #f44336;">{(current_value - threshold_value):.2f} kWh</div>
                </div>
            </div>
            
            <p><strong>Percentage Over Threshold:</strong> {((current_value - threshold_value) / threshold_value * 100):.1f}%</p>
            <p><strong>Time:</strong> {timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
            
            <p>Please review your energy usage in the EnerSight dashboard to identify high consumption sources.</p>
            
            <a href="http://localhost:3000/dashboard" class="btn">View Dashboard</a>
        </div>
        <div class="footer">
            <p>This is an automated alert from EnerSight Energy Monitoring System.</p>
            <p>To adjust your alert settings, visit your preferences page.</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return self.send_email(to_email, subject, body_text, body_html)
    
    def send_test_email(self, to_email: str, username: str) -> bool:
        """Send an on-demand test email to verify the notification pipeline."""
        subject = "✉️ EnerSight Test Email"
        sent_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        body_text = f"""
Hello {username},

This is a test email from EnerSight, sent on demand from the dashboard.

If you are reading this, email notifications are working correctly.

Sent at: {sent_at}

Best regards,
EnerSight Team
        """.strip()

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-top: none; }}
        .ok-box {{ background: #ecfdf5; border: 1px solid #10b981; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0;">✉️ Test Email</h2>
            <p style="margin: 5px 0 0 0;">Notification pipeline check</p>
        </div>
        <div class="content">
            <p>Hello <strong>{username}</strong>,</p>
            <div class="ok-box">
                <strong>✅ Email notifications are working correctly.</strong>
            </div>
            <p>This test email was sent on demand from the EnerSight dashboard.</p>
            <p><strong>Sent at:</strong> {sent_at}</p>
        </div>
        <div class="footer">
            <p>This is a test message from EnerSight Energy Monitoring System.</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        return self.send_email(to_email, subject, body_text, body_html)

    def send_anomaly_alert(
        self,
        to_email: str,
        username: str,
        anomaly_score: float,
        timestamp: datetime
    ) -> bool:
        """Send anomaly detection alert email"""
        subject = "🚨 Anomaly Detected in Energy Consumption"
        
        body_text = f"""
Hello {username},

An unusual pattern has been detected in your energy consumption.

Anomaly Score: {anomaly_score:.2f}
Time: {timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}

This could indicate unexpected energy usage or equipment malfunction. Please review your dashboard for details.

Best regards,
EnerSight Team
        """.strip()
        
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #f44336 0%, #e91e63 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-top: none; }}
        .alert-box {{ background: #ffebee; border: 1px solid #f44336; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .btn {{ background: #f44336; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }}
        .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0;">🚨 Anomaly Alert</h2>
            <p style="margin: 5px 0 0 0;">Unusual Pattern Detected</p>
        </div>
        <div class="content">
            <p>Hello <strong>{username}</strong>,</p>
            
            <div class="alert-box">
                <strong>🚨 An unusual pattern has been detected in your energy consumption.</strong>
            </div>
            
            <p><strong>Anomaly Score:</strong> {anomaly_score:.2f}</p>
            <p><strong>Time:</strong> {timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
            
            <p>This could indicate unexpected energy usage or equipment malfunction. Please review your dashboard for details.</p>
            
            <a href="http://localhost:3000/anomalies" class="btn">View Anomalies</a>
        </div>
        <div class="footer">
            <p>This is an automated alert from EnerSight Energy Monitoring System.</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return self.send_email(to_email, subject, body_text, body_html)


# Singleton instance
email_service = EmailService()
