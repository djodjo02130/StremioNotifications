# Stremio Notifications for Home Assistant

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fdjodjo02130%2FStremioNotifications)

Track your Stremio library and get notified of new releases via Home Assistant calendar events.

## Features

- Connects to your Stremio account and fetches your library (followed series & movies)
- Periodically checks release dates via Cinemeta (Stremio's metadata addon)
- Creates calendar events in Home Assistant when a release is upcoming
- Lets you build HA automations on those calendar events to send notifications (push, Telegram, email, etc.)

## Prerequisites

1. A **Stremio account** with series/movies in your library
2. A **Local Calendar** integration in Home Assistant:
   - Go to **Settings > Devices & Services > Add Integration > Local Calendar**
   - Create a calendar named `stremio_releases` (or any name you prefer)

## Installation

1. Click the button above, or manually add this repository URL in Home Assistant:
   **Settings > Add-ons > Add-on Store > ⋮ > Repositories**
   ```
   https://github.com/djodjo02130/StremioNotifications
   ```
2. Install the **Stremio Notifications** addon
3. Configure your Stremio credentials and options in the addon Configuration tab
4. Start the addon

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `stremio_email` | *(required)* | Your Stremio account email |
| `stremio_password` | *(required)* | Your Stremio account password |
| `check_interval_hours` | `6` | How often to check for new releases (1-168h) |
| `calendar_entity` | `calendar.stremio_releases` | HA calendar entity to create events in |
| `days_ahead` | `14` | How many days ahead to look for upcoming releases (1-90) |
| `content_types` | `series, movies` | Types of content to track |
| `log_level` | `info` | Log verbosity (`debug`, `info`, `warning`, `error`) |

## Example Automation

Once events appear in your calendar, create an automation to get notified:

```yaml
automation:
  - alias: "Stremio Release Notification"
    trigger:
      - platform: calendar
        event: start
        entity_id: calendar.stremio_releases
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "{{ trigger.calendar_event.summary }}"
          message: "{{ trigger.calendar_event.description }}"
```

## How It Works

```
Stremio API            Cinemeta API           Home Assistant
(auth + library)       (metadata/dates)       (calendar events)
      |                      |                       |
      v                      v                       v
+----------------------------------------------------------+
|              Stremio Notifications Addon                  |
|                                                          |
|  1. Login to Stremio & fetch your library                |
|  2. Query Cinemeta for upcoming release dates            |
|  3. Create HA calendar events for new releases           |
|  4. Repeat every N hours                                 |
+----------------------------------------------------------+
```
