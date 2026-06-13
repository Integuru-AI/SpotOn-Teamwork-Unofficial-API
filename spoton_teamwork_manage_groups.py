from curl_cffi import requests
import re
from html import unescape

BASE_URL = "https://www.dolceclock.com"


def run(headers, user_input):
    """Manage employee groups - view groups and toggle settings."""
    base_url = BASE_URL

    action_type = user_input.get("action_type", "get")

    if action_type == "get":
        return _get_groups(base_url, headers, user_input)
    elif action_type == "force_role":
        return _force_role(base_url, headers, user_input)
    else:
        return {"status_code": 400, "body": {"error": "action_type must be 'get' or 'force_role'"}}


def _get_groups(base_url, headers, user_input):
    """Get groups data."""
    params = {
        "action": "groups-ajax",
    }

    response = requests.get(
        f"{base_url}/public/assets/inc/update.inc.php",
        params=params,
        headers={
            "Cookie": headers.get("Cookie", ""),
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{base_url}/public/?_company_id=7330",
        },
        impersonate="chrome131",
        timeout=30,
    )

    if response.status_code != 200:
        return {"status_code": response.status_code, "body": {"error": "Request failed"}}

    html = response.text

    if "<!DOCTYPE" in html[:20] or "login.php" in html[:200]:
        return {"status_code": 401, "body": {"error": "Session expired"}}

    return {"status_code": 200, "body": {"success": True, "groups": html[:3000]}}


def _force_role(base_url, headers, user_input):
    """Toggle force_role setting for groups."""
    enabled = user_input.get("enabled", True)

    params = {
        "action": "groups-ajax",
        "force_role": "1" if enabled else "0",
    }

    response = requests.get(
        f"{base_url}/public/assets/inc/update.inc.php",
        params=params,
        headers={
            "Cookie": headers.get("Cookie", ""),
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{base_url}/public/?_company_id=7330",
        },
        impersonate="chrome131",
        timeout=30,
    )

    if response.status_code != 200:
        return {"status_code": response.status_code, "body": {"error": "Request failed"}}

    html = response.text

    if "<!DOCTYPE" in html[:20] or "login.php" in html[:200]:
        return {"status_code": 401, "body": {"error": "Session expired"}}

    return {"status_code": 200, "body": {"success": True, "force_role": enabled}}
