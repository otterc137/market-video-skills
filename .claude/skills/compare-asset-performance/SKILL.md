---
name: compare-asset-performance
description: Compare the performance of stocks, ETFs or cryptocurrency pairs over a common period or week to date. Produce autoplaying MP4 chart inserts for market-update videos with brand-colored lines, moving logo markers and a readable final hold.
---

For video work, deliver the rendered MP4 as the primary asset. Use the HTML as a seekable composition during production. Choose the weekly cut for a weekly update and the long-period cut for a longer-term comparison. Match the archived editor's neutral dark panels, silver texture, Delight type and Geist Mono date labels. Place the insert on the edited speech timeline and retain the original narration. For a custom-length insert, adjust the draw duration and final hold to the cue.

Resolve the ticker, share class, currency and period before calculating. Record the cutoff and actual first and last shared observations. For example, Berkshire Class B is BRK-B on Yahoo. For stocks use daily adjusted closes, including the provider's split and distribution adjustments. For crypto use a quoted pair such as BTC-USD and check that the response includes the chosen field. Mixed calendars and exchange time zones can give different observation times on the same date. Explain that limitation when presenting a mixed comparison.

Run the script relative to this skill directory with Python 3.10+ and Matplotlib installed:

```sh
python3 scripts/compare.py NVDA MU BRK-B --start 2024-01-01 --end 2026-11-26 --out comparison
```

Use the episode’s actual dates. For “current,” pass today's date and check the effective end date. The script uses the intersection of valid exchange-local dates and a shared currency. It discards an unfinished current daily bar. Check the per-symbol spans and valid row counts in `sources.json`. Flag shortened coverage, unexplained gaps or stale endpoints before describing a result as current. A year-opening comparison starts at the first shared close. To measure a full calendar year's return including its first session, include the previous year's final close as the baseline.

The composition autoplays on the week containing the latest common date. Its baseline is the last shared close before Monday. For US equities this is usually Friday. A holiday-shortened week may have only a few observations. The full-period view rebases all lines to zero on the first common date. Both views use `100 × (adjusted close / baseline − 1)`. The marker moves smoothly between observations. Give each asset a separate card showing its logo, ticker and return. Use fixed-width digit slots throughout the hold and roll so the decimal point and percent sign stay anchored. A short vertical digit roll transitions between sampled session returns and settles on the exact ending value. Use `#full` for long-history playback. Add `?review` only for internal play/pause and scrubbing controls.

The CLI saves raw provider JSON, checksums, aligned daily adjusted closes and returns, a static PNG, and a self-contained seekable composition. Replay a snapshot with `--cached PATH_TO_RAW`. Add new verified logos and exact hex accents to a JSON map following `assets/brands.json`, and pass `--brands FILE`. The line core uses that accent. A lighter rim keeps dark tones visible. For a new asset, obtain and inspect its logo, record its source, and sample its accent before delivery. If artwork cannot be verified, disclose the text-marker fallback and its neutral or fallback color.

For a video insert, render the same player after installing the repository's rendering dependencies with `npm ci` from the repository root. From the skill directory:

```sh
node scripts/export.cjs comparison/interactive.html week comparison/week.mp4
node scripts/export.cjs comparison/interactive.html full comparison/full.mp4
```

The exporter produces silent 1280 × 720, 30 fps H.264 inserts with a 2.5-second ending hold. The weekly cut runs 6.5 seconds and the full-period cut runs 9 seconds. The renderer uses the included CSS theme and system fonts. The exporter needs FFmpeg and Chrome. Set `CHROME_PATH` for a different local browser installation. Review the short weekly window and the long window separately. Verify zero at each baseline and recompute the final displayed return from the saved endpoints. Check logos at a crossover, labels at phone width, and the final hold in the encoded video.
