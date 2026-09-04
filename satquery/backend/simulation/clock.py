from datetime import datetime, timedelta
from pydantic import BaseModel, Field

class SimulationClock(BaseModel):
    current_time: datetime
    start_time: datetime
    end_time: datetime
    timestep_seconds: float = 60.0
    speed: float = 1.0
    running: bool = False
    
    def step(self, force: bool = False):
        if (self.running or force) and self.current_time < self.end_time:
            self.current_time += timedelta(seconds=self.timestep_seconds)
            
    def play(self):
        self.running = True
        
    def pause(self):
        self.running = False
        
    def reset(self):
        self.current_time = self.start_time
        self.running = False
