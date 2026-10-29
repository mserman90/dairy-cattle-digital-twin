"""
AgriTwin: Döngüsel Çiftlik Atık, Biyogaz Kojenerasyon & Yenilenebilir Enerji İkizi
(Circular Manure Anaerobic Digester, Biogas CHP & Net-Zero Farm Energy Twin)

Özellikler:
- Sürü bazında günlük dışkı ve idrar (gübre) üretimi (kg/gün)
- Mezofilik Anaerobik Çürütücü (Anaerobic Digester, 38°C, HRT: 28 gün)
- Biyogaz üretimi (m³ CH4/gün, %62 Metan saflığı)
- Kojenerasyon (CHP - Combined Heat and Power) Elektrik ve Isı Üretimi (kWh/gün)
- Çiftlik operasyonel elektrik tüketimi (Sağım robotu, soğutma tankı, fanlar, aydınlatma)
- Net-Zero Şebeke Bağımsızlığı: Fazla elektriğin şebekeye satışı (YEKDEM / Feed-in Tariff)
- Biyogübre (Digestat) ile kimyasal N-P-K gübre ikamesi ve amonyak emisyon kontrolü
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ManureExcretionData(BaseModel):
    total_manure_kg_day: float = Field(..., description="Sürü toplam günlük ham gübre miktarı (kg/gün)")
    total_solids_pct: float = Field(13.2, description="Toplam Katı Madde Oranı (TS %)")
    volatile_solids_kg_day: float = Field(..., description="Uçucu Katı Madde Miktarı (VS, kg/gün)")
    nitrogen_content_kg: float = Field(..., description="Gübredeki toplam organik azot (N, kg/gün)")
    phosphorus_content_kg: float = Field(..., description="Fosfor içeriği (P2O5, kg/gün)")
    potassium_content_kg: float = Field(..., description="Potasyum içeriği (K2O, kg/gün)")

class AnaerobicDigesterState(BaseModel):
    digester_id: str = "AD-DIGESTER-01"
    digester_type: str = "Mezofilik Sürekli Karışımlı Tank Reaktör (CSTR)"
    operating_temp_c: float = 38.5
    hydraulic_retention_time_days: int = 28
    daily_biogas_production_m3: float = Field(..., description="Günlük üretilen ham biyogaz hacmi (m³/gün)")
    methane_content_pct: float = Field(62.5, description="Metan oranı (% CH4)")
    daily_pure_methane_m3: float = Field(..., description="Günlük saf metan hacmi (m³ CH4/gün)")
    biogas_lower_heating_value_kwh_m3: float = Field(6.25, description="Biyogaz alt ısıl değeri (kWh/m³)")

class FarmPowerConsumption(BaseModel):
    milking_robot_kwh: float = Field(..., description="Sağım robotu günlük tüketimi (kWh)")
    milk_cooling_tank_kwh: float = Field(..., description="Süt soğutma tankı kompresörü (kWh)")
    ventilation_fans_misting_kwh: float = Field(..., description="Barınak fanları ve sisleme pompası (kWh)")
    manure_scraper_lighting_kwh: float = Field(..., description="Otomatik gübre sıyırıcı ve LED aydınlatma (kWh)")
    water_pumps_office_kwh: float = Field(..., description="Su pompaları ve idari bina (kWh)")
    total_consumption_kwh_day: float = Field(..., description="Çiftlik toplam günlük elektrik ihtiyacı (kWh/gün)")

class CHPCogenerationOutput(BaseModel):
    chp_unit_id: str = "CHP-JEN-60kW"
    electrical_efficiency_pct: float = Field(38.0, description="CHP Elektriksel Verim (%)")
    thermal_efficiency_pct: float = Field(48.0, description="CHP Isıl Verim (%)")
    daily_electricity_generated_kwh: float = Field(..., description="Günlük üretilen elektrik (kWh/gün)")
    daily_heat_generated_kwh: float = Field(..., description="Günlük üretilen termal ısı (kWh/gün - sıcak su & çürütücü ısıtma)")
    net_grid_export_kwh: float = Field(..., description="Şebekeye satılan net fazla elektrik (kWh/gün)")
    self_sufficiency_ratio_pct: float = Field(..., description="Enerji Öz Yeterlilik Oranı (%)")
    is_net_zero_energy: bool = Field(True, description="Çiftlik Net-Zero / Enerji Pozitif mi?")

class DigestateBiofertilizer(BaseModel):
    daily_digestate_tons: float = Field(..., description="Günlük fermente biyogübre çıktısı (ton/gün)")
    annual_chemical_fertilizer_saving_tl: float = Field(..., description="Yıllık kimyasal gübre ikamesi tasarrufu (TL)")
    mineralized_nitrogen_pct: float = Field(65.0, description="Hemen alınabilir amonyum azotu oranı (%)")

class FarmEnergyTwinProfile(BaseModel):
    timestamp: datetime
    herd_size: int
    manure: ManureExcretionData
    digester: AnaerobicDigesterState
    consumption: FarmPowerConsumption
    chp: CHPCogenerationOutput
    fertilizer: DigestateBiofertilizer
    daily_electricity_savings_tl: float
    daily_grid_revenue_tl: float
    annual_total_energy_benefit_tl: float
    annual_co2_offset_tons: float
    status_summary: str

class CircularBiogasEnergyEngine:
    """
    Süt Çiftliği Döngüsel Atık, Biyogaz ve Kojenerasyon Simülasyon Motoru
    """

    @classmethod
    def simulate_farm_energy(
        cls,
        herd_size: int = 80,
        active_fans_count: int = 6,
        is_heat_wave: bool = False,
        electricity_tariff_tl_kwh: float = 3.85,
        feed_in_tariff_tl_kwh: float = 4.20
    ) -> FarmEnergyTwinProfile:
        now = datetime.now()

        # 1. Gübre Üretimi (inek başına ortalama 54 kg/gün ham dışkı + idrar)
        # 80 baş için ~4.320 kg/gün gübre
        manure_per_cow_kg = 54.0
        total_manure_kg = herd_size * manure_per_cow_kg
        ts_pct = 13.2  # %13.2 Katı Madde
        total_solids_kg = total_manure_kg * (ts_pct / 100.0)
        # Katı maddenin %82'si Uçucu Katı Madde (Volatile Solids - VS)
        vs_kg = total_solids_kg * 0.82

        # Organik Azot (N: ~5.2 g/kg), Fosfor (P2O5: ~2.1 g/kg), Potasyum (K2O: ~4.5 g/kg)
        n_kg = round(total_manure_kg * 0.0052, 1)
        p_kg = round(total_manure_kg * 0.0021, 1)
        k_kg = round(total_manure_kg * 0.0045, 1)

        manure_data = ManureExcretionData(
            total_manure_kg_day=round(total_manure_kg, 1),
            total_solids_pct=ts_pct,
            volatile_solids_kg_day=round(vs_kg, 1),
            nitrogen_content_kg=n_kg,
            phosphorus_content_kg=p_kg,
            potassium_content_kg=k_kg
        )

        # 2. Anaerobik Çürütücü Biyogaz Üretimi
        # Biyokimyasal Metan Potansiyeli (BMP): 0.28 m³ CH4 / kg VS
        pure_methane_m3 = round(vs_kg * 0.285, 1)  # ~133 m³ saf CH4
        methane_pct = 62.5
        total_biogas_m3 = round(pure_methane_m3 / (methane_pct / 100.0), 1)  # ~213 m³ ham biyogaz

        digester_state = AnaerobicDigesterState(
            operating_temp_c=38.5,
            hydraulic_retention_time_days=28,
            daily_biogas_production_m3=total_biogas_m3,
            methane_content_pct=methane_pct,
            daily_pure_methane_m3=pure_methane_m3
        )

        # 3. Çiftlik Tüketimi (kWh/gün)
        milking_kwh = 24.5  # Robotik sağım ünitesi ve vakum pompaları
        cooling_kwh = 38.0  # Süt tankı dondurucu ve soğutma kompresörü
        fan_kwh = 52.0 if is_heat_wave else (active_fans_count * 3.5)
        scraper_lighting_kwh = 16.5
        pumps_office_kwh = 14.0
        total_consump = round(milking_kwh + cooling_kwh + fan_kwh + scraper_lighting_kwh + pumps_office_kwh, 1)

        consumption_data = FarmPowerConsumption(
            milking_robot_kwh=milking_kwh,
            milk_cooling_tank_kwh=cooling_kwh,
            ventilation_fans_misting_kwh=round(fan_kwh, 1),
            manure_scraper_lighting_kwh=scraper_lighting_kwh,
            water_pumps_office_kwh=pumps_office_kwh,
            total_consumption_kwh_day=total_consump
        )

        # 4. Kojenerasyon (CHP) Üretimi
        # Toplam primer biyogaz enerjisi: total_biogas_m3 * 6.25 kWh/m³
        primary_energy_kwh = total_biogas_m3 * 6.25  # ~1.330 kWh termal enerji
        elec_eff = 0.38  # %38 elektrik verimi
        therm_eff = 0.48  # %48 ısı verimi

        elec_generated_kwh = round(primary_energy_kwh * elec_eff, 1)  # ~506 kWh/gün elektrik
        heat_generated_kwh = round(primary_energy_kwh * therm_eff, 1)  # ~639 kWh/gün ısı

        net_export_kwh = round(max(0.0, elec_generated_kwh - total_consump), 1)
        self_suff_pct = round((elec_generated_kwh / total_consump) * 100.0, 1)

        chp_data = CHPCogenerationOutput(
            electrical_efficiency_pct=38.0,
            thermal_efficiency_pct=48.0,
            daily_electricity_generated_kwh=elec_generated_kwh,
            daily_heat_generated_kwh=heat_generated_kwh,
            net_grid_export_kwh=net_export_kwh,
            self_sufficiency_ratio_pct=self_suff_pct,
            is_net_zero_energy=(elec_generated_kwh >= total_consump)
        )

        # 5. Digestat Biyogübre
        daily_digestate = round(total_manure_kg * 0.94 / 1000.0, 2)  # ~4.06 ton/gün sıvı biyogübre
        # 1 ton digestat kimyasal gübre karşılığı tasarrufu: ~320 TL
        annual_fertilizer_saving = round(daily_digestate * 365.0 * 320.0, 2)  # ~474.000 TL/yıl

        fertilizer_data = DigestateBiofertilizer(
            daily_digestate_tons=daily_digestate,
            annual_chemical_fertilizer_saving_tl=annual_fertilizer_saving,
            mineralized_nitrogen_pct=65.0
        )

        # 6. Finansal Faydalar & CO2 Emisyon Dengelemesi
        # Çiftlik kendi tükettiği elektriği şebekeden çekmeyerek tasarruf eder:
        daily_savings = round(min(elec_generated_kwh, total_consump) * electricity_tariff_tl_kwh, 2)
        # Fazla elektriği YEKDEM tarifesiyle şebekeye satar:
        daily_export_rev = round(net_export_kwh * feed_in_tariff_tl_kwh, 2)

        annual_energy_benefit = round((daily_savings + daily_export_rev) * 365.0 + annual_fertilizer_saving, 2)
        # 1 kWh yenilenebilir elektrik ~0.48 kg CO2e fosil şebeke emisyonunu engeller:
        annual_co2_offset = round((elec_generated_kwh * 365.0 * 0.48) / 1000.0, 1)

        summary = (
            f"⚡ Çiftlik Net-Zero Enerji Fazlası Üretiyor! Günlük {elec_generated_kwh:.1f} kWh elektrik üretildi. "
            f"Çiftlik ihtiyacı ({total_consump:.1f} kWh) karşılandıktan sonra şebekeye {net_export_kwh:.1f} kWh temiz elektrik ihraç edildi "
            f"(Öz yeterlilik: %{self_suff_pct:.0f}). Biyogübre ve elektrikle yıllık +{annual_energy_benefit:,.0f} TL döngüsel katma değer yaratıldı."
        )

        return FarmEnergyTwinProfile(
            timestamp=now,
            herd_size=herd_size,
            manure=manure_data,
            digester=digester_state,
            consumption=consumption_data,
            chp=chp_data,
            fertilizer=fertilizer_data,
            daily_electricity_savings_tl=daily_savings,
            daily_grid_revenue_tl=daily_export_rev,
            annual_total_energy_benefit_tl=annual_energy_benefit,
            annual_co2_offset_tons=annual_co2_offset,
            status_summary=summary
        )
