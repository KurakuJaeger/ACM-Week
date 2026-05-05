from dataclasses import dataclass, field
from typing import Optional, List
from datetime import timedelta

@dataclass
class LapData:
    driver:       str
    team:         str
    lap_number:   int
    lap_time:     float          # seconds
    sector1:      Optional[float]
    sector2:      Optional[float]
    sector3:      Optional[float]
    compound:     str
    tyre_life:    int
    fresh_tyre:   bool
    is_personal_best: bool = False

@dataclass
class DriverTelemetry:
    driver:       str
    top_speed:    float
    avg_speed:    float
    min_speed:    float
    max_rpm:      float
    avg_rpm:      float
    gear_shifts:  int
    top_gear:     int
    full_throttle_pct: float
    brake_events: int
    drs_activations: int
    speeds:       List[float] = field(default_factory=list)
    throttles:    List[float] = field(default_factory=list)
    gears:        List[float] = field(default_factory=list)
    distances:    List[float] = field(default_factory=list)

@dataclass
class TireStint:
    driver:       str
    stint_number: int
    compound:     str
    start_lap:    int
    end_lap:      int
    tyre_age:     int
    best_lap:     float          # seconds
    deg_rate:     float          # seconds lost per lap

@dataclass
class CornerDelta:
    sector_index: int
    dist_start:   float
    dist_end:     float
    speed_a:      float
    speed_b:      float
    delta:        float          # positive = driver A faster

@dataclass
class SessionInfo:
    season:       int
    event:        str
    session_type: str
    circuit:      str
    country:      str
    date:         str
    total_drivers: int
    total_laps:   int
    air_temp:     float
    track_temp:   float
    rainfall:     bool

@dataclass
class CoachingPayload:
    driver:       str
    lap_number:   int
    lap_time:     float
    s1_delta:     float
    s2_delta:     float
    s3_delta:     float
    tyre_compound: str
    tyre_age:     int
    gap_to_leader: float
    top_speed:    float
    avg_throttle: float
    brake_events: int