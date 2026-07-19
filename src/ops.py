import json
import logging
import os
import urllib.request


logger = logging.getLogger(__name__)


def send_alert(event, message, **details):
    url = os.getenv("OPS_ALERT_WEBHOOK_URL", "").strip()
    if not url:
        logger.warning("ops_alert event=%s message=%s", event, message)
        return
    payload = json.dumps({"event": event, "message": message, "details": details}, ensure_ascii=False).encode("utf-8")
    try:
        request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(request, timeout=5).read()
    except Exception:
        logger.exception("ops_alert_delivery_failed event=%s", event)
