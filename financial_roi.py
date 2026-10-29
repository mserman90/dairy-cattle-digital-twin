from typing import Dict, Any
from pydantic import BaseModel, Field

class FinancialParameters(BaseModel):
    milk_price_per_kg: float = Field(16.5, description="Çiğ süt satış fiyatı (TL/kg)")
    roughage_cost_per_kg_dm: float = Field(5.2, description="Kaba yem kuru madde maliyeti (TL/kg)")
    concentrate_cost_per_kg_dm: float = Field(11.8, description="Kesif yem kuru madde maliyeti (TL/kg)")
    clinical_mastitis_cost_per_case: float = Field(4200.0, description="Klinik mastitis vaka maliyeti (İlaç + Dökülen Süt + Vet, TL)")
    missed_estrus_cost_per_cycle: float = Field(4800.0, description="Kaçırılan kızgınlık döngüsü maliyeti (21 gün açık kalma, TL)")
    system_initial_capex: float = Field(240000.0, description="80 başlık dijital ikiz donanım/sensör/yazılım yatırım maliyeti (TL)")
    monthly_opex_per_cow: float = Field(45.0, description="Hayvan başı aylık yazılım/bulut/bakım maliyeti (TL)")

class FinancialTwinOutput(BaseModel):
    daily_gross_milk_revenue: float
    daily_total_feed_cost: float
    daily_net_margin_over_feed: float
    monthly_feed_savings_from_optimization: float
    prevented_disease_losses_monthly: float
    prevented_estrus_losses_monthly: float
    total_monthly_net_benefit: float
    estimated_payback_period_years: float
    roi_percentage_year_1: float

class FarmFinancialEngine:
    """
    Süt Çiftliği Dijital İkizi Finansal & ROI Simülasyon Motoru
    """

    @staticmethod
    def calculate_economics(
        herd_size: int,
        daily_total_milk_kg: float,
        daily_total_dmi_kg: float,
        roughage_pct: float,
        concentrate_pct: float,
        is_ration_optimized: bool,
        subclinical_cases_caught_early: int,
        estrus_detected_timely: int,
        params: FinancialParameters = FinancialParameters()
    ) -> FinancialTwinOutput:
        # 1. Günlük Gelir ve Yem Gideri
        daily_revenue = daily_total_milk_kg * params.milk_price_per_kg

        # Ağırlıklı yem birim maliyeti (TL / kg DMI)
        feed_unit_cost = (
            (roughage_pct / 100.0) * params.roughage_cost_per_kg_dm +
            (concentrate_pct / 100.0) * params.concentrate_cost_per_kg_dm
        )
        daily_feed_cost = daily_total_dmi_kg * feed_unit_cost
        daily_margin = daily_revenue - daily_feed_cost

        # 2. Rasyon Optimizasyon Tasarrufu (Yemden Yararlanma İyileşmesi)
        # 80 başlık çiftlik ölçeğine projeksiyon katsayısı
        scale_factor = 80.0 / max(1, herd_size)
        projected_monthly_feed_savings = (
            (daily_feed_cost * 0.14 * 30.0 * scale_factor) if is_ration_optimized
            else (daily_feed_cost * 0.04 * 30.0 * scale_factor)
        )

        # 3. Erken Teşhis ile Önlenen Hastalık Maliyeti (Mastitis)
        # Her erken teşhis edilen subklinik vaka, klinik tedavi ve dökülen süt maliyetinin %70'ini kurtarır
        disease_savings_monthly = (subclinical_cases_caught_early * params.clinical_mastitis_cost_per_case * 0.70) * (scale_factor / 3.0)

        # 4. Zamanında Tohumlama ile Önlenen Boş Gün Maliyeti
        estrus_savings_monthly = (estrus_detected_timely * params.missed_estrus_cost_per_cycle) * (scale_factor / 4.0)

        # 5. Toplam Aylık Net Fayda
        monthly_opex = params.monthly_opex_per_cow * 80.0
        total_monthly_benefit = (
            projected_monthly_feed_savings +
            disease_savings_monthly +
            estrus_savings_monthly -
            monthly_opex
        )

        # 6. Yatırımın Geri Dönüşü (ROI & Payback Period)
        annual_benefit = max(1000.0, total_monthly_benefit * 12.0)
        payback_years = round(params.system_initial_capex / annual_benefit, 2)
        roi_year_1 = round(((annual_benefit - params.system_initial_capex) / params.system_initial_capex) * 100.0, 1)

        return FinancialTwinOutput(
            daily_gross_milk_revenue=round(daily_revenue, 2),
            daily_total_feed_cost=round(daily_feed_cost, 2),
            daily_net_margin_over_feed=round(daily_margin, 2),
            monthly_feed_savings_from_optimization=round(projected_monthly_feed_savings, 2),
            prevented_disease_losses_monthly=round(disease_savings_monthly, 2),
            prevented_estrus_losses_monthly=round(estrus_savings_monthly, 2),
            total_monthly_net_benefit=round(total_monthly_benefit, 2),
            estimated_payback_period_years=payback_years,
            roi_percentage_year_1=roi_year_1
        )
