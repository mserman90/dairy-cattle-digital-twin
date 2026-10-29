"""
AgriTwin: Otonom Robotik Sağım & 4 Loblu Çeyrek Meme (Quarter-Level)
Spektroskopik / Somatik Hücre (SCC) Dijital İkizi
(DeLaval VMS / Lely Astronaut / GEA DairyRobot Mimarisi)

Özellikler:
- 4 Ayrı Meme Lobu (RF: Sağ Ön, RR: Sağ Arka, LF: Sol Ön, LR: Sol Arka)
- Lob bazında bağımsız süt iletkenliği (Conductivity, mS/cm)
- Hat içi optik spektrometre ile Somatik Hücre Sayısı (SCC, hücre/mL)
- Lob bazında kızılötesi kan dedektörü (Blood in milk, ppm)
- Otomatik Çeyrek Süt Ayrımı (Quarter-Milk Diversion): Yalnızca enfekte lobun sütü atık hattına sevk edilir, sağlıklı 3 lob ana tanka gider!
- Meme başı hiperkeratoz (Teat ring callousness, 1.0 - 4.0) ve vakum sağlığı analizi
- Sağım sonrası robotik hedefe yönelik dezenfektan püskürtme (Post-dip spraying) ve başlık buhar sterilizasyonu
"""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
import random
from pydantic import BaseModel, Field

class QuarterTelemetry(BaseModel):
    quarter_id: Literal["RF", "RR", "LF", "LR"]
    quarter_name_tr: str
    yield_kg: float = Field(..., description="Lob süt verimi (kg)")
    conductivity_ms_cm: float = Field(..., description="Elektriksel iletkenlik (Normal: 4.8 - 5.5 mS/cm)")
    somatic_cell_count: int = Field(..., description="Spektroskopik Somatik Hücre Sayısı (SCC, hücre/mL)")
    blood_in_milk_ppm: float = Field(..., description="Sütte kan varlığı (Normal: < 10 ppm)")
    peak_flow_rate_kg_min: float = Field(..., description="Maksimum süt akış hızı (kg/dk)")
    hyperkeratosis_score: float = Field(..., description="Meme ucu hiperkeratoz skoru (1.0 - 4.0)")
    mastitis_status: Literal["HEALTHY", "SUBCLINICAL", "CLINICAL"]
    valve_destination: Literal["MAIN_TANK", "SEPARATION_DRAIN"] = "MAIN_TANK"
    diagnostic_note: str

class RoboticMilkingTwinProfile(BaseModel):
    robot_id: str = "ROBOT-VMS-01"
    capture_timestamp: datetime
    animal_id: str
    total_yield_kg: float
    accepted_to_tank_kg: float
    diverted_waste_kg: float
    quarters: Dict[str, QuarterTelemetry]
    weighted_scc: int
    is_any_quarter_diverted: bool = False
    teat_cup_disinfection: str = "Otomatik Buhar + Perasetik Asit Sterilizasyonu"
    post_dip_formula: str = "Bariyer İyotlu Polimer Sprey"
    robot_recommendation: str

class RoboticMilkingEngine:
    """
    4 Loblu Meme Seviyesi Robotik Sağım & Spektroskopi Simülasyon Motoru
    """

    QUARTER_METADATA = {
        "RF": {"name": "Sağ Ön (Right Front)", "yield_share": 0.22},
        "RR": {"name": "Sağ Arka (Right Rear)", "yield_share": 0.28},
        "LF": {"name": "Sol Ön (Left Front)", "yield_share": 0.21},
        "LR": {"name": "Sol Arka (Left Rear)", "yield_share": 0.29},
    }

    @classmethod
    def simulate_quarter_milking(
        cls,
        animal_id: str,
        total_session_yield_kg: float,
        is_mastitis_induced: bool = False,
        infected_quarter: str = "LR",  # Varsayılan enfekte lob: Sol Arka
        severity: float = 1.0
    ) -> RoboticMilkingTwinProfile:
        now = datetime.now()
        quarters_data: Dict[str, QuarterTelemetry] = {}
        total_accepted = 0.0
        total_diverted = 0.0
        weighted_scc_sum = 0.0

        for q_id, meta in cls.QUARTER_METADATA.items():
            base_yield = round(total_session_yield_kg * meta["yield_share"] + random.uniform(-0.15, 0.15), 2)
            base_yield = max(0.5, base_yield)

            is_infected = (is_mastitis_induced and q_id == infected_quarter)

            if is_infected:
                # Enfekte çeyrek (Örn: Sol Arka mastitis)
                yield_drop = 0.65 - (severity - 1.0) * 0.15
                q_yield = round(base_yield * yield_drop, 2)
                # İletkenlik belirgin yükselir (Na+ ve Cl- sızıntısı)
                conductivity = round(6.75 + (severity - 1.0) * 0.85 + random.uniform(-0.1, 0.15), 2)
                # Somatik hücre sayısı fırlar (Örn: 580.000 - 1.200.000 hücre/mL)
                scc = int(620000 * severity + random.randint(-40000, 60000))
                blood = round(35.0 * severity + random.uniform(-5.0, 10.0), 1)
                flow = round(1.2 - (severity - 1.0) * 0.3, 2)
                hk_score = round(2.8 + (severity - 1.0) * 0.4, 1)

                status = "CLINICAL" if scc > 500000 else "SUBCLINICAL"
                destination = "SEPARATION_DRAIN"
                total_diverted += q_yield

                note = (
                    f"🚨 {meta['name']} lobunda mastitis tespit edildi! İletkenlik: {conductivity} mS/cm, "
                    f"SCC: {scc:,} hücre/mL. Robot vanası devreye girerek bu lobun sütünü atık tankına yönlendirdi."
                )
            else:
                # Sağlıklı çeyrek
                q_yield = base_yield
                conductivity = round(5.05 + random.uniform(-0.15, 0.15), 2)
                scc = random.randint(45000, 130000)
                blood = round(random.uniform(1.0, 6.0), 1)
                flow = round(2.4 + random.uniform(-0.2, 0.3), 2)
                hk_score = round(1.2 + random.uniform(0.0, 0.3), 1)

                status = "HEALTHY"
                destination = "MAIN_TANK"
                total_accepted += q_yield
                note = f"✅ {meta['name']} sağlıklı. Hücre sayısı {scc:,} hücre/mL, süt ana tanka akıyor."

            weighted_scc_sum += scc * q_yield

            quarters_data[q_id] = QuarterTelemetry(
                quarter_id=q_id,
                quarter_name_tr=meta["name"],
                yield_kg=q_yield,
                conductivity_ms_cm=conductivity,
                somatic_cell_count=scc,
                blood_in_milk_ppm=blood,
                peak_flow_rate_kg_min=flow,
                hyperkeratosis_score=hk_score,
                mastitis_status=status,
                valve_destination=destination,
                diagnostic_note=note
            )

        calc_total_yield = round(total_accepted + total_diverted, 2)
        overall_scc = int(weighted_scc_sum / max(0.1, calc_total_yield))
        any_diverted = total_diverted > 0

        if any_diverted:
            rec = (
                f"Robotik Ayrım Aktif: Enfekte {infected_quarter} lobundan {total_diverted:.2f} kg süt atığa ayrıldı. "
                f"Sağlıklı 3 lobdan toplanan {total_accepted:.2f} kg süt başarıyla ana tanka kabul edildi (Süt kaybı %{int((total_diverted/calc_total_yield)*100)} ile sınırlandı)."
            )
            dip = "Hedefe Yönelik Klorheksidin + Laktik Asit Bariyer Dezenfektanı"
        else:
            rec = "Tüm 4 meme lobu sağlıklı. 4 lobun sütü de doğrudan birinci sınıf ana süt tankına yönlendirildi."
            dip = "Standart İyotlu Bariyer Polimer Sprey"

        return RoboticMilkingTwinProfile(
            robot_id=f"VMS-ROBOT-01",
            capture_timestamp=now,
            animal_id=animal_id,
            total_yield_kg=calc_total_yield,
            accepted_to_tank_kg=round(total_accepted, 2),
            diverted_waste_kg=round(total_diverted, 2),
            quarters=quarters_data,
            weighted_scc=overall_scc,
            is_any_quarter_diverted=any_diverted,
            teat_cup_disinfection="Otomatik Başlık İçi Buhar Sterilizasyonu (95°C, 12 sn)",
            post_dip_formula=dip,
            robot_recommendation=rec
        )
