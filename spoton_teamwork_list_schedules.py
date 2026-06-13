import re
from datetime import datetime, timedelta
from curl_cffi import requests


def run(headers, user_input):
    """List weekly schedule shifts (employee, role, location, date, start/end time)."""
    base_url = BASE_URL

    # Parse week_start_date input (YYYY-MM-DD) or default to current week's Monday
    week_start_date = user_input.get("week_start_date")
    if week_start_date:
        try:
            dt = datetime.strptime(week_start_date, "%Y-%m-%d")
        except ValueError:
            return {"status_code": 400, "body": {"error": "week_start_date must be in YYYY-MM-DD format"}}
        # Find the Monday of that week
        monday = dt - timedelta(days=dt.weekday())
    else:
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())

    # Format datestr as "Mon DD, YYYY" for the API (e.g. "May 25, 2026")
    datestr = monday.strftime("%b %d, %Y").replace(" 0", " ")

    # Build request headers
    req_headers = {
        "Cookie": headers.get("Cookie", ""),
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "text/html, */*; q=0.01",
        "Referer": f"{base_url}/public/?_company_id=7330",
    }

    location_id = user_input.get("location_id")

    if location_id:
        # Fetch single location
        locations = [{"id": location_id, "name": None}]
    else:
        # Fetch main schedule page to discover locations
        page_resp = requests.get(
            f"{base_url}/public/?_company_id=7330",
            headers={"Cookie": headers.get("Cookie", "")},
            impersonate="chrome131",
            timeout=30,
        )
        if not page_resp.text or "login" in page_resp.url and "company_id" not in page_resp.url:
            return {"status_code": 401, "body": {"error": "Session expired"}}

        # Extract location options from the page
        loc_matches = re.findall(r"value='(\d+)'>([^<]+)</option>", page_resp.text)
        if not loc_matches:
            return {"status_code": 500, "body": {"error": "Could not find locations on schedule page"}}
        locations = [{"id": m[0], "name": m[1]} for m in loc_matches]

    # Fetch schedule for each location
    all_locations = []
    for loc in locations:
        loc_id = loc["id"]
        resp = requests.get(
            f"{base_url}/public/assets/inc/update.inc.php",
            params={
                "action": "loccontents-ajax",
                "loc_id": loc_id,
                "dashboard": "1",
                "datestr": datestr,
                "byEmployee": "1",
            },
            headers=req_headers,
            impersonate="chrome131",
            timeout=30,
        )

        # Empty body means session expired
        if not resp.text or len(resp.text.strip()) == 0:
            return {"status_code": 401, "body": {"error": "Session expired"}}

        html = resp.text

        # Extract location name from the response if not already known
        loc_name = loc["name"]
        if not loc_name:
            name_match = re.search(r"class='loc_area_title[^']*'>(.*?)</span>", html)
            loc_name = name_match.group(1).strip() if name_match else f"Location {loc_id}"

        # Extract week dates from column headers
        dates = re.findall(r'popupShowDay\(this, \d+, "(\d{4}-\d{2}-\d{2})"\)', html)
        week_dates = dates[:7]

        # Parse shifts per employee
        shifts = []
        emp_sections = re.split(r"(?=<tr[^>]*id='emp_)", html)

        for section in emp_sections:
            # Get employee ID and name
            emp_id_match = re.search(r"id='emp_(\d+)'", section)
            if not emp_id_match:
                continue
            emp_id = emp_id_match.group(1)

            name_match = re.search(r"href='preferences\.php\?emp_id=\d+'>([^<]+)", section)
            emp_name = name_match.group(1).strip() if name_match else "Unknown"

            # Find day cells with shifts - each has data-testid ending in day_N
            # Split by day cells
            day_cells = re.findall(
                r'data-testid="[^"]*day_(\d+)"[^>]*class="emp-shifts"[^>]*>(.*?)(?=</ul>)',
                section,
                re.DOTALL,
            )

            for day_num, cell_content in day_cells:
                day_idx = int(day_num) - 1
                if day_idx >= len(week_dates):
                    continue
                shift_date = week_dates[day_idx]

                # Extract individual shifts from the cell
                shift_matches = re.findall(
                    r"id='shift-?(\d+)'.*?<span ?>([\d:]+[ap]m)</span>\s*-\s*<span[^>]*>([\w:]+[ap]?m?|EOB)</span>.*?week_role[^']*'>(.*?)</div>",
                    cell_content,
                    re.DOTALL,
                )

                for shift_id, start_time, end_time, role in shift_matches:
                    # Convert 12h times to 24h format
                    start_24 = _convert_to_24h(start_time)
                    end_24 = _convert_to_24h(end_time) if end_time != "EOB" else "EOB"

                    shifts.append({
                        "shift_id": shift_id,
                        "employee_id": emp_id,
                        "employee_name": emp_name,
                        "role": role.strip(),
                        "date": shift_date,
                        "start_time": start_24,
                        "end_time": end_24,
                    })

        all_locations.append({
            "location_id": loc_id,
            "location_name": loc_name,
            "shifts": shifts,
        })

    # Compute week range
    week_end = monday + timedelta(days=6)

    return {
        "status_code": 200,
        "body": {
            "week_start": monday.strftime("%Y-%m-%d"),
            "week_end": week_end.strftime("%Y-%m-%d"),
            "locations": all_locations,
        },
    }


# === PRIVATE ===


def _convert_to_24h(time_str):
    """Convert '2:00pm' or '10:00am' to 'HH:MM' 24h format."""
    if not time_str or time_str == "EOB":
        return time_str
    try:
        # Handle formats like "2:00pm", "10:00am"
        time_str = time_str.lower().strip()
        dt = datetime.strptime(time_str, "%I:%M%p")
        return dt.strftime("%H:%M")
    except ValueError:
        return time_str
