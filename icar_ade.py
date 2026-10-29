from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ICARDocumentHeader(BaseModel):
    specification_version: str = "2.0.0"
    document_id: str
    created_timestamp: datetime
    sending_system: str = "AgriTwin-EdgeCore-v2"
    source_farm_id: str = "TR-34-AGRITWIN-01"

class ICARAnimalIdentification(BaseModel):
    country_code: str = "TR"
    visual_id: str
    electronic_id: Optional[str] = None
    species: str = "BOVINE"
    breed: str = "HOL"  # Holstein
    sex: str = "FEMALE"

class ICARMilkRecording(BaseModel):
    recording_timestamp: datetime
    milking_session_id: str
    milk_yield_kg: float
    conductivity_ms_cm: float
    milking_duration_seconds: int

class ICARSensorObservation(BaseModel):
    observation_type: str  # RUMINATION, ACTIVITY_INDEX, BODY_TEMP, LYING_TIME
    observation_timestamp: datetime
    value: float
    unit_of_measure: str

class ICARHealthEvent(BaseModel):
    event_timestamp: datetime
    diagnostic_category: str  # e.g., MASTITIS_SUBCLINICAL, ESTRUS_DETECTED, HEAT_STRESS
    risk_score: float
    recommended_action: str
    sorting_gate_target: str

class ICARADEAnimalRecord(BaseModel):
    animal: ICARAnimalIdentification
    days_in_milk: int
    lactation_number: int
    milk_recordings: List[ICARMilkRecording] = []
    sensor_observations: List[ICARSensorObservation] = []
    health_events: List[ICARHealthEvent] = []

class ICARDocument(BaseModel):
    header: ICARDocumentHeader
    records: List[ICARADEAnimalRecord]

class ICARADEAdapter:
    """
    ICAR Animal Data Exchange (ADE) Standart Dönüştürücü ve Doğrulayıcı Adaptörü
    """

    @staticmethod
    def export_to_icar_ade(animals: List[Any], farm_id: str = "TR-34-AGRITWIN-01") -> Dict[str, Any]:
        """Çiftlikteki hayvan ikizlerini standart ICAR ADE formatına seri hale getirir"""
        now = datetime.now()
        doc_header = ICARDocumentHeader(
            document_id=f"ADE-EXPORT-{int(now.timestamp())}",
            created_timestamp=now,
            source_farm_id=farm_id
        )

        records = []
        for a in animals:
            ident = ICARAnimalIdentification(
                visual_id=a.id,
                electronic_id=f"982000{a.id.replace('TR-34-', '')}"
            )

            # Milk recording
            milk = ICARMilkRecording(
                recording_timestamp=a.latest_milking.timestamp,
                milking_session_id=f"MILK-{a.id}-{int(a.latest_milking.timestamp.timestamp())}",
                milk_yield_kg=a.latest_milking.yield_kg,
                conductivity_ms_cm=a.latest_milking.conductivity_ms_cm,
                milking_duration_seconds=a.latest_milking.milking_duration_sec
            )

            # Sensor observations
            obs = [
                ICARSensorObservation(
                    observation_type="RUMINATION_TIME_2H",
                    observation_timestamp=now,
                    value=float(a.telemetry.rumination_minutes_2h),
                    unit_of_measure="MINUTES"
                ),
                ICARSensorObservation(
                    observation_type="ACTIVITY_INDEX",
                    observation_timestamp=now,
                    value=float(a.telemetry.activity_index),
                    unit_of_measure="STEPS_PER_HOUR"
                ),
                ICARSensorObservation(
                    observation_type="BODY_TEMPERATURE",
                    observation_timestamp=now,
                    value=float(a.telemetry.body_temperature_c),
                    unit_of_measure="DEGREES_CELSIUS"
                )
            ]

            # Health events
            events = []
            if a.dss.overall_health_status != "HEALTHY":
                events.append(ICARHealthEvent(
                    event_timestamp=now,
                    diagnostic_category="MASTITIS_RISK" if a.dss.mastitis_risk_score > 0.5 else "ESTRUS_ALERT",
                    risk_score=max(a.dss.mastitis_risk_score, a.dss.estrus_probability),
                    recommended_action=a.dss.recommended_action,
                    sorting_gate_target=a.gate_assignment
                ))

            record = ICARADEAnimalRecord(
                animal=ident,
                days_in_milk=a.days_in_milk,
                lactation_number=a.lactation_number,
                milk_recordings=[milk],
                sensor_observations=obs,
                health_events=events
            )
            records.append(record)

        doc = ICARDocument(header=doc_header, records=records)
        return doc.model_dump(mode="json")
