# backend/data/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

# 1. DETERMINISTIC METRICS (Hard sensor telemetry/values)
class TankerTelemetry(BaseModel):
    tanker_name: str
    imo_number: int
    latitude: float
    longitude: float
    current_knots: float
    heading_degrees: float
    remaining_fuel_days: float

# 2. DETERMINISTIC STRUCTURED DATA (Official digital documentation)
class CargoManifest(BaseModel):
    manifest_id: str
    vessel_name: str
    crude_grade: str
    cargo_volume_barrels: int
    origin_wellhead: str
    destination_port: str
    chemical_profile: Dict[str, float] = Field(..., description="Contains sulfur_pct and api_gravity keys")

# 3. NONDETERMINISTIC METRICS (Derived probablistic metrics)
class CorridorRiskAssessment(BaseModel):
    zone_id: str
    sentiment_index: float = Field(..., ge=-1.0, le=1.0, description="-1.0 highly hostile, 1.0 completely peaceful")
    calculated_disruption_probability: float = Field(..., ge=0.0, le=1.0)
    chaos_monkey_override: bool = False

# 4. NONDETERMINISTIC UNSTRUCTURED DATA (Raw textual streams)
class GeopoliticalIntelligenceDispatch(BaseModel):
    source_agency: str
    timestamp: str
    raw_text: str
    inferred_locations: List[str]
    threat_level_tag: str  # LOW, MEDIUM, CRITICAL
# backend/data/models.py (Append to the bottom of the file)

class BlackSwanCrisisInjection(BaseModel):
    target_chokepoint: str  # e.g., "Strait_of_Hormuz" or "Red_Sea"
    simulated_intensity: float  # scale from 0.0 to 1.0
    compromise_domestic_pipeline: bool  # Simulates an additional simultaneous onshore cyber/physical asset strike