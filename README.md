# Keyword Frequency Monitor

An early Python project for keyword-frequency monitoring, scheduled automation, and notification workflows using public web catalog data.

The project is designed to run as a lightweight scheduled check. In the original deployment, an external Telegram bot was used to notify the user, and an external cron service at https://console.cron-job.org/ was used as the worker/scheduler to keep the monitor running continuously by triggering the GitHub Actions workflow.

## What It Does

- Fetches public catalog data from a JSON endpoint.
- Counts occurrences of a target keyword across thread subjects and comments.
- Compares the count against a configurable threshold.
- Sends notifications when the threshold is met or exceeded.
- Uses a cooldown file to avoid repeated alerts within a short window.

## Repository Contents

- Main Python script - Fetches catalog data, counts keyword occurrences, and sends alerts.
- `.github/workflows/main.yml` - GitHub Actions workflow that runs the monitor.

There are no placeholder services or mock components in this repository. The monitor expects real notification credentials to be provided through environment variables or GitHub Actions secrets.

## Configuration

The monitor is configured with environment variables:

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | Yes | None | Telegram bot token used to send chat messages. |
| `TELEGRAM_CHAT_ID` | Yes | None | Telegram chat ID that receives alerts. |
| `PUSHOVER_USER_KEY` | Yes | None | Pushover user key for emergency alerts. |
| `PUSHOVER_APP_TOKEN` | Yes | None | Pushover application token. |
| `KEYWORD` | No | `happening` | Keyword to count in the catalog. |
| `THRESHOLD` | No | `25` | Minimum keyword count required to send an alert. |
| `WHOLE_WORD` | No | `0` | Set to `1` to count whole-word matches only. |

## Usage

Run the monitor locally:

```bash
TELEGRAM_BOT_TOKEN="your-token" \
TELEGRAM_CHAT_ID="your-chat-id" \
PUSHOVER_USER_KEY="your-user-key" \
PUSHOVER_APP_TOKEN="your-app-token" \
KEYWORD="happening" \
THRESHOLD="25" \
python3 path/to/monitor_script.py
```

On Windows PowerShell:

```powershell
$env:TELEGRAM_BOT_TOKEN = "your-token"
$env:TELEGRAM_CHAT_ID = "your-chat-id"
$env:PUSHOVER_USER_KEY = "your-user-key"
$env:PUSHOVER_APP_TOKEN = "your-app-token"
$env:KEYWORD = "happening"
$env:THRESHOLD = "25"
python path\to\monitor_script.py
```

## GitHub Actions Deployment

The included workflow runs the script on demand through `workflow_dispatch`. Required secrets should be configured in the GitHub repository settings:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `PUSHOVER_USER_KEY`
- `PUSHOVER_APP_TOKEN`

The workflow also restores and saves `.last_alarm` through the GitHub Actions cache so alert cooldown state can persist between runs.

To run continuously, use an external scheduler such as https://console.cron-job.org/ to trigger the workflow at the desired interval. For example, the scheduler can call the GitHub Actions workflow dispatch API on a fixed schedule, while GitHub Actions performs the actual script execution.

## Methodology

The script downloads public catalog JSON data from a configured endpoint.

It then combines each catalog item's subject field and comment/snippet field into a single searchable text block. Keyword matching is case-insensitive.

By default, matching uses substring counts. For example, `war` would also match inside a longer word. Set `WHOLE_WORD=1` to use regular-expression whole-word matching instead.

When the count is greater than or equal to `THRESHOLD`, the script sends:

- A Pushover emergency alert.
- A Telegram message.

After an alert, the script writes the current timestamp to `.last_alarm`. Alerts are suppressed for 60 minutes after the last alarm.

## Limitations and Disclaimers

- This project depends on a public JSON catalog endpoint. Availability, response format, and rate limits may change outside this repository's control.
- The monitor only checks the catalog URL configured in the script.
- Counts are based on catalog subject and comment/snippet data, not full source contents.
- Substring matching can produce false positives unless `WHOLE_WORD=1` is enabled.
- The script does not classify, verify, or interpret posts. It only counts text occurrences.
- Notification delivery depends on external Telegram, Pushover, GitHub Actions, and scheduler availability.
- This repository is for monitoring public keyword frequency only. Use responsibly and comply with the terms and policies of any third-party services involved.
