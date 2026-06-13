from curl_cffi import requests
import re
from html import unescape
from datetime import datetime

BASE_URL = "https://www.dolceclock.com"


def run(headers, user_input):
    """Load weekly schedule for a location."""
    base_url = BASE_URL

    loc_id = user_input.get("location_id", "104132882")

    # Date format: "Mon DD, YYYY" or accept YYYY-MM-DD and convert
    date_str = user_input.get("date", "")
    if date_str and re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        date_str = dt.strftime("%b %d, %Y")

    by_role = user_input.get("by_role", False)

    params = {
        "action": "loccontents-ajax",
        "loc_id": str(loc_id),
        "headers": "false",
        "sticky": "1",
    }
    if by_role:
        params["byRole"] = "1"
    else:
        params["byEmployee"] = "1"

    if date_str:
        params["dashboard"] = "1"
        params["datestr"] = date_str

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

    schedule = _parse_schedule(html)

    return {"status_code": 200, "body": schedule}


def _parse_schedule(html):
    """Parse schedule data from HTML response."""
    result = {
        "location": "",
        "week_dates": [],
        "employees": [],
    }

    # Extract location name
    loc_match = re.search(r"class='loc_area_title[^']*'>(.*?)</span>", html)
    if loc_match:
        result["location"] = unescape(loc_match.group(1).strip())

    # Extract week dates from header
    date_matches = re.findall(
        r"popupShowDay\(this,\s*\d+,\s*\"(\d{4}-\d{2}-\d{2})\"\)",
        html,
    )
    if date_matches:
        result["week_dates"] = list(dict.fromkeys(date_matches))  # dedupe, preserve order

    # Extract employee rows with their shifts
    # Each employee has a TD with emp_id and then 7 day cells
    emp_sections = re.findall(
        r"href='preferences\.php\?emp_id=(\d+)'>(.*?)</a>.*?</td>(.*?)</tr>",
        html,
        re.DOTALL,
    )

    for emp_id, emp_name_raw, days_html in emp_sections:
        emp_name = re.sub(r"<[^>]+>", "", emp_name_raw).strip()
        emp_data = {
            "employee_id": emp_id,
            "name": unescape(emp_name),
            "shifts": [],
        }

        # Find shift boxes in this employee's row
        shifts = re.findall(
            r"id='shift-?(\d+)'[^>]*>.*?<span class='scheduled_range[^']*'>"
            r"<span[^>]*>([^<]+)</span>\s*-\s*<span[^>]*>([^<]+)</span>",
            days_html,
            re.DOTALL,
        )

        for shift_id, start_time, end_time in shifts:
            shift = {
                "shift_id": shift_id,
                "start_time": start_time.strip(),
                "end_time": end_time.strip(),
            }

            # Try to find the role for this shift
            role_match = re.search(
                rf"id='shift-?{shift_id}'.*?class='week_role[^']*'[^>]*>(.*?)</div>",
                days_html,
                re.DOTALL,
            )
            if role_match:
                shift["role"] = unescape(role_match.group(1).strip())

            # Try to find shift note
            note_match = re.search(
                rf"id=\"shift_note-{shift_id}\"[^>]*>(.*?)</span>",
                days_html,
                re.DOTALL,
            )
            if note_match:
                note = re.sub(r"<[^>]+>", "", note_match.group(1)).strip()
                note = note.lstrip("- ").strip()
                if note and note != "&nbsp;":
                    shift["note"] = unescape(note)

            emp_data["shifts"].append(shift)

        if emp_data["shifts"] or emp_data["name"] != "Unassigned":
            result["employees"].append(emp_data)

    return result
