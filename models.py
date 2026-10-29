from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from physiological_models import PhysiologicalProfile, RationComposition, WoodCurvePoint
from financial_roi import FinancialTwinOutput
from edge_gateway import EdgeGatewayState
from vision_twin import VisionCameraAssessment
from rumen_twin import RumenTwinProfile
from robotic_milking_twin import RoboticMilkingTwinProfile
from biogas_energy_twin import FarmEnergyTwinProfile
from barn_robotics_twin import BarnRoboticsFleetProfile
from calving_twin import CowCalvingTwin, FarmMaternitySummary
from genomic_breeding_twin import CowPedigreeProfile, HerdGenomicSummary

class AnimalTelemetry(BaseModel):
    activity_index: int = Field(..., description="Adım / aktivite indeksi (adım/saat)")
    rumination_minutes_2h: int = Field(..., description="Son 2 saatlik geviş getirme süresi (dakika)")
    body_temperature_c: float = Field(..., description="Vücut sıcaklığı (°C)")
    lying_time_hours: float = Field(..., description="Bugünkü toplam yatma süresi (saat)")
    feed_intake_kg: float = Field(..., description="Bugünkü yem tüketimi (kg)")

class MilkingSession(BaseModel):
    timestamp: datetime
    yield_kg: float = Field(..., description="Sağım süt miktarı (kg)")
    conductivity_ms_cm: float = Field(..., description="Süt elektriksel iletkenliği (mS/cm)")
    milking_duration_sec: int = Field(..., description="Sağım süresi (saniye)")

class XAIFactor(BaseModel):
    metric: str
    observed_value: str
    baseline_value: str
    impact_weight: float = Field(..., description="Karara etki ağırlığı (0.0 - 1.0)")
    description: str

class DSSAssessment(BaseModel):
    mastitis_risk_score: float = Field(..., description="Mastitis riski (0.0 - 1.0)")
    heat_stress_level: Literal["NONE", "MILD", "MODERATE", "SEVERE"]
    estrus_probability: float = Field(..., description="Kızgınlık olasılığı (0.0 - 1.0)")
    overall_health_status: Literal["HEALTHY", "WARNING", "CRITICAL"]
    recommended_action: Literal["NONE", "INSPECT_FOR_INSEMINATION", "DIVERT_TO_TREATMENT_PEN", "ACTIVATE_MISTING"]
    xai_explanations: List[XAIFactor] = []

class Animal(BaseModel):
    id: str = Field(..., description="Kulak küpe no (ICAR uyumlu)")
    name: str
    breed: str = "Holstein Friesian"
    lactation_number: int
    days_in_milk: int
    daily_average_yield: float
    current_zone: str
    telemetry: AnimalTelemetry
    latest_milking: MilkingSession
    dss: DSSAssessment
    gate_assignment: Literal["BARN_RETURN", "TREATMENT_PEN", "WAITING"] = "BARN_RETURN"
    history_yield: List[float] = []
    # Faz 2/3 Eklemeleri:
    physiology: PhysiologicalProfile
    lactation_curve: List[WoodCurvePoint] = []
    # Faz 7 Vision AI Eklemeleri:
    vision: Optional[VisionCameraAssessment] = None
    # Faz 8 Rumen & SARA İkizi:
    rumen: Optional[RumenTwinProfile] = None
    # Faz 10 Otonom Robotik Sağım & 4 Loblu Çeyrek İkizi:
    milking_twin: Optional[RoboticMilkingTwinProfile] = None
    # Faz 14 Doğum, Buzağılama & Distosi İkizi:
    calving: Optional[CowCalvingTwin] = None
    # Faz 13 Genomik Seleksiyon & Pedigri İkizi:
    pedigree: Optional[CowPedigreeProfile] = None

class BarnZone(BaseModel):
    zone_id: str
    name: str
    temperature_c: float
    relative_humidity_pct: float
    thi_index: float
    heat_stress_category: Literal["NORMAL", "MILD_STRESS", "MODERATE_STRESS", "SEVERE_STRESS"]
    ventilation_fans_active: bool
    misting_active: bool
    animal_count: int

class SortingGateState(BaseModel):
    gate_id: str = "GATE-01"
    status: Literal["IDLE", "ROUTING_NORMAL", "ROUTING_TREATMENT"] = "IDLE"
    last_diverted_animal_id: Optional[str] = None
    last_reason: Optional[str] = None
    last_updated: datetime

class FarmSustainabilityKPIs(BaseModel):
    total_daily_methane_kg: float = Field(..., description="Çiftlik toplam günlük enterik metan (kg CH4)")
    total_co2e_kg: float = Field(..., description="Toplam günlük CO2 eşdeğeri (kg CO2e)")
    avg_methane_intensity: float = Field(..., description="Ortalama metan yoğunluğu (g CH4 / kg süt)")
    feed_conversion_efficiency: float = Field(..., description="Yemden Yararlanma (kg Süt / kg DMI)")

class FarmTwinState(BaseModel):
    farm_name: str = "AgriTwin Akıllı Süt Çiftliği"
    simulation_tick: int
    simulation_running: bool
    current_time: datetime
    active_scenario: Optional[str] = None
    barn_zones: List[BarnZone]
    animals: List[Animal]
    sorting_gate: SortingGateState
    current_ration: RationComposition
    active_ration_strategy: str = "BALANCED_PARETO"
    sustainability: FarmSustainabilityKPIs
    financials: FinancialTwinOutput
    edge_gateway: EdgeGatewayState
    energy: Optional[FarmEnergyTwinProfile] = None
    robotics: Optional[BarnRoboticsFleetProfile] = None
    # Faz 14 Doğum, Buzağılama & Distosi İkizi:
    maternity: Optional[FarmMaternitySummary] = None
    # Faz 13 Genomik Seleksiyon & Çiftleştirme İkizi:
    genomics: Optional[HerdGenomicSummary] = None
