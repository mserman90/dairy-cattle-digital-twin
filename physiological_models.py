import math
from typing import Dict, List, Tuple
from pydantic import BaseModel, Field

class WoodCurveParams(BaseModel):
    a: float = Field(..., description="Başlangıç süt verim ölçeği")
    b: float = Field(..., description="Zirveye (peak) tırmanış eğimi")
    c: float = Field(..., description="Zirve sonrası persistance azalma katsayısı")

class WoodCurvePoint(BaseModel):
    dim: int
    expected_yield: float

class PhysiologicalProfile(BaseModel):
    wood_params: WoodCurveParams
    peak_dim: int = Field(..., description="Zirve süt verimi günü")
    peak_yield: float = Field(..., description="Zirve süt verimi (kg/gün)")
    body_weight_kg: float = 620.0
    body_condition_score: float = Field(3.25, description="Vücut Kondisyon Skoru (BCS, 1-5)")
    dry_matter_intake_kg: float = Field(22.5, description="Günlük Kuru Madde Tüketimi (DMI, kg)")
    net_energy_balance_mcal: float = Field(0.0, description="Net Enerji Dengesi (EB, Mcal/gün)")
    enteric_methane_g_day: float = Field(380.0, description="Enterik Metan Salımı (g CH4 / gün)")
    methane_intensity_g_per_kg_milk: float = Field(12.5, description="Metan Yoğunluğu (g CH4 / kg süt)")
    carbon_equivalent_kg_co2e: float = Field(10.6, description="CO2 Eşdeğeri (kg CO2e / gün)")

class RationComposition(BaseModel):
    roughage_pct: float = Field(55.0, description="Kaba Yem Oranı (%) - Mısır Silajı / Yonca")
    concentrate_pct: float = Field(45.0, description="Kesif Yem Oranı (%) - Tahıl / Protein Karma")
    fat_supplement_pct: float = Field(1.5, description="Yem Katkısı / Korunmuş Yağ (%)")
    crude_protein_pct: float = Field(16.5, description="Ham Protein (%)")
    neutral_detergent_fiber_pct: float = Field(32.0, description="NDF (%)")

class PhysiologicalEngine:
    """
    inSiliCow & RuFaS matematiksel model referansları ile geliştirilmiş
    fizyolojik simülasyon ve laktasyon motoru.
    """

    @staticmethod
    def calculate_wood_yield(params: WoodCurveParams, dim: int) -> float:
        """
        Wood's Incomplete Gamma Curve:
        y(t) = a * (t^b) * e^(-c * t)
        """
        if dim <= 0:
            return params.a
        t = float(dim)
        val = params.a * (t ** params.b) * math.exp(-params.c * t)
        return round(max(5.0, val), 2)

    @staticmethod
    def get_wood_curve_points(params: WoodCurveParams, max_dim: int = 305, step: int = 15) -> List[WoodCurvePoint]:
        """0'dan 305. güne kadar standart laktasyon eğrisi noktalarını üretir"""
        points = []
        for dim in range(10, max_dim + 1, step):
            points.append(WoodCurvePoint(
                dim=dim,
                expected_yield=PhysiologicalEngine.calculate_wood_yield(params, dim)
            ))
        return points

    @staticmethod
    def get_peak_stats(params: WoodCurveParams) -> Tuple[int, float]:
        """Wood modelinde t_peak = b / c, y_peak = a * (b/c)^b * e^(-b)"""
        if params.c <= 0:
            return (60, 35.0)
        t_peak = int(round(params.b / params.c))
        y_peak = PhysiologicalEngine.calculate_wood_yield(params, t_peak)
        return (t_peak, y_peak)

    @staticmethod
    def evaluate_energy_and_emissions(
        body_weight_kg: float,
        actual_yield_kg: float,
        milk_fat_pct: float,
        dim: int,
        ration: RationComposition
    ) -> Dict[str, float]:
        """
        RuFaS / NRC Ruminant & IPCC Tier 2 Enterik Metan Modeli
        """
        # 1. Kuru Madde Tüketimi (DMI - Dry Matter Intake, NRC Formülü)
        # DMI = (0.0185 * BW + 0.305 * FCM) * (1 - e^(-0.192 * (dim/7 + 3.67)))
        fcm_4pct = 0.4 * actual_yield_kg + 15.0 * (milk_fat_pct / 100.0) * actual_yield_kg
        fcm = max(10.0, fcm_4pct)
        week_of_lactation = max(1.0, dim / 7.0)
        lag_factor = 1.0 - math.exp(-0.192 * (week_of_lactation + 3.67))
        dmi_kg = round((0.0185 * body_weight_kg + 0.305 * fcm) * lag_factor, 2)

        # 2. Enerji İhtiyacı ve Dengesi (Net Energy for Lactation - NE_L Mcal/gün)
        # Yaşama payı enerjisi (Maintenance): 0.08 * BW^0.75
        ne_maintenance = 0.08 * (body_weight_kg ** 0.75)
        # Süt üretimi enerjisi: FCM * 0.70 Mcal/kg
        ne_milk = fcm * 0.70
        ne_required = ne_maintenance + ne_milk

        # Rasyonun enerji yoğunluğu (Mcal NE_L / kg DMI)
        # Kesif yem arttıkça enerji yoğunluğu artar (1.55 - 1.78 Mcal/kg)
        ne_diet_density = 1.45 + (ration.concentrate_pct / 100.0) * 0.30 + (ration.fat_supplement_pct / 100.0) * 0.15
        ne_intake = dmi_kg * ne_diet_density
        energy_balance = round(ne_intake - ne_required, 2)

        # 3. IPCC Tier 2 Enterik Metan (CH4) Emisyonu
        # Brüt Enerji Tüketimi (GE, MJ/gün): DMI * 18.45 MJ/kg
        ge_mj = dmi_kg * 18.45
        
        # Methane Conversion Factor (Ym %): Standart kaba yem ağırlıklı rasyonda ~6.5%
        # Kesif yem ve yağ katkısı Ym'yi düşürür (örneğin %5.2 - %6.5 aralığı)
        ym_base = 0.065
        ym_reduction = (ration.concentrate_pct - 40.0) * 0.0003 + (ration.fat_supplement_pct * 0.003)
        ym = max(0.048, min(0.070, ym_base - ym_reduction))

        # Metan Enerjisi = GE * Ym (MJ CH4)
        ch4_mj = ge_mj * ym
        # Metanın yanma ısısı: 55.65 MJ/kg CH4 -> 1 kg = 1000 g
        ch4_g_day = round((ch4_mj / 55.65) * 1000.0, 1)

        # Metan Yoğunluğu (g CH4 / kg Süt)
        methane_intensity = round(ch4_g_day / max(1.0, actual_yield_kg), 2)

        # Karbon Ayak İzi (IPCC AR5 GWP100: 1 kg CH4 = 28 kg CO2e)
        co2_equivalent_kg = round((ch4_g_day / 1000.0) * 28.0, 2)

        return {
            "dmi_kg": dmi_kg,
            "ne_intake_mcal": round(ne_intake, 2),
            "ne_required_mcal": round(ne_required, 2),
            "energy_balance_mcal": energy_balance,
            "methane_g_day": ch4_g_day,
            "methane_intensity": methane_intensity,
            "co2_equivalent_kg": co2_equivalent_kg,
            "fcm_kg": round(fcm, 2)
        }
