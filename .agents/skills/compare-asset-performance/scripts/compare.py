"""Compare equities, ETFs and cryptocurrencies using daily adjusted closes on shared dates."""
import argparse
import base64
import mimetypes
import csv
from datetime import date, datetime, time, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


def epoch(day):
    return int(datetime.combine(day, time.min, timezone.utc).timestamp())


def load(symbol, start, end, output, cached):
    params = urlencode(dict(period1=epoch(start), period2=epoch(end + timedelta(days=1)),
                            interval="1d", events="div,splits", includeAdjustedClose="true"))
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol)}?{params}"
    if cached:
        raw = (cached / (symbol + ".json")).read_bytes()
    else:
        with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as response:
            raw = response.read()
    chart = json.loads(raw)["chart"]
    if chart["error"] or not chart["result"]:
        raise ValueError(f"{symbol}: provider returned no series")
    series = chart["result"][0]
    meta = series["meta"]
    if meta["symbol"] != symbol or meta["instrumentType"] not in {"EQUITY", "ETF", "CRYPTOCURRENCY"}:
        raise ValueError(f"Unexpected instrument for {symbol}")
    zone = ZoneInfo(meta["exchangeTimezoneName"])
    timestamps = series["timestamp"]
    values = series["indicators"]["adjclose"][0]["adjclose"]
    if len(timestamps) != len(values):
        raise ValueError(f"{symbol}: timestamp/value count mismatch")
    prices = {}
    for timestamp, value in zip(timestamps, values):
        day = datetime.fromtimestamp(timestamp, zone).date()
        now = datetime.now(timezone.utc)
        if day >= now.astimezone(zone).date():
            close = meta.get("currentTradingPeriod",{}).get("regular",{}).get("end")
            if not close or datetime.fromtimestamp(close,zone).date()!=day or now.timestamp()<close:
                continue
        if start <= day <= end and value is not None and math.isfinite(value) and value > 0:
            if day in prices:
                raise ValueError(f"{symbol}: duplicate session {day}")
            prices[day] = value
    if not prices:
        raise ValueError(f"{symbol}: no valid observations in range")
    (output / (symbol + ".json")).write_bytes(raw)
    return prices, dict(symbol=symbol, url=url, field="indicators.adjclose[0].adjclose",
                        instrument_type=meta["instrumentType"], currency=meta["currency"], timezone=str(zone), first=str(min(prices)),
                        last=str(max(prices)), valid_rows=len(prices), sha256=hashlib.sha256(raw).hexdigest())


def render(dates, returns, output, colors, edges):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.dates import AutoDateLocator, ConciseDateFormatter, MonthLocator, DateFormatter
    from matplotlib.ticker import PercentFormatter

    fig = plt.figure(figsize=(12.8, 7.2), dpi=100, facecolor="#151618")
    fig.text(.065, .884, "Cumulative return", color="#f1f2f3", fontsize=32)
    fig.text(.067, .821, f"{dates[0]:%b %d, %Y}  –  {dates[-1]:%b %d, %Y}   ·   Adjusted close",
             fontsize=14, color="#b3b6ba")
    ax = fig.add_axes([.085, .135, .665, .595], facecolor="#151618")
    ax.spines[:].set_visible(False)
    ax.tick_params(colors="#b5b7ba", length=0, pad=8)
    ax.yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    locator = AutoDateLocator(minticks=3, maxticks=8)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(ConciseDateFormatter(locator))
    if 460 <= (dates[-1]-dates[0]).days <= 1800:
        ax.xaxis.set_major_locator(MonthLocator(bymonth=[1,7]))
        ax.xaxis.set_major_formatter(DateFormatter("%b %Y"))
    ax.xaxis.get_offset_text().set_color("#b5b7ba")
    ax.grid(axis="y", color="#343639", linewidth=.7)
    ax.axhline(0, color="#797c80", lw=.9)
    ax.set_xlim(dates[0], dates[-1])
    ordered = sorted(returns, key=lambda s: returns[s][-1], reverse=True)
    fig.text(.79,.762,"Period return",fontsize=12,color="#b3b6ba")
    for idx, sym in enumerate(ordered):
        color = colors[sym]
        ax.plot(dates,returns[sym],color=edges[sym],lw=3.3)
        ax.plot(dates, returns[sym], color=color, lw=1.75)
        y = .69 - idx * min(.146, .52 / max(1,len(ordered)-1))
        fig.text(.79, y, sym, fontsize=15, color=edges[sym], weight="bold")
        fig.text(.79, y-.056, f"{returns[sym][-1]:+.2f}%", fontsize=24, color="#f2f3f4")
    fig.savefig(output / "comparison.png", dpi=100)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("symbols", nargs="+")
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, default=date.today(), help="Inclusive completed session cutoff (default: today)")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cached", type=Path, help="Replay previously downloaded Yahoo chart JSON")
    parser.add_argument("--brands", type=Path, default=Path(__file__).resolve().parents[1]/"assets/brands.json")
    args = parser.parse_args()
    symbols = [s.upper() for s in args.symbols]
    if not (2 <= len(set(symbols)) == len(symbols) <= 6) or not all(re.fullmatch(r"[A-Z0-9][A-Z0-9.-]*",s) for s in symbols):
        parser.error("Use two to six distinct exchange tickers")
    if args.start >= args.end or args.end > datetime.now(timezone.utc).date():
        parser.error("Use an inclusive cutoff through today UTC")
    args.out.mkdir(parents=True, exist_ok=True)
    raw_dir = args.out / "raw"
    raw_dir.mkdir(exist_ok=True)
    data, sources = {}, []
    for symbol in symbols:
        data[symbol], source = load(symbol,args.start,args.end,raw_dir,args.cached)
        sources.append(source)
    if len({s["currency"] for s in sources}) != 1:
        parser.error("Convert to a shared currency before comparing these assets")
    dates = sorted(set.intersection(*(set(rows) for rows in data.values())))
    if len(dates) < 2:
        parser.error("Fewer than two shared observations")
    returns = {s:[100*(data[s][d]/data[s][dates[0]]-1) for d in dates] for s in symbols}
    with (args.out / "daily.csv").open("w", newline="") as f:
        w=csv.writer(f, lineterminator="\n")
        w.writerow(["date"]+[f"{s}_adjusted_close" for s in symbols]+[f"{s}_return_pct" for s in symbols])
        for i,d in enumerate(dates):
            w.writerow([d]+[data[s][d] for s in symbols]+[returns[s][i] for s in symbols])
    audit=dict(requested=[str(args.start),str(args.end)], observed=[str(dates[0]),str(dates[-1])],
               common_sessions=len(dates), run_utc=datetime.now(timezone.utc).isoformat(),
               input_mode="cached" if args.cached else "download", sources=sources)
    (args.out/"sources.json").write_text(json.dumps(audit,indent=2)+"\n")
    assets = Path(__file__).resolve().parents[1] / "assets"
    brands = json.loads(args.brands.read_text())
    fallback = ["#7bd5ed","#f0b97b","#afc495","#dd9cb9","#b9a7e9","#d8da83"]
    colors, edges, logos = {}, {}, []
    for i,sym in enumerate(symbols):
        brand = brands.get(sym,{})
        color = brand.get("accent", fallback[i])
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}",color):
            raise ValueError(f"Invalid logo accent for {sym}")
        colors[sym] = color
        rgb = [int(color[k:k+2],16) for k in (1,3,5)]
        edges[sym] = "#" + "".join(f"{round(v+(255-v)*.5):02x}" for v in rgb)
        logo = brand.get("logo")
        if logo:
            path = args.brands.parent / logo
            mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
            logos.append("data:"+mime+";base64,"+base64.b64encode(path.read_bytes()).decode())
        else:
            logos.append(None)
    monday = dates[-1] - timedelta(days=dates[-1].weekday())
    baseline = next((i for i in reversed(range(len(dates))) if dates[i]<monday),None)
    if baseline is not None and (monday-dates[baseline]).days>7:
        baseline=None
    payload=dict(symbols=symbols,dates=list(map(str,dates)),values=[[data[s][d] for d in dates] for s in symbols],
                 names=[brands.get(s,{}).get("name",s) for s in symbols],colors=list(colors.values()),edges=list(edges.values()),logos=logos,weekStart=baseline)
    html=(assets/"player.html").read_text().replace("__DATA__",json.dumps(payload).replace("<",r"\u003c"))
    css = (assets/"video.css").read_text()
    html=html.replace("__VIDEO_CSS__",css).replace("__NUMBER_FLOW__",(assets/"number-flow.min.js").read_text())
    (args.out/"interactive.html").write_text(html)
    render(dates,returns,args.out,colors,edges)
    if baseline is not None:
        print("Week baseline",dates[baseline],{s:round(100*(data[s][dates[-1]]/data[s][dates[baseline]]-1),2) for s in symbols})
    print(dates[0],dates[-1],len(dates),{s:round(returns[s][-1],2) for s in symbols})


if __name__ == "__main__":
    main()
