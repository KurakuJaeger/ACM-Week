import { useState, useEffect } from "react";
import "./App.css";
import Onboarding from "./Onboarding";

interface DriverTelemetry {
  driver: string;
  top_speed: number;
  avg_speed: number;
  min_speed: number;
  max_rpm: number;
  avg_rpm: number;
  gear_shifts: number;
  top_gear: number;
  full_throttle_pct: number;
  brake_events: number;
  drs_activations: number;
  speeds: number[];
  throttles: number[];
  gears: number[];
  distances: number[];
}

interface TelemetrySnapshot {
  type: string;
  timestamp: number;
  drivers: DriverTelemetry[];
}

function App() {
  const [onboardingCompleted, setOnboardingCompleted] = useState(() => {
    return localStorage.getItem('f1-pitwall-onboarding-completed') === 'true';
  });

  const handleOnboardingComplete = () => {
    setOnboardingCompleted(true);
    localStorage.setItem('f1-pitwall-onboarding-completed', 'true');
  };

  if (!onboardingCompleted) {
    return <Onboarding onComplete={handleOnboardingComplete} />;
  }

  const [drivers, setDrivers] = useState<DriverTelemetry[]>([]);
  const [connected, setConnected] = useState(false);
  const [status, setStatus] = useState("Connecting...");
  const [sessionData, setSessionData] = useState<any>(null);
  const [topLaps, setTopLaps] = useState<any>(null);

  // ── WEBSOCKET CONNECTION ──────────────────────────────────────────────
  useEffect(() => {
    const wsUrl = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnected(true);
      setStatus("Connected to Backend");
      console.log("✅ WebSocket connected");
    };

    ws.onmessage = (event) => {
      try {
        const snapshot: TelemetrySnapshot = JSON.parse(event.data);
        if (snapshot.type === "telemetry_update" && snapshot.drivers) {
          setDrivers(snapshot.drivers);
          setStatus(
            `Updated: ${new Date(snapshot.timestamp * 1000).toLocaleTimeString()}`,
          );
        }
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    };

    ws.onerror = () => {
      setConnected(false);
      setStatus("Connection error");
    };

    ws.onclose = () => {
      setConnected(false);
      setStatus("Disconnected");
    };

    return () => ws.close();
  }, []);

  // ── FETCH SESSION DATA ────────────────────────────────────────────────
  useEffect(() => {
    const fetchSession = async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
        const [sessionRes, lapsRes] = await Promise.all([
          fetch(`${apiUrl}/session`),
          fetch(`${apiUrl}/laps?limit=5`),
        ]);

        if (sessionRes.ok) {
          setSessionData(await sessionRes.json());
        }
        if (lapsRes.ok) {
          setTopLaps(await lapsRes.json());
        }
      } catch (e) {
        console.error("Failed to fetch session data:", e);
      }
    };

    fetchSession();
    const interval = setInterval(fetchSession, 10000);
    return () => clearInterval(interval);
  }, []);

  // ── SPARKLINE GENERATOR ───────────────────────────────────────────────
  const sparkline = (values: number[], width = 20): string => {
    if (!values || values.length === 0) return "";
    const bars = " ▁▂▃▄▅▆▇█";
    const mn = Math.min(...values);
    const mx = Math.max(...values);
    const step = Math.max(1, Math.floor(values.length / width));
    const sampled = values.filter((_, i) => i % step === 0).slice(0, width);

    return sampled
      .map((v) => {
        const idx =
          mx === mn
            ? 0
            : Math.floor(((v - mn) / (mx - mn)) * (bars.length - 1));
        return bars[idx];
      })
      .join("");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-8">
      {/* HEADER */}
      <div className="mb-8">
        <div className="flex items-center mb-4">
          <div className="w-12 h-12 bg-gradient-to-r from-red-500 to-red-600 rounded-full flex items-center justify-center text-2xl mr-4 shadow-lg">
            🏎️
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-red-400 via-white to-red-400 bg-clip-text text-transparent">
            🏁 F1-PITWALL-AI
          </h1>
        </div>
        <p className="text-slate-400">Real-time telemetry dashboard</p>
        <div
          className={`mt-2 px-3 py-1 rounded-full text-sm inline-block ${
            connected ? "bg-green-500/20 text-green-400 border border-green-500/30" : "bg-red-500/20 text-red-400 border border-red-500/30"
          }`}
        >
          {connected ? "● Live" : "○ Offline"} — {status}
        </div>
      </div>

      {/* SESSION INFO */}
      {sessionData && (
        <div className="mb-8 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-slate-700/50 to-slate-800/50 p-4 rounded-lg border border-slate-600 hover:border-red-500/50 transition-colors">
            <p className="text-slate-400 text-sm">Event</p>
            <p className="text-xl font-bold text-white">
              {sessionData.season} {sessionData.event}
            </p>
          </div>
          <div className="bg-gradient-to-br from-slate-700/50 to-slate-800/50 p-4 rounded-lg border border-slate-600 hover:border-red-500/50 transition-colors">
            <p className="text-slate-400 text-sm">Session</p>
            <p className="text-xl font-bold text-white">{sessionData.session_type}</p>
          </div>
          <div className="bg-gradient-to-br from-slate-700/50 to-slate-800/50 p-4 rounded-lg border border-slate-600 hover:border-red-500/50 transition-colors">
            <p className="text-slate-400 text-sm">Drivers</p>
            <p className="text-xl font-bold text-white">{sessionData.total_drivers}</p>
          </div>
          <div className="bg-gradient-to-br from-slate-700/50 to-slate-800/50 p-4 rounded-lg border border-slate-600 hover:border-red-500/50 transition-colors">
            <p className="text-slate-400 text-sm">Track Temp</p>
            <p className="text-xl font-bold text-white">{sessionData.track_temp}°C</p>
          </div>
        </div>
      )}

      {/* TOP LAPS */}
      {topLaps && (
        <div className="mb-8 bg-gradient-to-br from-slate-700/30 to-slate-800/30 rounded-lg p-6 border border-slate-600 shadow-lg">
          <h2 className="text-2xl font-bold mb-4 text-white flex items-center">
            <span className="text-red-400 mr-2">🏆</span>
            Top Laps
          </h2>
          <div className="space-y-3">
            {topLaps.laps?.slice(0, 5).map((lap: any, i: number) => (
              <div
                key={i}
                className={`flex justify-between items-center p-3 rounded border transition-all ${
                  i === 0
                    ? 'bg-gradient-to-r from-yellow-500/20 to-yellow-600/20 border-yellow-500/50 shadow-md'
                    : 'bg-slate-800/50 border-slate-600 hover:border-red-500/30'
                }`}
              >
                <div>
                  <p className={`font-bold ${i === 0 ? 'text-yellow-400' : 'text-white'}`}>
                    {i + 1}. {lap.driver}
                  </p>
                  <p className="text-sm text-slate-400">{lap.team}</p>
                </div>
                <div className="text-right">
                  <p className={`font-bold text-lg ${i === 0 ? 'text-yellow-400' : 'text-white'}`}>
                    {lap.lap_time?.toFixed(3)}s
                  </p>
                  <p className="text-sm text-slate-400">
                    {lap.gap_to_pole === 0
                      ? "POLE"
                      : `+${lap.gap_to_pole?.toFixed(3)}s`}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* LIVE TELEMETRY */}
      {drivers.length > 0 && (
        <div className="mb-8 bg-gradient-to-br from-slate-700/30 to-slate-800/30 rounded-lg p-6 border border-slate-600 shadow-lg">
          <h2 className="text-2xl font-bold mb-4 text-white flex items-center">
            <span className="text-red-400 mr-2">📡</span>
            Live Telemetry
          </h2>
          <div className="space-y-6">
            {drivers.map((drv) => (
              <div
                key={drv.driver}
                className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-4 rounded border border-slate-600 hover:border-red-500/30 transition-colors"
              >
                <h3 className="text-xl font-bold mb-4 text-white flex items-center">
                  <span className="text-red-400 mr-2">🏎️</span>
                  {drv.driver}
                </h3>

                {/* Speed Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div>
                    <p className="text-slate-400 text-xs">Top Speed</p>
                    <p className="text-lg font-bold">{drv.top_speed} km/h</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-xs">Avg Speed</p>
                    <p className="text-lg font-bold">{drv.avg_speed} km/h</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-xs">Max RPM</p>
                    <p className="text-lg font-bold">{drv.max_rpm}</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-xs">Full Throttle</p>
                    <p className="text-lg font-bold">
                      {drv.full_throttle_pct.toFixed(1)}%
                    </p>
                  </div>
                </div>

                {/* Speed Trace */}
                <div className="mb-4">
                  <p className="text-slate-400 text-xs mb-2">Speed Trace</p>
                  <p className="font-mono text-green-400">
                    {sparkline(drv.speeds)}
                  </p>
                </div>

                {/* Throttle Trace */}
                <div className="mb-4">
                  <p className="text-slate-400 text-xs mb-2">Throttle Map</p>
                  <p className="font-mono text-yellow-400">
                    {sparkline(drv.throttles)}
                  </p>
                </div>

                {/* Gear Trace */}
                <div className="mb-4">
                  <p className="text-slate-400 text-xs mb-2">
                    Gear Progression
                  </p>
                  <p className="font-mono text-blue-400">
                    {sparkline(drv.gears)}
                  </p>
                </div>

                {/* Other Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  <div>
                    <p className="text-slate-400 text-xs">Gear Shifts</p>
                    <p className="font-bold">{drv.gear_shifts}</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-xs">Brake Events</p>
                    <p className="font-bold">{drv.brake_events}</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-xs">DRS Uses</p>
                    <p className="font-bold">{drv.drs_activations}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!connected && (
        <div className="text-center p-8 bg-gradient-to-br from-red-500/10 to-red-600/10 rounded-lg border border-red-500/30 shadow-lg">
          <div className="text-4xl mb-4">🏁</div>
          <p className="text-red-400 mb-2 text-lg font-semibold">Waiting for Backend connection...</p>
          <p className="text-slate-400 text-sm">
            Make sure the Backend server is running on port 8000
          </p>
          <div className="mt-4 flex justify-center">
            <div className="animate-pulse w-4 h-4 bg-red-500 rounded-full"></div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
