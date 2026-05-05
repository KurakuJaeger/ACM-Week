#NOTE: This file contains the AI coaching engine for the F1 Pitwall system demo not the officia or real one okay PIPOY :)))

import os
import json
import asyncio
from typing import Optional
from dotenv import load_dotenv
from anthropic import Anthropic
from data_models import CoachingPayload

load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not set in .env")

client = Anthropic()

# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an elite F1 race engineer and coaching AI for the Pitwall system.
Your role is to provide brief, actionable coaching insights to drivers based on real-time telemetry data.

Format your response as JSON with these fields:
{
  "insight": "1-2 sentence coaching tip focused on the specific metric",
  "action": "1 specific action the driver should take",
  "sector": "which sector this applies to (1, 2, or 3)",
  "priority": "high" | "medium" | "low"
}

Be specific, technical, and practical. Focus on:
- Sector-by-sector improvement opportunities
- Throttle and brake optimization
- Tyre management and degradation trends
- Gap analysis vs leader
- Speed consistency

Keep responses concise and actionable."""

# ── COACHING ENGINE ───────────────────────────────────────────────────────────
def generate_coaching(payload: CoachingPayload) -> dict:
    """
    Takes a CoachingPayload and returns Claude-generated coaching insights.
    
    Args:
        payload: Driver telemetry and lap data
        
    Returns:
        dict with coaching insight, action, sector, and priority
    """
    prompt = f"""
    Driver: {payload.driver}
    Lap: {payload.lap_number}
    Lap Time: {payload.lap_time:.3f}s
    
    Sector Deltas:
    - Sector 1: {payload.s1_delta:+.3f}s
    - Sector 2: {payload.s2_delta:+.3f}s
    - Sector 3: {payload.s3_delta:+.3f}s
    
    Telemetry:
    - Tyre: {payload.tyre_compound} (Age: {payload.tyre_age} laps)
    - Gap to Leader: {payload.gap_to_leader:+.3f}s
    - Top Speed: {payload.top_speed:.0f} km/h
    - Avg Throttle: {payload.avg_throttle:.1f}%
    - Brake Events: {payload.brake_events}
    
    Provide coaching feedback to help {payload.driver} improve this lap.
    """
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=200,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.content[0].text
        
        # Try to parse JSON response
        try:
            coaching = json.loads(content)
        except json.JSONDecodeError:
            # Fallback if Claude doesn't return valid JSON
            coaching = {
                "insight": content[:100],
                "action": "Review telemetry and adjust accordingly",
                "sector": 1,
                "priority": "medium"
            }
        
        return coaching
    
    except Exception as e:
        print(f"  ✗ Claude API error: {str(e)}")
        return {
            "insight": "Unable to generate coaching at this time",
            "action": "Continue monitoring telemetry",
            "sector": 1,
            "priority": "low"
        }

# ── STREAMING COACH ───────────────────────────────────────────────────────────
def stream_coaching(payload: CoachingPayload):
    """
    Stream coaching feedback with streaming API for real-time display.
    Yields chunks of the response as they arrive from Claude.
    """
    prompt = f"""
    Driver: {payload.driver}
    Lap: {payload.lap_number}
    Lap Time: {payload.lap_time:.3f}s
    Gap to Leader: {payload.gap_to_leader:+.3f}s
    Sector Deltas: S1 {payload.s1_delta:+.3f}s | S2 {payload.s2_delta:+.3f}s | S3 {payload.s3_delta:+.3f}s
    Tyre: {payload.tyre_compound} ({payload.tyre_age}L) | Speed: {payload.top_speed:.0f}km/h | Throttle: {payload.avg_throttle:.1f}%
    
    Give {payload.driver} brief, actionable coaching in JSON format.
    """
    
    try:
        with client.messages.stream(
            model="claude-3-5-sonnet-20241022",
            max_tokens=200,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": prompt}
            ]
        ) as stream:
            for text in stream.text_stream:
                yield text
    
    except Exception as e:
        yield json.dumps({"error": str(e)})

# ── CONVERSATION MODE ────────────────────────────────────────────────────────
class CoachingSession:
    """
    Maintains conversation history for multi-turn coaching sessions.
    Allows back-and-forth discussion about driver performance.
    """
    def __init__(self, driver: str):
        self.driver = driver
        self.conversation_history = []
    
    def chat(self, message: str) -> str:
        """
        Send a message and get a response from the coach.
        Maintains full conversation history.
        """
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                system=f"You are an F1 race engineer coaching {self.driver}. Provide detailed, technical feedback.",
                messages=self.conversation_history
            )
            
            assistant_message = response.content[0].text
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return assistant_message
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    def clear_history(self):
        """Clear conversation history to start fresh."""
        self.conversation_history = []

# ── BATCH ANALYSIS ───────────────────────────────────────────────────────────
def analyze_multiple_drivers(payloads: list[CoachingPayload]) -> list[dict]:
    """
    Analyze telemetry for multiple drivers in one API call.
    More efficient than calling generate_coaching multiple times.
    """
    drivers_text = "\n\n".join([
        f"Driver: {p.driver} | Lap: {p.lap_number} | Time: {p.lap_time:.3f}s | Gap: {p.gap_to_leader:+.3f}s"
        for p in payloads
    ])
    
    prompt = f"""
    Analyze telemetry for multiple drivers and provide coaching for each:
    
    {drivers_text}
    
    Return a JSON array with coaching for each driver in order.
    """
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.content[0].text
        try:
            results = json.loads(content)
            if not isinstance(results, list):
                results = [results]
        except json.JSONDecodeError:
            results = [{"insight": content, "action": "Review", "sector": 1, "priority": "medium"}]
        
        return results
    
    except Exception as e:
        print(f"  ✗ Batch analysis error: {str(e)}")
        return [{"error": str(e)} for _ in payloads]

# ── CLI TEST ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test the AI coach with sample data
    print("\n" + "█" * 60)
    print("██  F1-PITWALL-AI  ·  COACHING ENGINE  ·  TEST MODE")
    print("█" * 60 + "\n")
    
    sample_payload = CoachingPayload(
        driver="VER",
        lap_number=25,
        lap_time=92.345,
        s1_delta=-0.125,
        s2_delta=0.043,
        s3_delta=-0.087,
        tyre_compound="HARD",
        tyre_age=12,
        gap_to_leader=0.156,
        top_speed=324.5,
        avg_throttle=78.3,
        brake_events=14
    )
    
    print("  Generating coaching for VER...")
    coaching = generate_coaching(sample_payload)
    print(f"\n  Insight: {coaching.get('insight')}")
    print(f"  Action: {coaching.get('action')}")
    print(f"  Sector: {coaching.get('sector')}")
    print(f"  Priority: {coaching.get('priority')}")
    
    print("\n" + "█" * 60)
    print("██  Testing complete")
    print("█" * 60 + "\n")
