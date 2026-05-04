# Weekend Ride Routine — Prompt

This is the prompt John runs (via `/schedule` or manually) in a Claude session
that has the Google Calendar and Gmail MCPs connected. It consumes the
`weather.json` produced by this repo's GitHub Action and decides whether to
draft a riding report email.

Edit this file directly when tuning behaviour — it's the canonical version.

---

This routine's purpose is to alert John if the weekend looks like it'll be a good time for riding or not.

BIKE CONTEXT: superbike on semi-slick tyres. Slicks need warmth and DRY roads to
grip safely — wet/damp surfaces and cold temps are non-negotiable disqualifiers.
Road condition is the dominant factor; weather quality is secondary.

LOCATION ROLES:
- 🏠 Origin (home): Springvale — bike lives here. If Springvale roads are wet
  or damp the bike can't safely leave the garage, regardless of destination
  conditions. Springvale's road status is a HARD GATE.
- 🏙️ Reference (urban): Melbourne — included for city/route context only, not
  a ride destination.
- 🛣️ Destinations, by region:
    · Dandenongs:   Gembrook
    · Yarra Ranges: Healesville, Warburton, Mount Donna Buang
    · Reefton Spur (the road itself, between Marysville and Warburton)
    · Alpine:       Marysville, Lake Mountain
    · High Country: Jamieson
  Best-ride selection draws from these eight only.

ALTITUDE NOTE: Lake Mountain (~1480m), Mount Donna Buang (~1245m), and Reefton
Spur sit high enough that the temperature_2m_min < 8°C disqualifier will
naturally filter them out for much of autumn/winter/spring. That's intended —
slicks won't grip cold tarmac, especially at altitude where road surface
temperature runs cooler than air.

────────────────────────────────────────────────────────────────────────

1. Fetch the latest forecast from
   https://raw.githubusercontent.com/LyonsAI-JC/routines-automations/main/weekend-ride-checker/weather.json?cb=<current-unix-timestamp>
   The cache-buster avoids the 5-min CDN cache. The JSON covers all ten locations
   for a 5-day window: three days BEFORE the weekend (`prior_days` = Wed/Thu/Fri)
   plus Saturday and Sunday (`weekend`). Each location's `daily.time` array lines
   up with all daily field arrays — match by date when slicing prior vs weekend.

2. Assess EXPECTED ROAD CONDITIONS first (this is the dominant factor for slicks).
   Per location, from the prior 3 days:
   - moisture_in  = sum(precipitation_sum) over prior 3 days
   - moisture_out = sum(et0_fao_evapotranspiration) over prior 3 days
   - net = moisture_in - moisture_out
     * net > +5mm AND mean(humidity) > 70%  → 🌧️ WET
     * net between -5 and +5mm               → 💧 DAMP
     * net < -5mm OR mean(humidity) < 50%    → ☀️ DRY
   - If rain falls ON the weekend day itself, override to WET.
   Mountain and forest roads hold moisture longer than urban. The Yarra Ranges
   (Healesville, Warburton, Mt Donna Buang, Reefton Spur, Marysville, Lake
   Mountain) and Dandenongs (Gembrook) stay damp noticeably longer than
   Springvale/Melbourne; alpine ridges (Lake Mountain, Mt Donna Buang) longer
   still. Jamieson is high country but open and drier than the rainforest
   ranges. Lean one step wetter for ranges/alpine when calling close ones.

3. Assess RIDING CONDITIONS per DESTINATION per weekend day. Gated logic, biased
   toward tyre safety:

   HARD DISQUALIFIERS → ❌ Poor (ride not viable):
   - Springvale (origin) roads WET or DAMP — bike can't leave safely
   - Destination roads WET
   - Any precipitation on the ride day (precip_sum > 0.5mm OR precip_prob > 30%)
   - Thunderstorm forecast (weathercode 95/96/99)
   - temperature_2m_min < 8°C — too cold for slicks to come up to grip
   - windgusts_10m_max > 50 km/h

   MARGINAL flags → cap at ⚠️ Marginal:
   - Destination roads DAMP (origin must still be DRY)
   - temperature_2m_max < 16°C — cool for slicks, grip will be tentative
   - windspeed_10m_max > 35 km/h sustained

   Otherwise:
   - ☀️ Excellent: all roads DRY, no precip, max 18–30°C, winds < 25 km/h
   - ✅ Good: all roads DRY, no precip, no marginal flags
   - ⚠️ Marginal: at least one marginal flag, no disqualifier
   - ❌ Poor: any disqualifier

   Springvale and Melbourne don't get rated (they're not destinations) — show
   "—" for their rating cell.

4. CALENDAR ANALYSIS — pull events for FRIDAY, Saturday, AND Sunday.

   AVAILABILITY: A weekend day is "available" if there's at least one contiguous
   free window of 3+ hours during daylight (sunrise/sunset in JSON).

   NIGHT-BEFORE CHECK: For each potential ride day, examine the previous night's
   events (Friday night for a Sat ride, Sat night for a Sun ride). If a likely
   social/drinking event — keywords: drinks, party, birthday, wedding, celebration,
   dinner with, pub, bar, brewery, gig, show, [name]'s [event] — finishes late,
   push the earliest sensible ride start:
     * Ends ≤ 8pm     → no adjustment
     * Ends 8pm–11pm  → start no earlier than 9am
     * Ends 11pm–1am  → start no earlier than 11am
     * Ends > 1am     → start no earlier than 1pm
   Use judgment on ambiguous titles ("Project review with Sam at 7pm" ≠ drinks;
   "drinks with Sam at 7pm" = drinks). Only push the start time when the title
   has clear social keywords; when in doubt, don't adjust.

   RECOMMENDED START = MAX(free-window opens, hangover-adjusted earliest, sunrise + 1hr)
   RECOMMENDED END   = MIN(free-window closes, sunset - 1hr, next event start)

   If the recommended window collapses to < 3 hours, treat that day as unavailable.

5. SEND RULE: ALWAYS create a Gmail draft addressed to jchandler1995@gmail.com
   (a Google Script forwards drafts from there). The report runs in one of two
   MODES, decided by the assessment:

   - MODE A — RIDE: at least one DESTINATION is rated ⚠️ Marginal or better on
     an available day (post-adjustment window ≥ 3 hours). Recommend the best
     day + destination + window.
   - MODE B — NO-GO: every destination on every available day is ❌ Poor, OR
     Springvale roads are wet/damp on both days, OR the recommended windows
     all collapsed below 3 hours. Recommend skipping the ride and pivoting
     to other plans, with a clear explanation of WHAT blocked it.

   The two modes share the same overall template — only the SUBJECT, PRE-HEADER,
   TL;DR CARD, and VERDICT differ. Tables (Weather Forecast, Road Conditions)
   render the same way in both modes; in NO-GO mode they show the ❌ Poor /
   🌧️ WET / 💧 DAMP statuses that explain the blocker.

   ── SUBJECT ──
   Format: 🏍️ Weekend Ride Report - <DD-MM-YYYY> — <verdict suffix>
   - Date is Saturday's, e.g. 09-05-2026
   - Verdict suffix:
     * MODE A: rating emoji + best day + best DESTINATION, e.g.
       "✅ Sat at Jamieson" or "⚠️ Sun at Reefton Spur (cool & damp)"
     * MODE B: ❌ Skip this weekend + one-word reason, e.g.
       "❌ Skip this weekend — wet roads" or
       "❌ Skip this weekend — rain & cold"

   ── EMAIL BODY (HTML) ──
   Inline CSS only — NO <style> blocks (Outlook 2016+ strips them). Build layout
   from nested HTML tables. Every <table> declares a width AND
   style="border-collapse:collapse;" inline. Wrap everything in a max-width:600px
   container table. No external assets (images, web fonts, CSS). System font stack:
   -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif.

   Single shared palette across rating pills, road status pills, and verdict box:
     · Green  #16a34a  (Excellent / Good / DRY)
     · Amber  #f59e0b  (Marginal / DAMP)
     · Red    #dc2626  (Poor / WET)

   STRUCTURE in this order:

   (a) PRE-HEADER — hidden inbox preview, FIRST element after <body>:
       <div style="display:none;max-height:0;overflow:hidden;mso-hide:all;">
         MODE A: e.g. "Sat at Reefton Spur — dry roads, 22°C. Ride 11am–4pm."
         MODE B: e.g. "Skip this weekend — wet roads everywhere, rain Sat & Sun."
       </div>

   (b) HEADER — 🏍️ "Weekend Ride Weather Report" + date range subtitle.

   (c) TL;DR CARD — coloured panel tinted to match the verdict colour.
       MODE A — green or amber tint, big readable type:
         · Headline: best day + best DESTINATION (e.g. "Saturday at Reefton Spur")
         · Sub-line: Ride: ☀️ Excellent · Roads: ☀️ Dry · Window: 11am–4pm
       MODE B — red tint:
         · Headline: "Skip this weekend" (or similar — e.g. "Bike stays in the
           garage")
         · Sub-line: one-line reason summary, e.g.
           "Wet roads at home + rain forecast both days. Make other plans."
       Window/details only shown in MODE A.

   (d) 📅 CALENDAR CHECK — coloured callout. Three lines:
         · Saturday: free <window>, recommended start <time>
         · Sunday:   free <window>, recommended start <time>
         · Friday context (only if it affects timing): one line, e.g.
           "Friday: drinks with Mike until ~midnight — Sat start pushed to 11am."
       Skip the Friday-context line if no night-before adjustments apply.

   (e) 🌦️ WEATHER FORECAST BY LOCATION — table:
         | Location | Saturday <D Mon> | Sunday <D Mon> | Ride Rating |
       With 10 rows, group by region using small grey sub-header rows so the
       table scans in chunks. Order:
         • Home & Reference: Springvale (home), Melbourne (reference)
         • Dandenongs:       Gembrook
         • Yarra Ranges:     Healesville, Warburton, Mount Donna Buang
         • Reefton Spur
         • Alpine:           Marysville, Lake Mountain
         • High Country:     Jamieson
       Annotate Springvale "(home)" and Melbourne "(reference)" in the location
       cell. Ride Rating shows "—" for home/reference rows; destinations get a
       coloured pill.

       Beneath each location row, add a 5-DAY TREND STRIP — sub-row spanning the
       day/rating columns with five inline cells, one per entry in `daily.time`:
         [W ☔] [T ☔] [F ⛅] [S ☀️] [S ☀️]
       Day-letter (W/T/F/S/S) + weathercode emoji:
         0 → ☀️ · 1-3 → ⛅ · 45,48 → 🌫️ · 51-57 → 🌦️ ·
         61-67, 80-82 → 🌧️ · 71-77, 85-86 → ❄️ · 95-99 → ⛈️
       Sat/Sun cells get a subtle highlight.

   (f) 🛣️ ROAD CONDITIONS — table for ALL TEN locations, Springvale row FIRST
       (it's the gate). Use the same regional grouping as the weather table.
       Columns:
         | Location | Status | Why |
       Annotate Springvale: "(home — bike must leave on dry roads)".
       Status: 🌧️ WET / 💧 DAMP / ☀️ DRY (coloured pill).
       Why: one line referencing the prior 3 days, e.g.
         "27mm rain Wed–Fri, only 5mm drying, humidity 75% avg".

   (g) 🏁 VERDICT — coloured callout matching the TL;DR.
       MODE A: lead with day + destination + recommended window (e.g. "Head to
       Reefton Spur Saturday — ride 11am–4pm to dodge the post-drinks fog,
       then home before sunset"). Note routes/areas to avoid (e.g. wet alpine
       summits, cold ridges). 2–4 sentences.
       MODE B: lead with the headline blocker in plain English (e.g. "Springvale
       roads will be soaked from 35mm of rain Wed–Fri — bike's not leaving the
       garage. Both Sat and Sun also forecast rain across the ranges."). End
       with a brief pivot suggestion (e.g. "Good weekend to clean the bike,
       catch up on indoor things, or look ahead to next Saturday's outlook.").
       2–4 sentences total.

   (h) FOOTER — small grey text:
       "Auto-generated by your Claude Code riding routine.
        Forecast source: Open-Meteo (https://open-meteo.com).
        Always check the latest BOM forecast before you head out."

   No footnotes about location names or "data unavailable" — all ten locations
   have full data. Use real values throughout, no placeholders.

A draft is always created — MODE A when a viable ride exists, MODE B when it
doesn't. The only thing that varies is whether the headline says "go riding"
or "skip this weekend".
