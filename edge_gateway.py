from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

class VeterinaryTreatment(BaseModel):
    animal_id: str
    diagnosis: str
    drug_administered: str
    dosage: str
    prescribed_at: datetime
    withdrawal_period_days: int = Field(5, description="Süte geçiş süresi / arınma süresi (gün)")
    milk_tank_lock_active: bool = True
    milk_disposal_divert_active: bool = True

class EdgeGatewayState(BaseModel):
    is_online: bool = True
    connection_mode: str = "CLOUD_CONNECTED"  # CLOUD_CONNECTED, OFFLINE_EDGE_FALLBACK, SYNCING
    offline_buffered_packets: int = 0
    local_fail_safe_actuations_count: int = 0
    last_sync_timestamp: Optional[datetime] = None
    active_treatments: List[VeterinaryTreatment] = []

class EdgeGatewayEngine:
    def __init__(self):
        self.state = EdgeGatewayState(
            is_online=True,
            connection_mode="CLOUD_CONNECTED",
            offline_buffered_packets=0,
            local_fail_safe_actuations_count=0,
            last_sync_timestamp=datetime.now(),
            active_treatments=[]
        )
        self.buffer: List[Dict[str, Any]] = []

    def toggle_connection(self) -> EdgeGatewayState:
        """Kırsal internet bağlantısını kesme veya yeniden bağlama simülasyonu"""
        self.state.is_online = not self.state.is_online
        if not self.state.is_online:
            self.state.connection_mode = "OFFLINE_EDGE_FALLBACK"
        else:
            self.state.connection_mode = "SYNCING"
            # Flush buffer
            self.state.offline_buffered_packets = 0
            self.state.last_sync_timestamp = datetime.now()
            self.state.connection_mode = "CLOUD_CONNECTED"
        return self.state

    def process_telemetry_packet(self, packet: Dict[str, Any], conductivity: float) -> Optional[str]:
        """Edge katmanında yerel eşik kontrolü ve tamponlama"""
        actuation_triggered = None
        if not self.state.is_online:
            self.buffer.append(packet)
            self.state.offline_buffered_packets = len(self.buffer)

            # Local Fail-Safe Rule (Edge Kuralı): İnternet olmasa bile yüksek iletkenlikte kapıyı hemen aç
            if conductivity > 6.2:
                self.state.local_fail_safe_actuations_count += 1
                actuation_triggered = "LOCAL_FAILSAFE_ROUTING_TREATMENT"

        return actuation_triggered

    def add_treatment(self, animal_id: str, drug: str, days: int = 5) -> VeterinaryTreatment:
        treatment = VeterinaryTreatment(
            animal_id=animal_id,
            diagnosis="Subklinik Mastitis (Enflamasyon)",
            drug_administered=drug,
            dosage="10 ml İntramammar",
            prescribed_at=datetime.now(),
            withdrawal_period_days=days,
            milk_tank_lock_active=True,
            milk_disposal_divert_active=True
        )
        self.state.active_treatments.append(treatment)
        return treatment

    def get_animal_treatment(self, animal_id: str) -> Optional[VeterinaryTreatment]:
        return next((t for t in self.state.active_treatments if t.animal_id == animal_id), None)

# Global Edge Gateway Singleton
edge_gateway = EdgeGatewayEngine()
