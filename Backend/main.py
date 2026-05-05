import os
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import fastf1
import pandas as pd
import sys
from pathlib import Path as PathlibPath
sys.path.insert(0, str(PathlibPath(__file__).parent))
from data_models import (
    LapData, DriverTelemetry, TireStint,
    CornerDelta, SessionInfo, CoachingPayload
)

# ── CONFIG ────────────────────────────────────────────────────────────────────
load_dotenv()
BASE_DIR  = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / os.getenv("CACHE_DIR", "cache")
CACHE_DIR.mkdir(exist_ok=True)
SEASON    = int(os.getenv("F1_SEASON", 2026))
EVENT     = os.getenv("F1_EVENT", "Suzuka")
SESSION   = os.getenv("F1_SESSION", "Q")

fastf1.Cache.enable_cache(str(CACHE_DIR))

# ── APP INIT ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "F1-Pitwall-AI",
    description = "Real-time F1 telemetry API with AI race engineer coaching",
    version     = "0.2.0"
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:5173",
                         "http://localhost:5174",
                         "http://localhost:5175"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── SESSION CACHE ─────────────────────────────────────────────────────────────
# Stores the loaded session in memory so every
# endpoint doesn't reload it from disk each time
_session_cache = {}

def get_session():
    key = f"{SEASON}_{EVENT}_{SESSION}"
    if key not in _session_cache:
        print(f"  Loading session: {SEASON} {EVENT} {SESSION}...")
        session = fastf1.get_session(SEASON, EVENT, SESSION)
        session.load(telemetry=True, laps=True, weather=True)
        _session_cache[key] = session
        print(f"  ✔ Session cached")
    return _session_cache[key]

# ── WEBSOCKET MANAGER ─────────────────────────────────────────────────────────
# Manages multiple connected frontend clients
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        print(f"  ● Client connected  ·  total: {len(self.active)}")

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)
        print(f"  ○ Client disconnected  ·  total: {len(self.active)}")

    async def broadcast(self, data: dict):
        disconnected = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.active.remove(ws)

manager = ConnectionManager()

# ── HELPERS ───────────────────────────────────────────────────────────────────
def lap_to_dict(lap) -> dict:
    return {
        "driver":     lap['Driver'],
        "team":       str(lap['Team']),
        "lap_number": int(lap['LapNumber']) if pd.notna(lap['LapNumber']) else 0,
        "lap_time":   lap['LapTime'].total_seconds() if pd.notna(lap['LapTime']) else None,
        "sector1":    lap['Sector1Time'].total_seconds() if pd.notna(lap['Sector1Time']) else None,
        "sector2":    lap['Sector2Time'].total_seconds() if pd.notna(lap['Sector2Time']) else None,
        "sector3":    lap['Sector3Time'].total_seconds() if pd.notna(lap['Sector3Time']) else None,
        "compound":   str(lap['Compound']) if pd.notna(lap['Compound']) else "—",
        "tyre_life":  int(lap['TyreLife']) if pd.notna(lap['TyreLife']) else 0,
        "fresh_tyre": bool(lap['FreshTyre']) if pd.notna(lap['FreshTyre']) else False,
    }

def telemetry_to_dict(driver: str, session) -> dict:
    lap = session.laps.pick_drivers(driver).pick_fastest()
    tel = lap.get_telemetry()
    return {
        "driver":           driver,
        "top_speed":        round(float(tel['Speed'].max()), 2),
        "avg_speed":        round(float(tel['Speed'].mean()), 2),
        "min_speed":        round(float(tel['Speed'].min()), 2),
        "max_rpm":          round(float(tel['RPM'].max()), 0),
        "avg_rpm":          round(float(tel['RPM'].mean()), 0),
        "gear_shifts":      int((tel['nGear'].diff().abs() > 0).sum()),
        "top_gear":         int(tel['nGear'].max()),
        "full_throttle_pct":round(float((tel['Throttle'] == 100).sum() / len(tel) * 100), 2),
        "brake_events":     int(tel['Brake'].sum()),
        "drs_activations":  int(tel['DRS'].sum()),
        "speeds":           tel['Speed'].tolist(),
        "throttles":        tel['Throttle'].tolist(),
        "gears":            tel['nGear'].tolist(),
        "distances":        tel['Distance'].tolist() if 'Distance' in tel.columns else [],
    }

# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status":  "online",
        "app":     "f1-pitwall-ai",
        "version": "0.2.0",
        "docs":    "/docs"
    }

@app.get("/session")
def get_session_info():
    session = get_session()
    evt     = session.event
    wx      = session.weather_data
    return {
        "season":        SEASON,
        "event":         EVENT,
        "session_type":  SESSION,
        "circuit":       str(evt['Location']),
        "country":       str(evt['Country']),
        "round":         int(evt['RoundNumber']),
        "date":          str(session.date)[:10],
        "total_drivers": len(session.drivers),
        "total_laps":    len(session.laps),
        "air_temp":      round(float(wx['AirTemp'].mean()), 1),
        "track_temp":    round(float(wx['TrackTemp'].mean()), 1),
        "humidity":      round(float(wx['Humidity'].mean()), 1),
        "rainfall":      bool(wx['Rainfall'].any()),
    }

@app.get("/laps")
def get_top_laps(limit: int = 10):
    session = get_session()
    top     = session.laps.pick_quicklaps().sort_values('LapTime').head(limit)
    pole    = top.iloc[0]['LapTime']
    result  = []
    for _, lap in top.iterrows():
        d = lap_to_dict(lap)
        d['gap_to_pole'] = round(
            (lap['LapTime'] - pole).total_seconds(), 3
        ) if pd.notna(lap['LapTime']) else None
        result.append(d)
    return {"laps": result, "total": len(result)}

@app.get("/telemetry/{driver}")
def get_driver_telemetry(driver: str):
    session = get_session()
    try:
        data = telemetry_to_dict(driver.upper(), session)
        return data
    except Exception as e:
        return {"error": str(e), "driver": driver}

@app.get("/compare")
def compare_drivers(driver_a: str, driver_b: str, sectors: int = 20):
    session  = get_session()
    try:
        lap_a    = session.laps.pick_drivers(driver_a.upper()).pick_fastest()
        lap_b    = session.laps.pick_drivers(driver_b.upper()).pick_fastest()
        tel_a    = lap_a.get_car_data().add_distance()
        tel_b    = lap_b.get_car_data().add_distance()
        max_dist = min(tel_a['Distance'].max(), tel_b['Distance'].max())
        sec_size = max_dist / sectors
        deltas   = []
        for i in range(sectors):
            start = i * sec_size
            end   = (i + 1) * sec_size
            seg_a = tel_a[(tel_a['Distance'] >= start) & (tel_a['Distance'] < end)]
            seg_b = tel_b[(tel_b['Distance'] >= start) & (tel_b['Distance'] < end)]
            if seg_a.empty or seg_b.empty:
                continue
            deltas.append({
                "sector":     i + 1,
                "dist_start": round(float(start), 1),
                "dist_end":   round(float(end), 1),
                "speed_a":    round(float(seg_a['Speed'].mean()), 2),
                "speed_b":    round(float(seg_b['Speed'].mean()), 2),
                "delta":      round(float(seg_a['Speed'].mean() - seg_b['Speed'].mean()), 2),
            })
        return {
            "driver_a": driver_a.upper(),
            "driver_b": driver_b.upper(),
            "sectors":  deltas
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/tires")
def get_tire_data():
    session     = get_session()
    top_drivers = session.laps.pick_quicklaps().sort_values(
        'LapTime')['Driver'].unique()[:5]
    result      = []
    for drv in top_drivers:
        drv_laps = session.laps.pick_drivers(drv).pick_quicklaps().sort_values('LapNumber')
        if drv_laps.empty:
            continue
        for stint_num, stint_laps in drv_laps.groupby('Stint'):
            if len(stint_laps) < 1:
                continue
            lap_times = stint_laps['LapTime'].dt.total_seconds().values
            tyre_ages = stint_laps['TyreLife'].values
            cmp       = str(stint_laps['Compound'].iloc[0])
            deg_rate  = float((lap_times[-1] - lap_times[0]) /
                        max(len(lap_times) - 1, 1)) if len(lap_times) >= 2 else 0.0
            result.append({
                "driver":       drv,
                "stint":        int(stint_num),
                "compound":     cmp,
                "start_lap":    int(tyre_ages[0]),
                "end_lap":      int(tyre_ages[-1]),
                "tyre_age":     int(tyre_ages[-1] - tyre_ages[0]),
                "best_lap":     round(float(stint_laps['LapTime'].min().total_seconds()), 3),
                "deg_rate":     round(deg_rate, 4),
            })
    return {"stints": result, "total": len(result)}

@app.get("/weather")
def get_weather():
    session = get_session()
    wx      = session.weather_data
    return {
        "air_temp":      round(float(wx['AirTemp'].mean()), 1),
        "track_temp":    round(float(wx['TrackTemp'].mean()), 1),
        "humidity":      round(float(wx['Humidity'].mean()), 1),
        "pressure":      round(float(wx['Pressure'].mean()), 1),
        "wind_speed":    round(float(wx['WindSpeed'].mean()), 1),
        "wind_direction":round(float(wx['WindDirection'].mean()), 0),
        "rainfall":      bool(wx['Rainfall'].any()),
        "track_temps":   wx['TrackTemp'].tolist(),
        "air_temps":     wx['AirTemp'].tolist(),
    }

# ── WEBSOCKET ─────────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        session = get_session()
        while True:
            # Build live telemetry snapshot
            top_laps = session.laps.pick_quicklaps().sort_values('LapTime').head(3)
            drivers  = top_laps['Driver'].unique()[:2]

            snapshot = {
                "type":      "telemetry_update",
                "timestamp": asyncio.get_event_loop().time(),
                "drivers":   []
            }

            for drv in drivers:
                try:
                    snapshot["drivers"].append(
                        telemetry_to_dict(drv, session)
                    )
                except Exception:
                    pass

            await ws.send_json(snapshot)
            await asyncio.sleep(2)

    except WebSocketDisconnect:
        manager.disconnect(ws)

# ── STARTUP ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    print("\n" + "█" * 50)
    print("██  F1-PITWALL-AI  ·  SERVER STARTING  ·  v0.2")
    print("█" * 50)
    print(f"  Docs available at: http://localhost:8000/docs")
    print(f"  Season: {SEASON}  Event: {EVENT}  Session: {SESSION}")
    print("█" * 50 + "\n")
