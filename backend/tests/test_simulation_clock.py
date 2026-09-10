import time
from app.services.clock_service import SimulationClock
from app.models.simulation import ClockStatus

def test_simulation_clock_lifecycle():
    clock = SimulationClock()
    assert clock.status == ClockStatus.STOPPED
    
    clock.start(config_id="config-123", scenario="MULE_FAN_IN")
    assert clock.status == ClockStatus.RUNNING
    assert clock.active_scenario == "MULE_FAN_IN"
    
    # Speed multiplier
    clock.set_speed(10.0)
    assert clock.simulation_speed == 10.0
    
    clock.pause()
    assert clock.status == ClockStatus.PAUSED
    
    clock.resume()
    assert clock.status == ClockStatus.RUNNING
    
    clock.reset()
    assert clock.status == ClockStatus.STOPPED
    assert clock.active_config_id is None
