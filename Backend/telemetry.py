import os
import time
import fastf1
import fastf1.plotting
import pandas as pd
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

# ── CONFIG ────────────────────────────────────────────────────────────────────
load_dotenv()
BASE_DIR  = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / os.getenv("CACHE_DIR", "cache")
CACHE_DIR.mkdir(exist_ok=True)
SEASON    = int(os.getenv("F1_SEASON", 2026))
EVENT     = os.getenv("F1_EVENT", "Suzuka")
SESSION   = os.getenv("F1_SESSION", "Q")

fastf1.Cache.enable_cache(str(CACHE_DIR))

# ── ANSI COLORS ───────────────────────────────────────────────────────────────
R    = "\033[91m"
G    = "\033[92m"
Y    = "\033[93m"
B    = "\033[94m"
M    = "\033[95m"
C    = "\033[96m"
W    = "\033[97m"
DIM  = "\033[2m"
BOLD = "\033[1m"
RST  = "\033[0m"

W_TOTAL = 72

# ── LAYOUT HELPERS ────────────────────────────────────────────────────────────
def banner():
    pad = " " * ((W_TOTAL - 44) // 2)
    print(f"\n{R}{'█' * W_TOTAL}{RST}")
    print(f"{R}██{RST}{pad}{BOLD}{W}F1-PITWALL-AI  ·  TELEMETRY SYSTEM  ·  v0.2{RST}{pad}{R}██{RST}")
    print(f"{R}██{RST}{' ' * (W_TOTAL - 4)}{R}██{RST}")
    print(f"{R}██{RST}  {DIM}Real-time F1 data analysis · Race engineering intelligence{RST}  {R}██{RST}")
    print(f"{R}{'█' * W_TOTAL}{RST}\n")

def header(title, subtitle=""):
    top = f"┌─  {BOLD}{W}{title}{RST}"
    if subtitle:
        top += f"  {subtitle}"
    print(f"\n{B}{top}{RST}")
    print(f"{B}{'─' * W_TOTAL}{RST}")

def footer_line():
    print(f"{B}{'─' * W_TOTAL}{RST}")

def row(label, value, unit="", color=W, note=""):
    note_str = f"  {DIM}{note}{RST}" if note else ""
    print(f"  {DIM}{label:<22}{RST}{color}{BOLD}{value}{RST} {DIM}{unit}{RST}{note_str}")

def row2(l1, v1, u1, l2, v2, u2, c1=W, c2=W):
    left  = f"  {DIM}{l1:<22}{RST}{c1}{BOLD}{v1}{RST} {DIM}{u1}{RST}"
    right = f"  {DIM}{l2:<22}{RST}{c2}{BOLD}{v2}{RST} {DIM}{u2}{RST}"
    print(f"{left:<54}{right}")

def divider():
    print(f"  {DIM}{'·' * (W_TOTAL - 4)}{RST}")

def tag(label, color=B):
    return f"{color}[{label}]{RST}"

def pct_bar(value, max_val=100, width=20, color=G):
    filled = int((value / max_val) * width) if max_val > 0 else 0
    bar    = "█" * filled + "░" * (width - filled)
    return f"{color}{bar}{RST} {DIM}{value:.1f}%{RST}"

def compound_color(cmp):
    cmp = str(cmp).upper()
    if   cmp == "SOFT":                  return R
    elif cmp == "MEDIUM":                return Y
    elif cmp == "HARD":                  return W
    elif cmp in ("WET", "INTERMEDIATE"): return B
    return C

def compound_icon(cmp):
    cmp   = str(cmp).upper()
    icons = {"SOFT": "● S", "MEDIUM": "● M", "HARD": "● H",
             "INTERMEDIATE": "● I", "WET": "● W"}
    return icons.get(cmp, f"● {cmp[:1]}")

def sector_color(val, best):
    diff = (val - best).total_seconds()
    if diff < 0.05: return G
    elif diff < 0.3: return Y
    else: return R

def loading_bar(label, steps=20, delay=0.03):
    for i in range(steps):
        filled = "█" * (i + 1)
        empty  = "░" * (steps - i - 1)
        pct    = int(((i + 1) / steps) * 100)
        print(f"\r  {DIM}{label}  {RST}{B}{filled}{DIM}{empty}{RST}  {W}{pct}%{RST}", end="", flush=True)
        time.sleep(delay)
    print(f"\r  {DIM}{label}  {RST}{G}{'█' * steps}{RST}  {G}{BOLD}DONE{RST}    ")

def sparkline(values, width=60, color=G):
    bars   = " ▁▂▃▄▅▆▇█"
    mn, mx = min(values), max(values)
    step   = max(1, len(values) // width)
    sample = [values[i] for i in range(0, len(values), step)][:width]
    line   = ""
    for v in sample:
        idx   = int((v - mn) / (mx - mn) * (len(bars) - 1)) if mx != mn else 0
        line += bars[idx]
    return f"{color}{line}{RST}"

def dual_sparkline(v1, v2, width=60):
    bars     = " ▁▂▃▄▅▆▇█"
    mn1, mx1 = min(v1), max(v1)
    mn2, mx2 = min(v2), max(v2)
    step     = max(1, min(len(v1), len(v2)) // width)
    s1       = [v1[i] for i in range(0, len(v1), step)][:width]
    s2       = [v2[i] for i in range(0, len(v2), step)][:width]
    line1 = line2 = ""
    for v in s1:
        idx = int((v - mn1) / (mx1 - mn1) * (len(bars) - 1)) if mx1 != mn1 else 0
        line1 += bars[idx]
    for v in s2:
        idx = int((v - mn2) / (mx2 - mn2) * (len(bars) - 1)) if mx2 != mn2 else 0
        line2 += bars[idx]
    return line1, line2

def gap_bar(delta, scale=2.0, width=20):
    pos   = int(min(abs(delta) / scale, 1.0) * width)
    color = G if delta <= 0 else R
    bar   = ("░" * (width - pos) + "█" * pos) if delta <= 0 else ("█" * pos + "░" * (width - pos))
    return f"{color}{bar}{RST}"

# ─────────────────────────────────────────────────────────────────────────────
# MAIN SCRIPT
# ─────────────────────────────────────────────────────────────────────────────

banner()

# ── SESSION LOAD ──────────────────────────────────────────────────────────────
header("SESSION LOAD", tag("LIVE"))
print(f"  {DIM}Target  :{RST}  {W}{BOLD}{SEASON} {EVENT} Grand Prix  ·  {SESSION}{RST}")
loading_bar("Connecting to F1 data feed   ", steps=16, delay=0.04)
session = fastf1.get_session(SEASON, EVENT, SESSION)
loading_bar("Loading telemetry & lap data  ", steps=16, delay=0.04)
session.load(telemetry=True, laps=True, weather=True)
loading_bar("Processing session data       ", steps=16, delay=0.02)

total_laps = len(session.laps)
drivers    = session.drivers
print(f"\n  {G}✔ Session online  {RST}{DIM}·{RST}  {W}{BOLD}{len(drivers)} drivers{RST}"
      f"  {DIM}·{RST}  {W}{BOLD}{total_laps} laps{RST}  {DIM}·{RST}  {tag('NOMINAL', G)}")
footer_line()

# ── SESSION INFO ──────────────────────────────────────────────────────────────
header("SESSION INFO", tag("CIRCUIT DATA"))
evt = session.event
row2("Circuit",  str(evt['Location']),          "", "Country", str(evt['Country']),      "", C, C)
row2("Round",    f"Round {evt['RoundNumber']}", "", "Session", SESSION,                  "", C, C)
row2("Date",     str(session.date)[:10],        "", "Drivers", str(len(drivers)),         "", C, W)
footer_line()

# ── TOP 10 FASTEST LAPS ───────────────────────────────────────────────────────
header("QUALIFYING ORDER  —  TOP 10", tag("CLASSIFIED"))
print(f"  {DIM}{'POS':<5} {'DRV':<5} {'TEAM':<28} {'LAP TIME':<14} {'GAP':<11} {'CPD':<8} {'S1':<10} {'S2':<10} {'S3'}{RST}")
divider()

top10    = session.laps.pick_quicklaps().sort_values('LapTime').head(10)
pos_cols = [G, G, Y, Y, Y, W, W, W, W, W]
pole_lap = top10.iloc[0]['LapTime']

for i, (_, lap) in enumerate(top10.iterrows(), 1):
    lt      = str(lap['LapTime'])[7:15]
    gap     = (lap['LapTime'] - pole_lap).total_seconds()
    gap_str = "POLE" if i == 1 else f"+{gap:.3f}s"
    s1  = f"{lap['Sector1Time'].total_seconds():.3f}" if pd.notna(lap['Sector1Time']) else "—"
    s2  = f"{lap['Sector2Time'].total_seconds():.3f}" if pd.notna(lap['Sector2Time']) else "—"
    s3  = f"{lap['Sector3Time'].total_seconds():.3f}" if pd.notna(lap['Sector3Time']) else "—"
    col = pos_cols[i - 1]
    cmp = lap['Compound'] if pd.notna(lap['Compound']) else "—"
    cc  = compound_color(cmp)
    ci  = compound_icon(cmp)
    print(f"  {col}{BOLD}P{i:<4}{RST}"
          f"{W}{lap['Driver']:<5}{RST}"
          f"{DIM}{str(lap['Team'])[:27]:<28}{RST}"
          f"{col}{BOLD}{lt:<14}{RST}"
          f"{DIM}{gap_str:<11}{RST}"
          f"{cc}{ci:<8}{RST}"
          f"{DIM}{s1:<10}{s2:<10}{s3}{RST}")

footer_line()

# ── FASTEST LAP DEEP DIVE ─────────────────────────────────────────────────────
header("FASTEST LAP  —  DEEP TELEMETRY", tag("POLE"))
fastest = session.laps.pick_fastest()
tel     = fastest.get_telemetry()
cmp_col = compound_color(fastest['Compound'])
cmp_ico = compound_icon(fastest['Compound'])

print(f"\n  {R}{BOLD}▌▌▌  {fastest['Driver']}  ·  {fastest['Team']}  ▌▌▌{RST}\n")

row2("Lap Time",    str(fastest['LapTime'])[7:15],
                    "",   "Compound",   f"{cmp_ico} {fastest['Compound']}", "", G, cmp_col)
row2("Tyre Life",   f"{fastest['TyreLife']} laps",
                    "",   "Fresh Tyre", str(fastest['FreshTyre']),           "", Y, Y)
row2("Pit In",      str(fastest['PitInTime'])[:8]  if pd.notna(fastest['PitInTime'])  else "—",
                    "",   "Pit Out",    str(fastest['PitOutTime'])[:8] if pd.notna(fastest['PitOutTime']) else "—", "", C, C)
divider()
row2("Data Points", f"{len(tel)} samples",         "",     "Top Speed",  f"{tel['Speed'].max():.1f}",  "km/h", W, G)
row2("Avg Speed",   f"{tel['Speed'].mean():.1f}",  "km/h", "Min Speed",  f"{tel['Speed'].min():.1f}",  "km/h", W, R)
row2("Max RPM",     f"{tel['RPM'].max():.0f}",     "rpm",  "Avg RPM",    f"{tel['RPM'].mean():.0f}",   "rpm",  M, M)
row2("Gear Shifts", f"{(tel['nGear'].diff().abs() > 0).sum()}", "shifts",
                    "Top Gear",   f"{int(tel['nGear'].max())}",            "",     C, C)
row2("Brake Events",f"{tel['Brake'].sum()}",       "samples","DRS Active",f"{tel['DRS'].sum()}",       "samples", R, Y)
divider()

full_thr = (tel['Throttle'] == 100).sum()
off_thr  = (tel['Throttle'] == 0).sum()
partial  = len(tel) - full_thr - off_thr
print(f"\n  {DIM}{'Throttle Map':<22}{RST}")
print(f"  {DIM}Full    {RST}{pct_bar(full_thr / len(tel) * 100, color=G)}")
print(f"  {DIM}Partial {RST}{pct_bar(partial  / len(tel) * 100, color=Y)}")
print(f"  {DIM}Zero    {RST}{pct_bar(off_thr  / len(tel) * 100, color=R)}")
footer_line()

# ── SPEED TRACE ───────────────────────────────────────────────────────────────
header("SPEED TRACE  —  FULL LAP", tag("TELEMETRY"))
speeds    = tel['Speed'].values.tolist()
gears     = tel['nGear'].values.tolist()
throttles = tel['Throttle'].values.tolist()

print(f"\n  {DIM}Speed (km/h)    min:{min(speeds):.0f}  avg:{sum(speeds)/len(speeds):.0f}  max:{max(speeds):.0f}{RST}")
print(f"  {sparkline(speeds, width=66, color=G)}")
print(f"  {DIM}{'─' * 66}{RST}")
print(f"\n  {DIM}Gear            1st ────────────────────────────────── {int(max(gears))}th{RST}")
print(f"  {sparkline(gears, width=66, color=C)}")
print(f"  {DIM}{'─' * 66}{RST}")
print(f"\n  {DIM}Throttle (%)    0% ─────────────────────────────────── 100%{RST}")
print(f"  {sparkline(throttles, width=66, color=Y)}")
print(f"  {DIM}{'─' * 66}{RST}")
footer_line()

# ── SECTOR ANALYSIS ───────────────────────────────────────────────────────────
header("SECTOR ANALYSIS  —  TOP 5", tag("MINI SECTORS"))
top5    = session.laps.pick_quicklaps().sort_values('LapTime').head(5)
best_s1 = top5['Sector1Time'].min()
best_s2 = top5['Sector2Time'].min()
best_s3 = top5['Sector3Time'].min()

print(f"  {DIM}{'DRV':<6} {'SECTOR 1':<14} {'SECTOR 2':<14} {'SECTOR 3':<14} {'TOTAL'}{RST}")
divider()

for _, lap in top5.iterrows():
    s1c = sector_color(lap['Sector1Time'], best_s1) if pd.notna(lap['Sector1Time']) else DIM
    s2c = sector_color(lap['Sector2Time'], best_s2) if pd.notna(lap['Sector2Time']) else DIM
    s3c = sector_color(lap['Sector3Time'], best_s3) if pd.notna(lap['Sector3Time']) else DIM
    s1  = f"{lap['Sector1Time'].total_seconds():.3f}s" if pd.notna(lap['Sector1Time']) else "—"
    s2  = f"{lap['Sector2Time'].total_seconds():.3f}s" if pd.notna(lap['Sector2Time']) else "—"
    s3  = f"{lap['Sector3Time'].total_seconds():.3f}s" if pd.notna(lap['Sector3Time']) else "—"
    lt  = str(lap['LapTime'])[7:15]
    print(f"  {W}{BOLD}{lap['Driver']:<6}{RST}"
          f"{s1c}{BOLD}{s1:<14}{RST}"
          f"{s2c}{BOLD}{s2:<14}{RST}"
          f"{s3c}{BOLD}{s3:<14}{RST}"
          f"{W}{lt}{RST}")

print(f"\n  {G}█ GREEN{RST}{DIM}  < 0.05s off best   "
      f"{RST}{Y}█ YELLOW{RST}{DIM}  < 0.3s off best   "
      f"{RST}{R}█ RED{RST}{DIM}  > 0.3s off pace{RST}")
footer_line()

# ── DRIVER HEAD-TO-HEAD ───────────────────────────────────────────────────────
header("DRIVER HEAD-TO-HEAD  —  TOP 3", tag("COMPARISON"))
top3_drivers = top10['Driver'].unique()[:3]
rows_data    = []

for drv in top3_drivers:
    lap = session.laps.pick_drivers(drv).pick_fastest()
    t   = lap.get_telemetry()
    rows_data.append({
        "drv":  drv,
        "top":  t['Speed'].max(),
        "avg":  t['Speed'].mean(),
        "thr":  (t['Throttle'] == 100).sum() / len(t) * 100,
        "brk":  int(t['Brake'].sum()),
        "gear": int(t['nGear'].max()),
        "rpm":  t['RPM'].max(),
        "drs":  int(t['DRS'].sum()),
        "tel":  t,
    })

print(f"  {DIM}{'METRIC':<26}", end="")
for d in rows_data:
    print(f"{W}{BOLD}{d['drv']:<22}{RST}", end="")
print()
divider()

metrics = [
    ("Top Speed (km/h)",   "top",  G, False),
    ("Avg Speed (km/h)",   "avg",  W, False),
    ("Full Throttle (%)",  "thr",  Y, False),
    ("Brake Events",       "brk",  R, True),
    ("Max RPM",            "rpm",  M, False),
    ("DRS Activations",    "drs",  C, False),
    ("Top Gear",           "gear", C, False),
]

for label, key, color, lower_better in metrics:
    vals = [d[key] for d in rows_data]
    best = min(vals) if lower_better else max(vals)
    print(f"  {DIM}{label:<26}{RST}", end="")
    for d in rows_data:
        v   = d[key]
        col = G if v == best else color
        fmt = f"{v:.1f}" if isinstance(v, float) else str(v)
        mrk = f" {G}◀{RST}" if v == best else "   "
        print(f"{col}{BOLD}{fmt}{RST}{mrk:<19}", end="")
    print()

print(f"\n  {DIM}Speed trace — {rows_data[0]['drv']} vs {rows_data[1]['drv']}:{RST}")
sp1, sp2 = dual_sparkline(
    rows_data[0]['tel']['Speed'].values.tolist(),
    rows_data[1]['tel']['Speed'].values.tolist(),
    width=60
)
print(f"  {G}{BOLD}{rows_data[0]['drv']}{RST}  {sp1}")
print(f"  {R}{BOLD}{rows_data[1]['drv']}{RST}  {sp2}")
footer_line()

# ── LAP PROGRESSION ───────────────────────────────────────────────────────────
header("LAP PROGRESSION  —  POLE DRIVER", tag("EVOLUTION"))
drv1    = top3_drivers[0]
d1_laps = session.laps.pick_drivers(drv1).pick_quicklaps().sort_values('LapNumber')

if len(d1_laps) >= 2:
    lap_times = [lt.total_seconds() for lt in d1_laps['LapTime']]
    best_t    = min(lap_times)
    worst_t   = max(lap_times)
    spread    = worst_t - best_t if worst_t != best_t else 1.0

    print(f"\n  {DIM}{'LAP':<6} {'TIME':<12} {'DELTA':<14} {'COMPOUND':<10} CONSISTENCY BAR{RST}")
    divider()

    for _, lap in d1_laps.iterrows():
        lt_s   = lap['LapTime'].total_seconds()
        delta  = lt_s - best_t
        dc     = G if delta < 0.1 else (Y if delta < 0.5 else R)
        lt_fmt = str(lap['LapTime'])[7:15]
        cmp    = lap['Compound'] if pd.notna(lap['Compound']) else "—"
        cc     = compound_color(cmp)
        bar_w  = max(0, int(20 - (delta / spread * 20)))
        bar    = f"{dc}{'█' * bar_w}{'░' * (20 - bar_w)}{RST}"
        d_str  = f"{G}BEST{RST}   " if delta < 0.001 else f"{dc}+{delta:.3f}s{RST}"
        print(f"  {W}{BOLD}{int(lap['LapNumber']):<6}{RST}"
              f"{W}{lt_fmt:<12}{RST}"
              f"{d_str:<20}"
              f"{cc}{compound_icon(cmp):<10}{RST}"
              f"{bar}")
footer_line()

# ── GAP ANALYSIS ──────────────────────────────────────────────────────────────
header("GAP TO POLE  —  TOP 10", tag("INTERVALS"))
print(f"  {DIM}{'DRV':<6} {'GAP':<13} {'VISUAL':<24} {'TEAM'}{RST}")
divider()

max_gap = (top10.iloc[-1]['LapTime'] - pole_lap).total_seconds() + 0.01
for i, (_, lap) in enumerate(top10.iterrows(), 1):
    gap     = (lap['LapTime'] - pole_lap).total_seconds()
    col     = pos_cols[i - 1]
    g_str   = "POLE" if i == 1 else f"+{gap:.3f}s"
    bar     = gap_bar(gap, scale=max_gap)
    print(f"  {col}{BOLD}{lap['Driver']:<6}{RST}"
          f"{col}{g_str:<13}{RST}"
          f"{bar}  "
          f"{DIM}{str(lap['Team'])[:22]}{RST}")
footer_line()

# ── SPEED ZONES ───────────────────────────────────────────────────────────────
header("SPEED ZONE DISTRIBUTION  —  POLE LAP", tag("ZONES"))
bins        = [0, 100, 150, 200, 250, 300, 400]
labels      = ["0–100", "100–150", "150–200", "200–250", "250–300", "300+"]
zone_colors = [R, R, Y, G, G, M]
dist        = pd.cut(tel['Speed'], bins=bins, labels=labels)
counts      = dist.value_counts().reindex(labels)
total_pts   = len(tel)

print(f"\n  {DIM}{'ZONE (km/h)':<14} {'SAMPLES':<10} {'%':<8} DISTRIBUTION{RST}")
divider()

for lbl, col in zip(labels, zone_colors):
    cnt   = counts.get(lbl, 0)
    pct   = cnt / total_pts * 100
    bar_w = int(pct / 2.5)
    bar   = f"{col}{'█' * bar_w}{'░' * (40 - bar_w)}{RST}"
    print(f"  {DIM}{lbl:<14}{RST}{W}{int(cnt):<10}{RST}{col}{pct:<8.1f}{RST}{bar}")
footer_line()

# ── BRAKING ZONES ─────────────────────────────────────────────────────────────
header("BRAKING ZONE ANALYSIS", tag("BRAKE EVENTS"))
brake_arr   = tel['Brake'].values
transitions = np.where(np.diff(brake_arr.astype(int)) == 1)[0]
release_pts = np.where(np.diff(brake_arr.astype(int)) == -1)[0]

print(f"\n  {DIM}{'ZONE':<8} {'ENTRY km/h':<14} {'EXIT km/h':<14} {'SCRUB km/h':<14} {'DURATION'}{RST}")
divider()

for zone_i, start in enumerate(transitions[:10], 1):
    ends  = release_pts[release_pts > start]
    end   = ends[0] if len(ends) > 0 else start + 5
    zone  = tel.iloc[start:end + 1]
    if zone.empty:
        continue
    entry  = zone['Speed'].iloc[0]
    exit_s = zone['Speed'].iloc[-1]
    scrub  = entry - exit_s
    dur    = len(zone)
    col    = R if scrub > 80 else (Y if scrub > 40 else W)
    print(f"  {R}{BOLD}BZ-{zone_i:<5}{RST}"
          f"{W}{entry:<14.1f}{RST}"
          f"{col}{exit_s:<14.1f}{RST}"
          f"{R}{scrub:<14.1f}{RST}"
          f"{DIM}{dur} pts{RST}")
footer_line()

# ── WEATHER & TRACK CONDITIONS ────────────────────────────────────────────────
header("TRACK CONDITIONS", tag("ENVIRONMENT"))
wx      = session.weather_data
air_t   = wx['AirTemp'].mean()
trk_t   = wx['TrackTemp'].mean()
humid   = wx['Humidity'].mean()
press   = wx['Pressure'].mean()
wind_sp = wx['WindSpeed'].mean()
wind_dr = wx['WindDirection'].mean()
rain    = wx['Rainfall'].any()

air_col = G if 20 <= air_t <= 30 else (Y if 15 <= air_t <= 35 else R)
trk_col = G if 30 <= trk_t <= 50 else (Y if 20 <= trk_t <= 55 else R)

row2("Air Temp",   f"{air_t:.1f}",   "°C",   "Track Temp",  f"{trk_t:.1f}",   "°C",   air_col, trk_col)
row2("Humidity",   f"{humid:.1f}",   "%",    "Pressure",    f"{press:.1f}",   "mbar", C,       W)
row2("Wind Speed", f"{wind_sp:.1f}", "m/s",  "Wind Dir",    f"{wind_dr:.0f}", "°",    W,       W)
row("Rainfall",    "YES — WET RACE" if rain else "NO — DRY TRACK", color=B if rain else G)
divider()

temps = wx['TrackTemp'].values.tolist()
at    = wx['AirTemp'].values.tolist()
print(f"\n  {DIM}Track temp trend  min:{min(temps):.1f}°  max:{max(temps):.1f}°{RST}")
print(f"  {sparkline(temps, width=62, color=R)}")
print(f"  {DIM}Air temp trend    min:{min(at):.1f}°    max:{max(at):.1f}°{RST}")
print(f"  {sparkline(at, width=62, color=C)}")
footer_line()

# ── SYSTEM STATUS ─────────────────────────────────────────────────────────────
header("SYSTEM STATUS", tag("DIAGNOSTICS"))
systems = [
    ("FastF1 Data Feed",        True,  "NOMINAL"),
    ("Telemetry Pipeline",      True,  "NOMINAL"),
    ("Session Cache",           True,  "ACTIVE"),
    ("Weather Module",          True,  "NOMINAL"),
    ("Lap Processor",           True,  "NOMINAL"),
    ("AI Engine (Claude)",      False, "STANDBY  ·  activate via  ai.py"),
    ("Voice TTS (ElevenLabs)",  False, "STANDBY  ·  activate via  ai.py"),
    ("WebSocket Server",        False, "STANDBY  ·  activate via  main.py"),
    ("React Dashboard",         False, "STANDBY  ·  run  npm run dev"),
]

for name, ok, status in systems:
    icon = f"{G}●{RST}" if ok else f"{Y}●{RST}"
    scol = G if ok else Y
    print(f"  {icon}  {W}{name:<30}{RST}{scol}{BOLD}{status}{RST}")
footer_line()

# ── CORNER DELTA ANALYSIS ─────────────────────────────────────────────────────
header("CORNER DELTA  —  TOP 2 DRIVERS", tag("MICRO SECTORS"))

drv_a = top3_drivers[0]
drv_b = top3_drivers[1]

lap_a = session.laps.pick_drivers(drv_a).pick_fastest()
lap_b = session.laps.pick_drivers(drv_b).pick_fastest()

tel_a = lap_a.get_car_data().add_distance()
tel_b = lap_b.get_car_data().add_distance()

# Divide the lap into 20 micro sectors by distance
max_dist  = min(tel_a['Distance'].max(), tel_b['Distance'].max())
n_sectors = 20
sector_size = max_dist / n_sectors

print(f"\n  {DIM}Comparing {drv_a} vs {drv_b}  ·  {n_sectors} micro sectors{RST}")
print(f"  {DIM}{'SEC':<6} {'DIST':<12} {drv_a+' SPD':<14} {drv_b+' SPD':<14} {'DELTA':<10} BAR{RST}")
divider()

for i in range(n_sectors):
    dist_start = i * sector_size
    dist_end   = (i + 1) * sector_size

    seg_a = tel_a[(tel_a['Distance'] >= dist_start) & (tel_a['Distance'] < dist_end)]
    seg_b = tel_b[(tel_b['Distance'] >= dist_start) & (tel_b['Distance'] < dist_end)]

    if seg_a.empty or seg_b.empty:
        continue

    spd_a = seg_a['Speed'].mean()
    spd_b = seg_b['Speed'].mean()
    delta = spd_a - spd_b

    col   = G if delta > 0 else R
    d_str = f"+{delta:.1f}" if delta > 0 else f"{delta:.1f}"
    bar_w = min(int(abs(delta) / 3), 20)
    bar   = f"{col}{'█' * bar_w}{'░' * (20 - bar_w)}{RST}"

    print(f"  {W}MS{i+1:<4}{RST}"
          f"{DIM}{dist_start:.0f}–{dist_end:.0f}m{'':<4}{RST}"
          f"{G}{spd_a:<14.1f}{RST}"
          f"{R}{spd_b:<14.1f}{RST}"
          f"{col}{BOLD}{d_str:<10}{RST}"
          f"{bar}")

print(f"\n  {G}█ GREEN{RST}{DIM}  {drv_a} faster in this zone   "
      f"{RST}{R}█ RED{RST}{DIM}  {drv_b} faster in this zone{RST}")
footer_line()

# ── TIRE DEGRADATION ANALYSIS ─────────────────────────────────────────────────
header("TIRE DEGRADATION  —  TOP 3 DRIVERS", tag("DEG RATE"))

print(f"\n  {DIM}{'DRIVER':<8} {'STINT':<8} {'COMPOUND':<10} {'TYRE AGE':<10} {'LAP TIME':<12} {'DEG RATE'}{RST}")
divider()

for drv in top3_drivers:
    drv_laps = session.laps.pick_drivers(drv).pick_quicklaps().sort_values('LapNumber')
    if drv_laps.empty:
        continue

    stints = drv_laps.groupby('Stint')
    for stint_num, stint_laps in stints:
        if len(stint_laps) < 2:
            continue

        lap_times = stint_laps['LapTime'].dt.total_seconds().values
        tyre_ages = stint_laps['TyreLife'].values
        cmp       = stint_laps['Compound'].iloc[0]
        cc        = compound_color(str(cmp))

        # Deg rate = seconds lost per lap on this compound
        if len(lap_times) >= 2:
            deg_rate = (lap_times[-1] - lap_times[0]) / max(len(lap_times) - 1, 1)
        else:
            deg_rate = 0

        deg_col = G if deg_rate < 0.05 else (Y if deg_rate < 0.15 else R)
        best_lt = str(stint_laps['LapTime'].min())[7:15]

        print(f"  {W}{BOLD}{drv:<8}{RST}"
              f"{DIM}Stint {stint_num:<3}{RST}"
              f"{cc}{compound_icon(str(cmp)):<10}{RST}"
              f"{DIM}{int(tyre_ages[0])}→{int(tyre_ages[-1])} laps{'':<2}{RST}"
              f"{W}{best_lt:<12}{RST}"
              f"{deg_col}{BOLD}{deg_rate:+.3f}s/lap{RST}")

footer_line()

# ── FOOTER ────────────────────────────────────────────────────────────────────
print(f"\n{R}{'█' * W_TOTAL}{RST}")
print(f"{R}██{RST}  {G}{BOLD}✔ TELEMETRY SYSTEM ONLINE  ·  f1-pitwall-ai  ·  v0.2{RST}{'':>14}{R}██{RST}")
print(f"{R}██{RST}  {DIM}Next → python main.py  ·  cd frontend && npm run dev{RST}{'':>13}{R}██{RST}")
print(f"{R}{'█' * W_TOTAL}{RST}\n")

