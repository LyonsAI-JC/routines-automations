# routines-automations

Scheduled GitHub Actions that fetch external data for personal Claude routines.

Each routine lives in its own subfolder. Workflows are at `.github/workflows/`
(GitHub only discovers workflows there).

## Routines

### weekend-ride-checker/

Fetches Open-Meteo forecasts for ten Victorian locations across a 5-day window
(the upcoming weekend plus the three days before, used to assess road
conditions for semi-slick tyres) and commits the result to
`weekend-ride-checker/weather.json`. Locations cover the home origin
(Springvale), an urban reference (Melbourne), and riding destinations across
the Dandenongs, Yarra Ranges, Reefton Spur, Alpine, and High Country regions.

The Claude routine that consumes this JSON lives in
[`weekend-ride-checker/routine_prompt.md`](weekend-ride-checker/routine_prompt.md) —
edit that file when tuning behaviour. The routine fetches the JSON, assesses
road and riding conditions, checks Google Calendar (Friday + weekend) for
availability and night-before social events, and drafts a styled Gmail report
when conditions warrant a ride.
