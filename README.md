# routines-automations

Scheduled GitHub Actions that fetch external data for personal Claude routines.

Each routine lives in its own subfolder. Workflows are at `.github/workflows/`
(GitHub only discovers workflows there).

## Routines

### weekend-ride-checker/

Fetches Open-Meteo forecasts for the upcoming Saturday and Sunday across
five Victorian locations (Melbourne, Springvale, Healesville, Jamieson,
Marysville) and commits the result to `weekend-ride-checker/weather.json`.

A separate Claude routine reads that JSON, checks the user's Google Calendar
for weekend availability, and drafts a Gmail report if conditions look good
for riding.
