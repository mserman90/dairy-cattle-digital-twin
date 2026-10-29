from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import math
import random
from pydantic import BaseModel, Field

class RumenpHPoint(BaseModel):
    hour: int = Field(..., description="Günün saati (0-23)")
    rumen_ph: float = Field(..., description="Rumen sıvısı pH değeri")
    is_below_threshold: bool = False

class RumenBolusTelemetry(BaseModel):
    device_id: str = "BOLUS-RETICULO-01"
    capture_timestamp: datetime
    rumen_ph: float = Field(..., description="Anlık Rumen pH (Sağlıklı: 6.2 - 6.8)")
    rumen_temperature_c: float = Field(..., description="Rumen Sıcaklığı (°C, 38.8 - 40.2)")
    total_vfa_mmol_l: float = Field(..., description="Toplam Uçucu Yağ Asitleri (80 - 140 mmol/L)")
    acetate_to_propionate_ratio: float = Field(..., description="Asetat/Propiyonat Oranı (A:P, İdeal: > 2.5)")
    lactic_acid_mmol_l: float = Field(..., description="Laktik Asit Seviyesi (Normal: < 2.0 mmol/L)")
    rumen_contractions_per_min: float = Field(..., description="Rumen Motilite Kontraksiyon Sayısı (1.5 - 2.5 /dk)")
    drinking_bouts_today: int = Field(..., description="Bugünkü Su İçme Seansı Sayısı")

class SARAAssessment(BaseModel):
    sara_risk_score: float = Field(..., description="SARA Asidoz Riski (0.0 - 1.0)")
    hours_below_ph_5_8: float = Field(..., description="pH < 5.8 kritik eşik altında kalınan süre (saat/gün)")
    acidosis_stage: str = Field(..., description="NORMAL, MILD_RISK, SARA_ACIDOSIS, ACUTE_ACIDOSIS")
    rumen_motility_status: str = Field(..., description="NORMAL, HYPOMOTILE, ATONY")
    buffer_supplement_needed: bool = Field(False, description="Sodyum Bikarbonat / Tampon Yem Takviyesi İhtiyacı")
    clinical_interpretation: str

class RumenTwinProfile(BaseModel):
    telemetry: RumenBolusTelemetry
    assessment: SARAAssessment
    hourly_ph_curve: List[RumenpHPoint] = []

class RumenBiochemicalEngine:
    """
    inSiliCow & Dijkstra Rumen Fermantasyonu ve pH Kinetiği Simülasyon Motoru
    (Subacute Ruminal Acidosis - SARA İzleme)
    """

    @staticmethod
    def simulate_rumen_state(
        animal_id: str,
        concentrate_pct: float = 42.0,
        rumination_minutes_2h: int = 26,
        is_acidosis_induced: bool = False,
        severity: float = 1.0
    ) -> RumenTwinProfile:
        now = datetime.now()

        # 1. Fermantasyon ve Tamponlama Kinetiği
        # Geviş getirme tükürük tamponu (HCO3-) üretir. Geviş azaldıkça tamponlama düşer.
        saliva_buffer_factor = min(1.2, max(0.4, rumination_minutes_2h / 26.0))
        # Kesif yem / nişasta oranı asit üretimini hızlandırır.
        starch_acid_load = (concentrate_pct / 100.0) * 1.8

        if is_acidosis_induced:
            # SARA / Asidoz Hali
            base_ph = max(5.1, round(5.55 - (severity - 1.0) * 0.25 + random.uniform(-0.08, 0.08), 2))
            hours_low = round(3.8 + (severity - 1.0) * 2.1, 1)
            vfa = round(145.0 + (severity - 1.0) * 20.0, 1)
            ap_ratio = round(1.65 - (severity - 1.0) * 0.25, 2)
            lactic = round(4.5 + (severity - 1.0) * 3.0, 1)
            motility = round(0.8 - (severity - 1.0) * 0.2, 1)  # hipomotilite
            temp = round(39.9 + random.uniform(0.0, 0.4), 1)

            risk_score = min(0.99, round(0.70 + (severity - 1.0) * 0.18, 2))
            stage = "ACUTE_ACIDOSIS" if base_ph < 5.3 else "SARA_ACIDOSIS"
            motility_st = "ATONY" if motility < 0.6 else "HYPOMOTILE"
            buffer_need = True
            interp = (
                f"Subakut Rumen Asidozu (SARA) Tespiti! Rumen pH'ı günün {hours_low} saati 5.8 eşiğinin altında kaldı. "
                f"A:P oranı ({ap_ratio}) lif fermantasyonunun çöktüğünü gösteriyor. Rasyona 150g Sodyum Bikarbonat takviyesi önerilir."
            )
        else:
            # Sağlıklı Rumen Dinamiği
            base_ph = round(6.45 - (starch_acid_load * 0.15) + (saliva_buffer_factor * 0.12) + random.uniform(-0.06, 0.06), 2)
            base_ph = min(6.85, max(6.15, base_ph))
            hours_low = 0.4 if base_ph < 6.2 else 0.0
            vfa = round(110.0 + random.uniform(-8.0, 8.0), 1)
            ap_ratio = round(2.85 + random.uniform(-0.15, 0.15), 2)
            lactic = round(0.8 + random.uniform(-0.2, 0.3), 1)
            motility = round(1.9 + random.uniform(-0.2, 0.2), 1)
            temp = round(39.2 + random.uniform(-0.2, 0.2), 1)

            risk_score = 0.08
            stage = "NORMAL"
            motility_st = "NORMAL"
            buffer_need = False
            interp = f"Rumen fermantasyonu sağlıklı (pH {base_ph:.2f}). A:P oranı ({ap_ratio}) lif parçalayıcı bakteriler için idealdir."

        # 24 Saatlik Rumen pH Eğrisi Simülasyonu
        curve: List[RumenpHPoint] = []
        for h in range(24):
            # Sabah ve akşam yemleme saatlerinde (08:00 ve 18:00) pH geçici olarak dibe vurur
            dip = 0.35 * math.exp(-((h - 9) ** 2) / 8.0) + 0.40 * math.exp(-((h - 19) ** 2) / 8.0)
            h_ph = round(base_ph - dip + 0.18 + random.uniform(-0.04, 0.04), 2)
            if is_acidosis_induced:
                h_ph = min(5.95, h_ph)

            curve.append(RumenpHPoint(
                hour=h,
                rumen_ph=h_ph,
                is_below_threshold=(h_ph < 5.8)
            ))

        telemetry = RumenBolusTelemetry(
            device_id=f"BOLUS-{animal_id.replace('TR-34-', '')}",
            capture_timestamp=now,
            rumen_ph=base_ph,
            rumen_temperature_c=temp,
            total_vfa_mmol_l=vfa,
            acetate_to_propionate_ratio=ap_ratio,
            lactic_acid_mmol_l=lactic,
            rumen_contractions_per_min=motility,
            drinking_bouts_today=random.randint(6, 12)
        )

        assessment = SARAAssessment(
            sara_risk_score=risk_score,
            hours_below_ph_5_8=hours_low,
            acidosis_stage=stage,
            rumen_motility_status=motility_st,
            buffer_supplement_needed=buffer_need,
            clinical_interpretation=interp
        )

        return RumenTwinProfile(
            telemetry=telemetry,
            assessment=assessment,
            hourly_ph_curve=curve
        )

# Global Rumen Engine
rumen_engine = RumenBiochemicalEngine()
