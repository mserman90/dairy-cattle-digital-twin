"""
AgriTwin: Süt Sığırcılığı Çok Amaçlı Rasyon & Karbon-Verim Optimizasyon İkizi
(Multi-Objective TMR Feed Ration & Enteric Methane Pareto Optimizer)

Referans Modeller:
- RuFaS (Ruminant Farm Systems) Feed Intake & Nutritional Balance
- IPCC Tier 2 Enterik Metan Kinetiği (Ym katsayısı ve metan mitigasyonu)
- NRC (Nutrient Requirements of Dairy Cattle) Ham Protein, NDF ve NE_L Dengesi
- SARA Koruma Kısıtları (Minimum %28 NDF, Maksimum %28 Nişasta)
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

class FeedIngredient(BaseModel):
    id: str
    name: str
    category: Literal["ROUGHAGE", "CONCENTRATE", "PROTEIN", "ADDITIVE"]
    cost_per_kg_dm: float = Field(..., description="Kuru Madde Birim Maliyeti (TL/kg DM)")
    dm_pct: float = Field(..., description="Kuru Madde Oranı (%)")
    crude_protein_pct: float = Field(..., description="Ham Protein (% DM)")
    ndf_pct: float = Field(..., description="Nötr Deterjan Lif - NDF (% DM)")
    starch_pct: float = Field(..., description="Nişasta Oranı (% DM)")
    nel_mcal_kg: float = Field(..., description="Net Enerji Laktasyon (Mcal NE_L / kg DM)")
    methane_mitigation_pct: float = Field(0.0, description="Enterik Metan Azaltım Katsayısı (%)")

class RationIngredientShare(BaseModel):
    ingredient_id: str
    name: str
    kg_dm_per_cow_day: float
    percentage_of_diet: float
    daily_cost_tl: float

class TMRRationPlan(BaseModel):
    strategy_id: Literal["MAX_PROFIT", "ECO_LOW_METHANE", "BALANCED_PARETO"]
    strategy_title: str
    strategy_badge: str
    description: str
    ingredients: List[RationIngredientShare]
    total_dmi_kg: float
    daily_feed_cost_per_cow: float
    roughage_pct: float
    concentrate_pct: float
    crude_protein_pct: float
    ndf_pct: float
    starch_pct: float
    nel_density_mcal_kg: float
    predicted_milk_yield_kg: float
    daily_gross_revenue_per_cow: float
    daily_iofc_per_cow: float  # Income Over Feed Cost (Yem Maliyeti Üzeri Gelir)
    enteric_methane_g_day: float
    methane_intensity_g_per_kg: float
    carbon_reduction_pct: float
    carbon_credit_annual_savings_tl: float
    sara_safety_index: str  # "GÜVENLİ", "ORTA RİSK", "YÜKSEK GÜVENLİK"
    is_active: bool = False

class ParetoPoint(BaseModel):
    strategy_id: str
    name: str
    cost_tl_kg_dm: float
    methane_intensity_g_kg_milk: float
    iofc_tl_day: float

class MultiObjectiveOptimizationReport(BaseModel):
    baseline_strategy: str
    recommended_strategy: str
    plans: List[TMRRationPlan]
    pareto_frontier: List[ParetoPoint]
    herd_annual_profit_delta_tl: float
    herd_annual_co2e_reduction_kg: float

class TMRRationOptimizer:
    """
    Rasyon Formülasyonu ve Çok Amaçlı Pareto Optimizasyon Motoru
    """

    INGREDIENTS_CATALOG: Dict[str, FeedIngredient] = {
        "CORN_SILAGE": FeedIngredient(
            id="CORN_SILAGE",
            name="Mısır Silajı (Yüksek Kalite)",
            category="ROUGHAGE",
            cost_per_kg_dm=3.40,
            dm_pct=34.0,
            crude_protein_pct=8.2,
            ndf_pct=42.0,
            starch_pct=31.0,
            nel_mcal_kg=1.58,
            methane_mitigation_pct=0.0
        ),
        "ALFALFA_HAY": FeedIngredient(
            id="ALFALFA_HAY",
            name="Yonca Kuru Otu (Çiçeklenme Öncesi)",
            category="ROUGHAGE",
            cost_per_kg_dm=7.90,
            dm_pct=88.0,
            crude_protein_pct=19.5,
            ndf_pct=41.0,
            starch_pct=2.5,
            nel_mcal_kg=1.45,
            methane_mitigation_pct=0.0
        ),
        "BARLEY_GRAIN": FeedIngredient(
            id="BARLEY_GRAIN",
            name="Ezme Arpa / Mısır Tanesi",
            category="CONCENTRATE",
            cost_per_kg_dm=9.60,
            dm_pct=88.0,
            crude_protein_pct=11.5,
            ndf_pct=17.0,
            starch_pct=60.0,
            nel_mcal_kg=1.92,
            methane_mitigation_pct=-2.0
        ),
        "SOYBEAN_MEAL": FeedIngredient(
            id="SOYBEAN_MEAL",
            name="Soya Küspesi (%48 HP)",
            category="PROTEIN",
            cost_per_kg_dm=17.80,
            dm_pct=89.0,
            crude_protein_pct=48.0,
            ndf_pct=10.5,
            starch_pct=5.5,
            nel_mcal_kg=2.05,
            methane_mitigation_pct=0.0
        ),
        "WHEAT_BRAN": FeedIngredient(
            id="WHEAT_BRAN",
            name="Buğday Kepeği / Pamuk Küspesi",
            category="CONCENTRATE",
            cost_per_kg_dm=7.20,
            dm_pct=88.0,
            crude_protein_pct=16.0,
            ndf_pct=40.0,
            starch_pct=19.0,
            nel_mcal_kg=1.48,
            methane_mitigation_pct=0.0
        ),
        "BOVAER_3NOP_LIPID": FeedIngredient(
            id="BOVAER_3NOP_LIPID",
            name="3-NOP (Bovaer) & Korunmuş Yağ Kompleksi",
            category="ADDITIVE",
            cost_per_kg_dm=39.00,
            dm_pct=95.0,
            crude_protein_pct=0.0,
            ndf_pct=0.0,
            starch_pct=0.0,
            nel_mcal_kg=4.90,
            methane_mitigation_pct=-32.0  # Enterik metanojen arkeleri doğrudan inhibe eder
        ),
        "SODIUM_BICARBONATE": FeedIngredient(
            id="SODIUM_BICARBONATE",
            name="Sodyum Bikarbonat Rumen Tamponu",
            category="ADDITIVE",
            cost_per_kg_dm=14.50,
            dm_pct=99.0,
            crude_protein_pct=0.0,
            ndf_pct=0.0,
            starch_pct=0.0,
            nel_mcal_kg=0.0,
            methane_mitigation_pct=-3.0
        )
    }

    @classmethod
    def generate_optimization_plans(
        cls,
        active_strategy_id: str = "BALANCED_PARETO",
        milk_price_per_kg: float = 16.5,
        herd_size: int = 80
    ) -> MultiObjectiveOptimizationReport:
        """
        3 Çok Amaçlı Pareto Stratejisini Hesaplar
        """
        cat = cls.INGREDIENTS_CATALOG

        # -------------------------------------------------------------
        # Strateji 1: MAX_PROFIT (Maksimum Kâr & En Düşük Yem Maliyeti)
        # -------------------------------------------------------------
        # Amaç: Rasyon maliyetini en aza indirerek IOFC maksimizasyonu.
        # Yüksek mısır silajı + arpa, minimal katkı maddesi.
        dmi_1 = 22.2
        shares_1 = [
            ("CORN_SILAGE", 8.8),
            ("ALFALFA_HAY", 3.8),
            ("BARLEY_GRAIN", 5.2),
            ("SOYBEAN_MEAL", 2.6),
            ("WHEAT_BRAN", 1.6),
            ("BOVAER_3NOP_LIPID", 0.0),
            ("SODIUM_BICARBONATE", 0.2),
        ]
        plan_1 = cls._build_plan(
            strategy_id="MAX_PROFIT",
            title="Maksimum Kâr (En Düşük Maliyet)",
            badge="💰 MAKSİMUM IOFC",
            desc="Mısır silajı ve yerel tahıl ağırlıklı, düşük birim maliyetli ekonomik rasyon.",
            shares=shares_1,
            total_dmi=dmi_1,
            milk_yield=31.2,
            milk_price=milk_price_per_kg,
            ch4_baseline_g=390.0,
            ch4_reduction_pct=2.0,
            sara_safety="ORTA RİSK (%28.5 NDF)",
            herd_size=herd_size,
            is_active=(active_strategy_id == "MAX_PROFIT")
        )

        # -------------------------------------------------------------
        # Strateji 2: ECO_LOW_METHANE (Düşük Karbon & 3-NOP Yeşil Rasyon)
        # -------------------------------------------------------------
        # Amaç: Enterik metan salımını %30+ düşürerek karbon ayak izini en aza indirmek.
        # 3-NOP Bovaer + Korunmuş lipid + Yüksek yonca lifi.
        dmi_2 = 22.6
        shares_2 = [
            ("CORN_SILAGE", 6.8),
            ("ALFALFA_HAY", 5.6),
            ("BARLEY_GRAIN", 4.2),
            ("SOYBEAN_MEAL", 3.2),
            ("WHEAT_BRAN", 1.8),
            ("BOVAER_3NOP_LIPID", 0.7),
            ("SODIUM_BICARBONATE", 0.3),
        ]
        plan_2 = cls._build_plan(
            strategy_id="ECO_LOW_METHANE",
            title="Ekolojik Yeşil Rasyon (Düşük Karbon & 3-NOP)",
            badge="🌿 DÜŞÜK METAN (-%32)",
            desc="Bovaer (3-NOP) ve korunmuş yağ kompleksi ile metanojen arkeleri baskılayan iklim dostu rasyon.",
            shares=shares_2,
            total_dmi=dmi_2,
            milk_yield=32.4,
            milk_price=milk_price_per_kg,
            ch4_baseline_g=390.0,
            ch4_reduction_pct=32.5,
            sara_safety="GÜVENLİ (%33.8 NDF)",
            herd_size=herd_size,
            is_active=(active_strategy_id == "ECO_LOW_METHANE")
        )

        # -------------------------------------------------------------
        # Strateji 3: BALANCED_PARETO (Dengeli Pareto - SARA Korumalı)
        # -------------------------------------------------------------
        # Amaç: Hem kârlılığı koruyan, hem metanı %18 düşüren, hem de SARA asidozunu önleyen Pareto noktası.
        dmi_3 = 22.8
        shares_3 = [
            ("CORN_SILAGE", 7.8),
            ("ALFALFA_HAY", 4.8),
            ("BARLEY_GRAIN", 4.8),
            ("SOYBEAN_MEAL", 2.9),
            ("WHEAT_BRAN", 1.8),
            ("BOVAER_3NOP_LIPID", 0.3),
            ("SODIUM_BICARBONATE", 0.4),
        ]
        plan_3 = cls._build_plan(
            strategy_id="BALANCED_PARETO",
            title="Dengeli Pareto (SARA Korumalı & Optimum Kâr)",
            badge="⚖️ PARETO OPTİMUM",
            desc="SARA asidozunu tam tamponlayan, %18.5 metan tasarrufu sağlayan ve çiftlik kârını maksimize eden altın oran.",
            shares=shares_3,
            total_dmi=dmi_3,
            milk_yield=33.1,
            milk_price=milk_price_per_kg,
            ch4_baseline_g=390.0,
            ch4_reduction_pct=18.5,
            sara_safety="YÜKSEK GÜVENLİK (pH > 6.35)",
            herd_size=herd_size,
            is_active=(active_strategy_id == "BALANCED_PARETO")
        )

        plans = [plan_1, plan_2, plan_3]

        pareto_points = [
            ParetoPoint(
                strategy_id=p.strategy_id,
                name=p.strategy_title,
                cost_tl_kg_dm=round(p.daily_feed_cost_per_cow / p.total_dmi_kg, 2),
                methane_intensity_g_kg_milk=p.methane_intensity_g_per_kg,
                iofc_tl_day=p.daily_iofc_per_cow
            )
            for p in plans
        ]

        # 80 başlık sürü yıllık kâr farkı ve CO2e tasarrufu (Balanced vs Baseline Max Profit)
        delta_iofc_daily = (plan_3.daily_iofc_per_cow - plan_1.daily_iofc_per_cow) * herd_size
        annual_profit_delta = round(delta_iofc_daily * 365.0 + plan_3.carbon_credit_annual_savings_tl, 2)
        annual_co2e_reduction = round((plan_1.enteric_methane_g_day - plan_3.enteric_methane_g_day) / 1000.0 * 28.0 * herd_size * 365.0, 1)

        return MultiObjectiveOptimizationReport(
            baseline_strategy="MAX_PROFIT",
            recommended_strategy="BALANCED_PARETO",
            plans=plans,
            pareto_frontier=pareto_points,
            herd_annual_profit_delta_tl=annual_profit_delta,
            herd_annual_co2e_reduction_kg=annual_co2e_reduction
        )

    @classmethod
    def _build_plan(
        cls,
        strategy_id: str,
        title: str,
        badge: str,
        desc: str,
        shares: List[tuple],
        total_dmi: float,
        milk_yield: float,
        milk_price: float,
        ch4_baseline_g: float,
        ch4_reduction_pct: float,
        sara_safety: str,
        herd_size: int,
        is_active: bool
    ) -> TMRRationPlan:
        cat = cls.INGREDIENTS_CATALOG
        ing_shares: List[RationIngredientShare] = []
        total_cost = 0.0
        total_roughage_kg = 0.0
        total_concentrate_kg = 0.0
        weighted_cp = 0.0
        weighted_ndf = 0.0
        weighted_starch = 0.0
        weighted_nel = 0.0

        for ing_id, kg_val in shares:
            ing = cat[ing_id]
            pct = round((kg_val / total_dmi) * 100.0, 1)
            cost = round(kg_val * ing.cost_per_kg_dm, 2)
            total_cost += cost

            if ing.category == "ROUGHAGE":
                total_roughage_kg += kg_val
            else:
                total_concentrate_kg += kg_val

            weighted_cp += (kg_val / total_dmi) * ing.crude_protein_pct
            weighted_ndf += (kg_val / total_dmi) * ing.ndf_pct
            weighted_starch += (kg_val / total_dmi) * ing.starch_pct
            weighted_nel += (kg_val / total_dmi) * ing.nel_mcal_kg

            ing_shares.append(RationIngredientShare(
                ingredient_id=ing.id,
                name=ing.name,
                kg_dm_per_cow_day=kg_val,
                percentage_of_diet=pct,
                daily_cost_tl=cost
            ))

        # Gelir ve IOFC
        gross_rev = round(milk_yield * milk_price, 2)
        iofc = round(gross_rev - total_cost, 2)

        # Metan hesabı
        ch4_day = round(ch4_baseline_g * (1.0 - (ch4_reduction_pct / 100.0)), 1)
        methane_intensity = round(ch4_day / milk_yield, 2)

        # Karbon kredisi teşviği (1 ton CO2e azaltımı = ~650 TL karbon kredisi)
        saved_ch4_kg_annual = ((ch4_baseline_g - ch4_day) / 1000.0) * 365.0 * herd_size
        saved_co2e_tons = (saved_ch4_kg_annual * 28.0) / 1000.0
        carbon_credit_tl = round(saved_co2e_tons * 650.0, 2)

        return TMRRationPlan(
            strategy_id=strategy_id,
            strategy_title=title,
            strategy_badge=badge,
            description=desc,
            ingredients=ing_shares,
            total_dmi_kg=total_dmi,
            daily_feed_cost_per_cow=round(total_cost, 2),
            roughage_pct=round((total_roughage_kg / total_dmi) * 100.0, 1),
            concentrate_pct=round((total_concentrate_kg / total_dmi) * 100.0, 1),
            crude_protein_pct=round(weighted_cp, 1),
            ndf_pct=round(weighted_ndf, 1),
            starch_pct=round(weighted_starch, 1),
            nel_density_mcal_kg=round(weighted_nel, 2),
            predicted_milk_yield_kg=milk_yield,
            daily_gross_revenue_per_cow=gross_rev,
            daily_iofc_per_cow=iofc,
            enteric_methane_g_day=ch4_day,
            methane_intensity_g_per_kg=methane_intensity,
            carbon_reduction_pct=ch4_reduction_pct,
            carbon_credit_annual_savings_tl=carbon_credit_tl,
            sara_safety_index=sara_safety,
            is_active=is_active
        )
