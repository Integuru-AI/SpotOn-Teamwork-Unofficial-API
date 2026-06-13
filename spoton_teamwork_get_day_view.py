from curl_cffi import requests
import re
from html import unescape

BASE_URL = "https://www.dolceclock.com"


def run(headers, user_input):
    """Show day view (hourly schedule) for a location on a specific date."""
    base_url = BASE_URL

    loc_id = user_input.get("location_id", "104132882")

    date = user_input.get("date")
    if not date:
        from datetime import datetime as _dt
        date = _dt.now().strftime("%Y-%m-%d")

    params = {
        "action": "show-day-ajax",
        "loc_id": str(loc_id),
        "date": date,
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

    day_data = _parse_day_view(html)

    return {"status_code": 200, "body": day_data}


def _parse_day_view(html):
    """Parse day view HTML into structured data."""
    result = {
        "date": "",
        "location": "",
        "shifts": [],
        "clock_ins": [],
    }

    # Extract date
    date_match = re.search(r"id='schedule_date'\s*value='([^']+)'", html)
    if date_match:
        result["date"] = date_match.group(1)

    title_match = re.search(r"id='title_date'\s*value='([^']+)'", html)
    if title_match:
        result["title"] = title_match.group(1)

    # Extract location
    loc_match = re.search(r"@\s*(.*?)<", html)
    if loc_match:
        result["location"] = unescape(loc_match.group(1).strip())

    # Extract shift meters (visual timeline bars)
    shift_meters = re.findall(
        r"class='shift_time_meter'[^>]*id='meter-(\d+)'[^>]*"
        r"start='([^']*)'[^>]*end='([^']*)'[^>]*"
        r"startFull='([^']*)'[^>]*endFull='([^']*)'",
        html,
    )
    for shift_id, start, end, start_full, end_full in shift_meters:
        result["shifts"].append({
            "shift_id": shift_id,
            "start_time": start,
            "end_time": end,
            "start_full": start_full,
            "end_full": end_full,
        })

    # Alternative: parse shift info from other patterns
    if not result["shifts"]:
        shifts_alt = re.findall(
            r"id='shift-?(\d+)'[^>]*>.*?<span class='scheduled_range[^']*'>"
            r"<span[^>]*>([^<]+)</span>\s*-\s*<span[^>]*>([^<]+)</span>",
            html,
            re.DOTALL,
        )
        for shift_id, start, end in shifts_alt:
            shift = {
                "shift_id": shift_id,
                "start_time": start.strip(),
                "end_time": end.strip(),
            }
            # Find employee name nearby
            emp_match = re.search(
                rf"emp_id=(\d+).*?id='shift-?{shift_id}'",
                html,
                re.DOTALL,
            )
            if emp_match:
                shift["employee_id"] = emp_match.group(1)
            result["shifts"].append(shift)

    # Extract punch (clock-in) meters
    punch_meters = re.findall(
        r"class='punch_time_meter[^']*'[^>]*id='punch-(\d+)'[^>]*"
        r"start='([^']*)'[^>]*end='([^']*)'",
        html,
    )
    for punch_id, start, end in punch_meters:
        result["clock_ins"].append({
            "punch_id": punch_id,
            "start_time": start,
            "end_time": end,
        })

    return result
