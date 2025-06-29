import smtplib
import requests
from typing import Optional, Dict


def send_alert(message: str, alerts_cfg: Optional[Dict] = None) -> None:
    """Send an alert using email or a webhook."""
    if alerts_cfg is None:
        from .utils import load_config
        alerts_cfg = load_config().get("alerts", {})
    method = alerts_cfg.get("method")
    if method == "email":
        server = alerts_cfg.get("smtp_server")
        port = alerts_cfg.get("smtp_port", 587)
        user = alerts_cfg.get("smtp_user")
        password = alerts_cfg.get("smtp_password")
        to_addr = alerts_cfg.get("email_to")
        if server and user and password and to_addr:
            try:
                with smtplib.SMTP(server, port) as s:
                    s.starttls()
                    s.login(user, password)
                    s.sendmail(user, to_addr, message)
            except Exception:
                pass
    elif method == "webhook":
        url = alerts_cfg.get("webhook_url")
        if url:
            try:
                requests.post(url, json={"text": message}, timeout=10)
            except Exception:
                pass
