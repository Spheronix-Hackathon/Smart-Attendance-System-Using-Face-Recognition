from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

from ..config import settings


_LAST_MAIL_ERROR: str | None = None


def get_last_mail_error() -> str | None:
    return _LAST_MAIL_ERROR


def _set_last_mail_error(value: str | None) -> None:
    global _LAST_MAIL_ERROR
    _LAST_MAIL_ERROR = value


def _frontend_url(path: str = "") -> str:
    base_url = (settings.frontend_base_url or "").rstrip("/")
    suffix = path.lstrip("/")
    if suffix:
        return f"{base_url}/{suffix}"
    return base_url


def _get_premium_template(title: str, content: str, action_text: str = None, action_url: str = None) -> str:
    """Returns a premium, glassmorphic 'Deep Space' HTML email template."""
    action_button = f"""
        <div style="margin: 40px 0; text-align: center;">
            <a href="{action_url}" style="background: linear-gradient(135deg, #00d1c7 0%, #6f45ff 100%); color: #ffffff; padding: 16px 32px; border-radius: 12px; text-decoration: none; font-weight: 800; font-size: 0.9rem; letter-spacing: 2px; box-shadow: 0 10px 20px rgba(0, 209, 199, 0.2); display: inline-block;">{action_text}</a>
        </div>
    """ if action_text and action_url else ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
    </head>
    <body style="margin: 0; padding: 0; background-color: #020617; font-family: 'Inter', -apple-system, sans-serif;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #020617; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 24px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);">
                        <tr>
                            <td height="8" style="background: linear-gradient(90deg, #00d1c7 0%, #6f45ff 100%);"></td>
                        </tr>
                        <tr>
                            <td style="padding: 60px 40px;">
                                <div style="margin-bottom: 40px;">
                                    <span style="color: #ffffff; font-size: 1.5rem; font-weight: 900; letter-spacing: -0.5px;">SmartFace <span style="color: #00d1c7;">HUB</span></span>
                                </div>
                                <h1 style="color: #ffffff; font-size: 2rem; font-weight: 900; margin-bottom: 24px; line-height: 1.2; letter-spacing: -1px;">{title}</h1>
                                <div style="color: #94a3b8; font-size: 1.1rem; line-height: 1.6; margin-bottom: 32px;">
                                    {content}
                                </div>
                                {action_button}
                                <div style="margin-top: 60px; padding-top: 40px; border-top: 1px solid rgba(255, 255, 255, 0.05);">
                                    <p style="color: #475569; font-size: 0.8rem; line-height: 1.6; margin: 0;">
                                        This is a secure automated notification from the Smart Attendance System Using Face Recognition platform. If you did not expect this communication, please contact your systems administrator immediately.
                                    </p>
                                </div>
                            </td>
                        </tr>
                        <tr>
                            <td style="background-color: rgba(0, 0, 0, 0.2); padding: 24px 40px; text-align: center;">
                                <p style="color: #475569; font-size: 0.75rem; margin: 0; font-weight: 600; letter-spacing: 1px;">
                                    &copy; 2026 Smart Attendance System Using Face Recognition &bull; DEEP_SPACE_PROTOCOLS v2.0
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def _send_email_sync(recipient: str, subject: str, text_body: str, html_body: str = None) -> bool:
    if not settings.mail_enabled:
        _set_last_mail_error("mail_disabled")
        # In local/demo mode we intentionally skip SMTP sends.
        # OTP is already printed by send_otp_email, so avoid extra noisy logs.
        return False

    if not settings.mail_username or not settings.mail_password or not settings.mail_from:
        _set_last_mail_error("mail_not_configured")
        print(f"[MAIL:FALLBACK] {recipient} | {subject} | {text_body}")
        return False

    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(text_body)
    
    if html_body:
        message.add_alternative(html_body, subtype="html")

    timeout_seconds = 8
    try:
        if settings.mail_ssl_tls:
            with smtplib.SMTP_SSL(settings.mail_server, settings.mail_port, timeout=timeout_seconds) as client:
                if settings.use_credentials:
                    client.login(settings.mail_username, settings.mail_password)
                client.send_message(message)
        else:
            with smtplib.SMTP(settings.mail_server, settings.mail_port, timeout=timeout_seconds) as client:
                if settings.mail_starttls:
                    client.starttls()
                if settings.use_credentials:
                    client.login(settings.mail_username, settings.mail_password)
                client.send_message(message)
        _set_last_mail_error(None)
        return True
    except Exception as exc:
        error_text = str(exc)
        if "5.4.5" in error_text or "Daily user sending limit exceeded" in error_text:
            _set_last_mail_error("quota_exceeded")
            print(f"[MAIL:QUOTA] {recipient} | {subject} | {exc}")
        else:
            _set_last_mail_error("smtp_error")
            print(f"[MAIL:ERROR] {recipient} | {subject} | {exc}")
        return False


async def send_email(recipient: str, subject: str, text_body: str, html_body: str = None) -> bool:
    try:
        return await asyncio.to_thread(_send_email_sync, recipient, subject, text_body, html_body)
    except Exception as exc:
        _set_last_mail_error("smtp_error")
        print(f"[MAIL:FALLBACK] {recipient} | {subject} | {text_body} | reason={exc}")
        return False


async def send_otp_email(email: str, otp: str) -> bool:
    # High-visibility logging for development/troubleshooting
    print("\n" + "="*50)
    print(f" OTP FOR {email}: {otp} ")
    print("="*50 + "\n")
    
    title = "Verification Code"
    content = f"Your secure verification code is below. This sequence will expire in 10 minutes for your security."
    otp_display = f'<div style="background: rgba(0, 209, 199, 0.1); color: #00d1c7; font-size: 2.5rem; font-weight: 900; letter-spacing: 8px; padding: 24px; border-radius: 12px; text-align: center; border: 1px solid rgba(0, 209, 199, 0.2); font-family: monospace; margin: 32px 0;">{otp}</div>'
    
    html = _get_premium_template(title, f"{content}{otp_display}")
    return await send_email(email, f"Smart Attendance System Using Face Recognition - {title}", f"Your verification code is: {otp}", html)


async def send_registration_success(email: str) -> bool:
    title = "Registration Successful"
    content = "Welcome to the future of biometric attendance. Your student account has been successfully initialized and synchronized with the Smart Attendance System Using Face Recognition platform."
    html = _get_premium_template(title, content)
    return await send_email(email, f"Smart Attendance System Using Face Recognition - {title}", content, html)


async def send_password_changed(email: str) -> bool:
    title = "Security Alert: Password Updated"
    content = "Your account password was recently updated via the security terminal. If you did not authorize this action, your account may be compromised. Please lock your account and contact your administrator immediately."
    html = _get_premium_template(title, content, "PROTECT_ACCOUNT", "#")
    return await send_email(email, f"Smart Attendance System Using Face Recognition - {title}", content, html)


async def send_absent_notice(email: str, student_name: str, date_label: str) -> bool:
    title = "Attendance Notification"
    name = student_name or 'Student'
    content = f"Hello {name},<br><br>This is an automated telemetry report to inform you that your presence was <b>not detected</b> during the scheduled session on <b>{date_label}</b>. If this is a mismatch, please submit a synchronization request to your teacher."
    html = _get_premium_template(title, content, "VIEW_HISTORY", f"{_frontend_url('user_dashboard.html')}#attendance-history")
    return await send_email(email, f"Smart Attendance System Using Face Recognition - {title}", f"Notification: You were marked absent on {date_label}.", html)

