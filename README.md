# SpotOn Teamwork Unofficial API

Unofficial Python integrations for SpotOn Teamwork.

## Integrations

- `spoton_teamwork_list_schedules.py` - `list_schedules`.
- `spoton_teamwork_get_schedule.py` - `get_schedule`.
- `spoton_teamwork_manage_groups.py` - `manage_groups`.
- `spoton_teamwork_get_day_view.py` - `get_day_view`.

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

This unofficial API is built by [Integuru](https://integuru.com).

For custom requests or hosted authentication, contact richard@integuru.com or [schedule time with us](https://calendly.com/d/cqb8-d9x-nbf/integuru).

See the [complete list of APIs by Integuru](https://github.com/Integuru-AI/APIs-by-Integuru).
