import os
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("OPENF1_BASE_URL", "https://api.openf1.org/v1")

# ANSI colors
R = "\033[91m"; G = "\033[92m"; Y = "\033[93m"
W = "\033[97m"; DIM = "\033[2m"; BOLD = "\033[1m"; RST = "\033[0m"

def fetch_latest_laps():
    try:
        r = httpx.get(f"{BASE_URL}/laps?session_key=latest", timeout=10)
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        print(f"  {R}Feed error: {e}{RST}")
        return []

def fetch_driver_positions():
    try:
        r = httpx.get(f"{BASE_URL}/position?session_key=latest", timeout=10)
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        print(f"  {R}Position error: {e}{RST}")
        return []

def fetch_intervals():
    try:
        r = httpx.get(f"{BASE_URL}/intervals?session_key=latest", timeout=10)
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        print(f"  {R}Interval error: {e}{RST}")
        return []

def fetch_car_data(driver_number):
    try:
        r = httpx.get(
            f"{BASE_URL}/car_data?driver_number={driver_number}&session_key=latest",
            timeout=10
        )
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        print(f"  {R}Car data error: {e}{RST}")
        return []

def poll_live_session(interval_seconds=5):
    print(f"\n{R}{'█' * 60}{RST}")
    print(f"{R}██{RST}  {BOLD}{W}F1-PITWALL-AI  ·  LIVE FEED  ·  OpenF1{RST}  {R}██{RST}")
    print(f"{R}{'█' * 60}{RST}\n")
    print(f"  {G}● LIVE{RST}  Polling OpenF1 every {interval_seconds}s  ·  Ctrl+C to stop\n")

    tick = 0
    while True:
        tick += 1
        print(f"  {DIM}─── Tick {tick}  ·  {time.strftime('%H:%M:%S')} ───{RST}")

        laps = fetch_latest_laps()
        if laps:
            latest = laps[-1]
            print(f"  {W}Latest lap  ·  "
                  f"Driver: {G}{latest.get('driver_number','—')}{RST}  "
                  f"Lap: {Y}{latest.get('lap_number','—')}{RST}  "
                  f"Time: {G}{latest.get('lap_duration','—')}{RST}s")
        else:
            print(f"  {Y}No live lap data  ·  session may be between runs{RST}")

        positions = fetch_driver_positions()
        if positions:
            print(f"  {DIM}Positions received: {len(positions)} entries{RST}")

        intervals = fetch_intervals()
        if intervals:
            print(f"  {DIM}Intervals received: {len(intervals)} entries{RST}")

        print()
        time.sleep(interval_seconds)

if __name__ == "__main__":
    poll_live_session()