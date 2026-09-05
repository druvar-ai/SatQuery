"""
Mission Event model for SatQuery simulation timeline.

Events represent significant moments in a mission:
maneuvers, phase transitions, observation windows, etc.
They are defined per-scenario and their status is computed
relative to the current simulation time.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class MissionEvent(BaseModel):
    """A single event on the mission timeline."""
    event_id: str
    name: str = Field(description="Human-readable event name, e.g. 'ΔV1 — Transfer Injection'")
    event_type: Literal[
        "epoch",          # Mission start
        "maneuver",       # Burn / delta-V
        "phase_change",   # Transition between mission phases
        "observation",    # Observation opportunity
        "milestone",      # Generic milestone
    ] = "milestone"
    time_from_epoch_sec: float = Field(description="Seconds from mission epoch when this event occurs")
    spacecraft_id: Optional[str] = None
    description: str = ""
    icon: str = "○"  # Default icon; overridden per type

    def status(self, elapsed_sec: float) -> str:
        """Return 'completed', 'active', or 'upcoming' based on elapsed mission time."""
        # An event is considered 'active' in a small window around its time
        window = 120.0  # 2-minute window
        if elapsed_sec >= self.time_from_epoch_sec + window:
            return "completed"
        elif elapsed_sec >= self.time_from_epoch_sec - window:
            return "active"
        else:
            return "upcoming"

    def status_icon(self, elapsed_sec: float) -> str:
        s = self.status(elapsed_sec)
        if s == "completed":
            return "✓"
        elif s == "active":
            return "→"
        return "○"
