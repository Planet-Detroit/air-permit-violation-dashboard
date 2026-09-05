# Feature Spec: Restore and harden the Michigan Air Permit Violation Dashboard

**Date**: 2026-09-05
**Status**: Draft (for Nina's approval; open decisions listed at the end)

---

## 1. Purpose

The dashboard at dashboard.planetdetroit.org maps every Michigan facility
that EGLE's Air Quality Division has cited for violating its air permit
since 2018, with the notice text and a link to the PDF. It went quiet after
December 2024 when EGLE moved its document database to the MiEnviro portal,
and it silently showed stale data for twenty months. The daily job was
repaired on Sept 4, 2026, but the data still has an eighteen-month hole,
the collection method misses most notices, some new PDFs do not parse, the
facility directory is frozen at 2022, and nothing tells a reader or an
editor when the data is stale. This spec finishes the job: the dashboard
collects violation notices directly from MiEnviro, is complete back to 2018,
says how fresh it is, and tells us when it breaks.

## 2. Users

- **Primary user**: Michigan readers checking whether a facility near them
  has been cited, and reporters (Dustin, freelancers) looking for story leads
  and for the notice PDF to cite.
- **How they'll access it**: the public page, embedded iframes in articles
  (including `?srn=` deep links), and the public Google Sheet of all notices.
- **How often they'll use it**: readers occasionally after a story; reporters
  weekly. The data updates daily.

## 3. User Workflow

1. Reader opens the dashboard or an embedded map in a story.
2. Reader sees a map of facilities sized by violation count and colored by
   EPA class, a "recent violations" panel of the newest notices, and a line
   saying when the data was last updated.
3. Reader clicks a facility and sees each dated notice, the violations EGLE
   cited in plain language, the location if it differs from the facility
   address, and a link to the PDF.
4. A reporter opens the Google Sheet to filter by county, class, or year.
5. If the data is more than two days old, the page says so in a visible
   banner, and Nina has already received a failure notification.

## 4. Requirements

1. **Collect directly from MiEnviro.** Each day, ask the MiEnviro map
   explorer (nSITE) for every air facility that received a violation notice
   in the current and previous month (the statewide site search with
   enforcement type, issue-date month, and site type filters), then fetch
   each returned site's document list and keep the notices not yet in the
   dataset. Shelby Jouppi's dataset remains a cross-check, not the source.
2. **Count every kind of violation notice.** "Violation Notice," "Second
   Violation Notice," and their variants (after-the-fact, egregious, order to
   restore, request information) all count, and the type is stored and shown.
3. **Backfill the hole.** One-time run over every month from September 2024
   through the present, then a check of 2018 to 2024 against nSITE for
   notices the old scraper missed. Existing rows and their URLs are never
   removed.
4. **Recall check.** Every run records, for the current month, the number of
   air facilities nSITE says received a notice and the number the dataset
   holds. A gap larger than 5 percent is flagged in the run report.
5. **Parse the new PDFs.** The comment extractor handles the current EGLE
   table layout (spacer columns around "Process Description," "Permit/Rule
   Violated," "Comments"). Image-only scans are labeled "Scanned notice, see
   PDF" rather than "Please see document," and counted in the report.
6. **Keep the facility directory current.** A facility not in the 2022
   directory is added from the nSITE search result (name, address, city,
   zip, coordinates, and Title V status). Coordinates from nSITE are used for
   new facilities; existing pins do not move.
7. **Show freshness.** The job writes a small status file (last successful
   run, notices added, recall check). The page shows "Data updated <date>"
   and a visible banner if the last success is more than 48 hours old.
8. **Notify on failure.** A failed run sends a notification (channel to be
   decided) the same day. Silence is never the failure mode again.
9. **Preserve every public surface.** The page URL, `?srn=` deep links, the
   output CSV names and columns, the map data files the page reads, and the
   Google Sheet keep working unchanged.
10. **Tests and documentation.** Every requirement above has an automated
    test that runs in the workflow before scraping. A `MAINTENANCE.md`
    explains, for a non-technical person, what runs, how to tell it is
    working, and what to do when it is not.

## 5. Acceptance Criteria

Collection
- [ ] When the collector asks nSITE for August 2026 air-facility violation
      notices, then it returns the sites and fetches each site's documents
      without a login (recorded fixture from the live API).
- [ ] When a site's document list contains "Violation Notice" and "Second
      Violation Notice" entries, then both become rows with the correct type,
      date, facility ID, and PDF link, and unrelated documents (permits,
      inspection reports, form submissions) are ignored.
- [ ] When a notice is already in the dataset (same document ID or URL), then
      it is not added again.
- [ ] When Shelby's dataset contains a notice the collector did not find, then
      the run report lists it (cross-check), and vice versa.

Backfill and recall
- [ ] When the backfill finishes, then 2025 contains notices for at least
      190 air facilities (nSITE says 202 received one) and every month from
      September 2024 through June 2026 has rows.
- [ ] When the monthly recall check finds the dataset below 95 percent of
      the nSITE site count, then the run report flags it.
- [ ] When 2023 is re-checked, then the existing 260 rows remain and any
      additions are appended, never replaced.

Parsing
- [ ] When the parser reads the ZFS Ithaca notice (table with spacer
      columns), then it extracts the Comments cells.
- [ ] When the parser reads the Branch County Road Commission notice (image
      only), then the row reads "Scanned notice, see PDF," the report counts
      one scanned document, and the row still carries date, facility, and link.
- [ ] When a notice says "located at <address>, Michigan," then the location
      is captured; when it does not, the field is empty, not wrong.

Facilities and map
- [ ] When a notice belongs to a facility not in the directory, then the
      facility is added with nSITE coordinates and appears on the map; a
      facility already in the directory keeps its existing pin.
- [ ] When a notice is dated in a calendar year the map has never seen, then
      a count column for that year is added (existing test).
- [ ] When a MiEnviro URL has no filename, then facility ID and date come from
      the dataset (existing test).

Freshness and failure
- [ ] When a run succeeds, then the status file carries today's date and the
      page shows it.
- [ ] When the status file is more than 48 hours old, then the page shows the
      stale-data banner.
- [ ] When the workflow fails, then a notification is sent within the hour.

Stability
- [ ] When an article embed opens `?srn=N2155`, then the Stellantis Mack
      facility is selected as before.
- [ ] When the run finishes, then the Google Sheet "data" tab matches the
      output CSV.

## 6. Out of Scope

- Redesigning the map or page. The look stays; only the data and the
  freshness line change.
- Notices from other EGLE programs (water, waste, asbestos, dry cleaners)
  and drinking-water violations. Those belong to the Civic Action Toolbox
  collector, which will reuse this collector's code.
- Changing Shelby's repository. Her scraper keeps running; we only read it.
- Editorial judgment about what a notice means. Copy says "notice of
  violation," and the PDF is always linked.

## 7. Connects To

- MiEnviro nSITE site search and document endpoints (anonymous; see
  `civic-action-toolbox-app/docs/research/nsite-inventory-2026-09-04.md`).
- Shelby Jouppi's `michigan-egle-database-auto-scraper` outputs (cross-check).
- GitHub Actions (daily run), GitHub Pages (the page), the public Google
  Sheet via `sheets-updater.py`.
- pollution-near-me (air.planetdetroit.org), which links here and whose EPA
  data lags EGLE's; the two should cross-link and share the caveat.
- The Civic Action Toolbox "violation & enforcement notices" collector,
  which will import this collector rather than rebuild it.

## 8. Known Risks

- **If data is wrong**: a notice pinned to the wrong facility, or a parsed
  comment attributed to the wrong company, is a reputational risk. Mitigation:
  facility ID comes from EGLE's own site record, every row links its PDF,
  and the recall report is reviewed before backfilled data goes live.
- **If the tool goes down**: the page keeps serving the last good data and
  says how old it is; the notification reaches Nina the same day.
- **If MiEnviro changes**: the API is undocumented. Fixtures are recorded
  from real responses so a change breaks tests loudly, and the run report
  shows a sudden zero.
- **Rate limits and courtesy**: the collector makes one search per month
  window plus one request per affected site (about 10 to 30 a day; a few
  thousand during backfill, spread over hours with a delay).
- **Security**: no credentials are needed for collection. The Google Sheets
  service account key stays in GitHub secrets, unchanged.
- **Meaning**: many notices are paperwork violations. The type field and
  comment text let readers see which; the page copy says so.

## 9. Success Metrics

- Monthly notice count within 5 percent of nSITE's site count, every month.
- Zero days where the page shows data older than 48 hours without a banner.
- 2025 and 2026 fully populated within one week of approval.
- The Civic Action Toolbox collector ships by importing this code, not
  rewriting it.

---

## Open decisions for Nina

1. **Asbestos and dry-cleaner notices**: the Air Quality Division also
   issues violation notices to asbestos demolition sites (68 in 2026) and
   dry cleaners (22). Include them on the map with their own class, or keep
   the map to permitted air facilities? Recommendation: keep to permitted
   facilities and Title V, and let the Toolbox collector take the rest.
2. **Failure notification channel**: email to nina@, or a Slack channel?
   Recommendation: Slack, since the impact logger already posts there.
3. **Backfilled data review**: publish the 2025 backfill as soon as the
   recall check passes, or hold it for an editorial spot-check of a sample?
   Recommendation: spot-check 20 notices, then publish.
4. **Credit line**: keep "by Shelby Jouppi" and add "data collection updated
   September 2026"? Recommendation: yes.

_After approval: write the automated tests for each acceptance criterion
first, then implement, then update MAINTENANCE.md._
