# SpotOn Teamwork Unofficial API

Unofficial Python integrations for SpotOn Teamwork.

## Integrations

- `spoton_teamwork_list_schedules.py` - `list_schedules` (666 live events).
- `spoton_teamwork_get_schedule.py` - `get_schedule` (3 live events).
- `spoton_teamwork_manage_groups.py` - `manage_groups` (1 live events).
- `spoton_teamwork_get_day_view.py` - `get_day_view` (1 live events).

## Usage

Each file exposes a `run(input, context)` entrypoint. The runtime is expected to provide:

- `input`: integration-specific request fields.
- `context["headers"]`: authenticated request headers when required.
- `context["base_url"]`: the platform base URL when overriding the default.

Install dependencies:

```bash
pip install -r requirements.txt
```

## Info

This unofficial API is built by [Integuru.ai](https://integuru.ai/).

For custom requests or hosted authentication, contact richard@taiki.online.

See the [complete list of APIs by Integuru](https://github.com/Integuru-AI/APIs-by-Integuru).
