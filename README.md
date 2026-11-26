# Market video skills

Download this project, unzip it, and open the extracted folder in Codex or Claude Code. Use a signed-in client.

| Skill | Codex | Claude Code |
|---|---|---|
| Edit your market commentary with speech-timed charts and optional captions | `$edit-market-video` | `/edit-market-video` |
| Render an autoplaying comparison with rolling returns and moving logos | `$compare-asset-performance` | `/compare-asset-performance` |

Attach your own video for the editing skill. For a comparison, try “Compare NVDA, MU and BRK-B this week. Export a silent MP4.” The editing skill guides the agent through a new edit. The comparison skill includes a chart generator and an MP4 exporter.

## First comparison export

Install Python 3.10 or later, Node.js 22.12 or later, FFmpeg and Chrome. From the project root, run the following in your Python environment.

```sh
python3 -m pip install matplotlib
npm ci
python3 .agents/skills/compare-asset-performance/scripts/compare.py NVDA MU BRK-B --start 2024-01-01 --out comparison
node .agents/skills/compare-asset-performance/scripts/export.cjs comparison/interactive.html week comparison/week.mp4
```

Use `full` in place of `week` for the full period. Set `CHROME_PATH` when Chrome is installed in another location. The generator downloads daily adjusted closes from Yahoo Finance. A live run needs network access. To reproduce a completed run, pass its saved raw JSON directory with `--cached`. Check the effective dates before publishing.

The included company SVG marks come from TradingView’s symbol-logo CDN. See the [brand map](.agents/skills/compare-asset-performance/assets/brands.json) for sources and accents. The video uses a local CSS gradient, system fonts and [NumberFlow](.agents/skills/compare-asset-performance/assets/number-flow-LICENSE.md).
