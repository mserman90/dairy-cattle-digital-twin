import random
from datetime import datetime, timedelta
from typing import List, Optional
from models import (
    Animal, AnimalTelemetry, MilkingSession, DSSAssessment,
    XAIFactor, BarnZone, SortingGateState, FarmTwinState, FarmSustainabilityKPIs
)
from physiological_models import (
    WoodCurveParams, PhysiologicalProfile, RationComposition,
    PhysiologicalEngine
)
from financial_roi import FarmFinancialEngine
from edge_gateway import edge_gateway
from vision_twin import ComputerVisionTwinEngine
from rumen_twin import RumenBiochemicalEngine
from ration_optimizer import TMRRationOptimizer
from robotic_milking_twin import RoboticMilkingEngine
from biogas_energy_twin import CircularBiogasEnergyEngine
from barn_robotics_twin import robotics_fleet_engine
from calving_twin import CalvingDystociaEngine
from farm_devices_twin import farm_devices_engine
from genomic_breeding_twin import GenomicBreedingEngine

class FarmSimulator:
    def __init__(self):
        self.simulation_tick = 0
        self.simulation_running = True
        self.current_time = datetime.now()
        self.active_scenario: Optional[str] = None
        self.active_ration_strategy: str = "BALANCED_PARETO"

        # Current Herd Feeding Ration
        self.current_ration = RationComposition(
            roughage_pct=58.0,
            concentrate_pct=40.5,
            fat_supplement_pct=1.5,
            crude_protein_pct=16.8,
            neutral_detergent_fiber_pct=33.5
        )

        # Barn Zones initialization
        self.zones = [
            BarnZone(
                zone_id="ZONE-A",
                name="Bölüm A (Yüksek Verim Grubu)",
                temperature_c=22.5,
                relative_humidity_pct=58.0,
                thi_index=69.8,
                heat_stress_category="NORMAL",
                ventilation_fans_active=False,
                misting_active=False,
                animal_count=3
            ),
            BarnZone(
                zone_id="ZONE-B",
                name="Bölüm B (Orta Verim Grubu)",
                temperature_c=23.0,
                relative_humidity_pct=60.0,
                thi_index=70.5,
                heat_stress_category="NORMAL",
                ventilation_fans_active=False,
                misting_active=False,
                animal_count=3
            ),
            BarnZone(
                zone_id="ZONE-TREATMENT",
                name="Revir & İzolasyon Bölmesi",
                temperature_c=21.0,
                relative_humidity_pct=50.0,
                thi_index=67.2,
                heat_stress_category="NORMAL",
                ventilation_fans_active=False,
                misting_active=False,
                animal_count=0
            )
        ]

        self.sorting_gate = SortingGateState(
            gate_id="GATE-01",
            status="IDLE",
            last_diverted_animal_id=None,
            last_reason=None,
            last_updated=datetime.now()
        )

        # Raw Herd Configuration with Wood Lactation Curve Parameters
        raw_animals = [
            {
                "id": "TR-34-101", "name": "Sarıkız", "lact_no": 2, "dim": 85, "yield_avg": 34.5, "zone": "ZONE-A",
                "a": 22.5, "b": 0.22, "c": 0.0036, "bw": 640.0, "fat": 3.85
            },
            {
                "id": "TR-34-102", "name": "Benekli", "lact_no": 3, "dim": 120, "yield_avg": 38.0, "zone": "ZONE-A",
                "a": 24.2, "b": 0.24, "c": 0.0039, "bw": 660.0, "fat": 3.75
            },
            {
                "id": "TR-34-103", "name": "Papatya", "lact_no": 1, "dim": 45, "yield_avg": 29.5, "zone": "ZONE-A",
                "a": 17.8, "b": 0.18, "c": 0.0028, "bw": 570.0, "fat": 4.10
            },
            {
                "id": "TR-34-104", "name": "Yıldız", "lact_no": 2, "dim": 190, "yield_avg": 31.0, "zone": "ZONE-B",
                "a": 21.0, "b": 0.21, "c": 0.0034, "bw": 630.0, "fat": 3.90
            },
            {
                "id": "TR-34-105", "name": "Elif", "lact_no": 1, "dim": 60, "yield_avg": 28.0, "zone": "ZONE-B",
                "a": 17.0, "b": 0.17, "c": 0.0026, "bw": 560.0, "fat": 4.05
            },
            {
                "id": "TR-34-106", "name": "Nazlı", "lact_no": 4, "dim": 210, "yield_avg": 33.0, "zone": "ZONE-B",
                "a": 23.5, "b": 0.23, "c": 0.0040, "bw": 680.0, "fat": 3.70
            }
        ]

        self.animals: List[Animal] = []
        for r in raw_animals:
            wood_params = WoodCurveParams(a=r["a"], b=r["b"], c=r["c"])
            peak_dim, peak_yield = PhysiologicalEngine.get_peak_stats(wood_params)
            curve_points = PhysiologicalEngine.get_wood_curve_points(wood_params)

            # Initial physiological evaluation
            eval_metrics = PhysiologicalEngine.evaluate_energy_and_emissions(
                body_weight_kg=r["bw"],
                actual_yield_kg=r["yield_avg"],
                milk_fat_pct=r["fat"],
                dim=r["dim"],
                ration=self.current_ration
            )

            profile = PhysiologicalProfile(
                wood_params=wood_params,
                peak_dim=peak_dim,
                peak_yield=peak_yield,
                body_weight_kg=r["bw"],
                body_condition_score=3.25,
                dry_matter_intake_kg=eval_metrics["dmi_kg"],
                net_energy_balance_mcal=eval_metrics["energy_balance_mcal"],
                enteric_methane_g_day=eval_metrics["methane_g_day"],
                methane_intensity_g_per_kg_milk=eval_metrics["methane_intensity"],
                carbon_equivalent_kg_co2e=eval_metrics["co2_equivalent_kg"]
            )

            animal = Animal(
                id=r["id"],
                name=r["name"],
                lactation_number=r["lact_no"],
                days_in_milk=r["dim"],
                daily_average_yield=r["yield_avg"],
                current_zone=r["zone"],
                telemetry=AnimalTelemetry(
                    activity_index=40 + random.randint(-4, 4),
                    rumination_minutes_2h=26 + random.randint(-2, 2),
                    body_temperature_c=38.5 + round(random.uniform(-0.1, 0.2), 1),
                    lying_time_hours=11.5,
                    feed_intake_kg=profile.dry_matter_intake_kg
                ),
                latest_milking=MilkingSession(
                    timestamp=datetime.now() - timedelta(minutes=random.randint(10, 45)),
                    yield_kg=round(r["yield_avg"] / 2.0, 1),
                    conductivity_ms_cm=5.15,
                    milking_duration_sec=380
                ),
                dss=DSSAssessment(
                    mastitis_risk_score=0.08,
                    heat_stress_level="NONE",
                    estrus_probability=0.04,
                    overall_health_status="HEALTHY",
                    recommended_action="NONE",
                    xai_explanations=[]
                ),
                history_yield=[round(r["yield_avg"] + random.uniform(-0.5, 0.5), 1) for _ in range(5)],
                physiology=profile,
                lactation_curve=curve_points,
                vision=ComputerVisionTwinEngine.evaluate_cow_vision(r["id"], bcs_target=profile.body_condition_score, is_lame=False),
                rumen=RumenBiochemicalEngine.simulate_rumen_state(r["id"], concentrate_pct=self.current_ration.concentrate_pct, rumination_minutes_2h=26, is_acidosis_induced=False),
                milking_twin=RoboticMilkingEngine.simulate_quarter_milking(r["id"], total_session_yield_kg=r["yield_avg"] / 2.0, is_mastitis_induced=False),
                pedigree=GenomicBreedingEngine.HERD_COWS.get(r["id"])
            )
            self.animals.append(animal)

    def calculate_thi(self, temp_c: float, rh_pct: float) -> float:
        """NRC Standard THI (Temperature-Humidity Index) calculation"""
        t = temp_c
        rh = rh_pct
        thi = (1.8 * t + 32) - (0.55 - 0.0055 * rh) * (1.8 * t - 26)
        return round(thi, 1)

    def evaluate_zone_climate(self, zone: BarnZone):
        thi = self.calculate_thi(zone.temperature_c, zone.relative_humidity_pct)
        zone.thi_index = thi

        if thi < 68.0:
            zone.heat_stress_category = "NORMAL"
            zone.ventilation_fans_active = False
            zone.misting_active = False
        elif thi < 72.0:
            zone.heat_stress_category = "MILD_STRESS"
            zone.ventilation_fans_active = True
            zone.misting_active = False
        elif thi < 79.0:
            zone.heat_stress_category = "MODERATE_STRESS"
            zone.ventilation_fans_active = True
            zone.misting_active = False
        else:
            zone.heat_stress_category = "SEVERE_STRESS"
            zone.ventilation_fans_active = True
            zone.misting_active = True

    def evaluate_animal_dss(self, animal: Animal, zone: BarnZone):
        xai_factors: List[XAIFactor] = []
        mastitis_score = 0.05
        estrus_score = 0.04
        action = "NONE"

        # 1. Expected Wood yield comparison (Early Yield Deviation)
        expected_wood_yield = PhysiologicalEngine.calculate_wood_yield(
            animal.physiology.wood_params, animal.days_in_milk
        )
        observed_daily_yield = animal.latest_milking.yield_kg * 2.0  # approximate 2x milking
        yield_drop_pct = ((expected_wood_yield - observed_daily_yield) / expected_wood_yield) * 100

        if yield_drop_pct > 15.0:
            impact = min(0.35, yield_drop_pct / 80.0)
            mastitis_score += impact
            xai_factors.append(XAIFactor(
                metric="Wood Laktasyon Sapması",
                observed_value=f"{observed_daily_yield:.1f} kg/gün",
                baseline_value=f"{expected_wood_yield:.1f} kg (Wood Modeli)",
                impact_weight=round(impact, 2),
                description=f"Beklenen laktasyon eğrisinden %{yield_drop_pct:.1f} verim kaybı saptandı."
            ))

        # 2. Subclinical Mastitis Evaluation
        cond = animal.latest_milking.conductivity_ms_cm
        cond_base = 5.2
        if cond > 5.8:
            diff_pct = ((cond - cond_base) / cond_base) * 100
            impact = min(0.55, (cond - 5.5) / 2.0)
            mastitis_score += impact
            xai_factors.append(XAIFactor(
                metric="Süt Elektriksel İletkenliği",
                observed_value=f"{cond:.2f} mS/cm",
                baseline_value=f"{cond_base:.2f} mS/cm",
                impact_weight=round(impact, 2),
                description=f"Referans değerden %{diff_pct:.1f} yüksek. Meme dokusunda subklinik sızıntı/Na-Cl artışı."
            ))

        rum = animal.telemetry.rumination_minutes_2h
        if rum < 18:
            impact = 0.25
            mastitis_score += impact
            xai_factors.append(XAIFactor(
                metric="Geviş Getirme Süresi",
                observed_value=f"{rum} dk/2sa",
                baseline_value="25-30 dk/2sa",
                impact_weight=impact,
                description=f"Son 2 saatlik geviş süresi %{((26 - rum)/26)*100:.0f} azaldı. Sistemik stres veya ağrı göstergesi."
            ))

        temp = animal.telemetry.body_temperature_c
        if temp > 39.1:
            impact = 0.20
            mastitis_score += impact
            xai_factors.append(XAIFactor(
                metric="Vücut Sıcaklığı (Ateş)",
                observed_value=f"{temp:.1f}°C",
                baseline_value="38.5°C",
                impact_weight=impact,
                description="Hafif ateş/enflamasyon yanıtı tespit edildi."
            ))

        # 3. Estrus (Kızgınlık) Evaluation
        act = animal.telemetry.activity_index
        if act > 80:
            estrus_score = 0.88
            xai_factors.append(XAIFactor(
                metric="Lokomotor Aktivite Patlaması",
                observed_value=f"{act} adım/saat",
                baseline_value="40 adım/saat",
                impact_weight=0.70,
                description=f"Aktivite indeksi normalin {act/40:.1f} katına çıktı. Kızgınlık davranış paterni."
            ))
            if rum < 22:
                xai_factors.append(XAIFactor(
                    metric="Yeme/Geviş Dinamiği",
                    observed_value=f"{rum} dk",
                    baseline_value="26 dk",
                    impact_weight=0.20,
                    description="Kızgınlık sırasında beklenen geviş süresi gerilemesi."
                ))

        # 4. Energy Balance / Ketosis Risk
        if animal.physiology.net_energy_balance_mcal < -4.0:
            xai_factors.append(XAIFactor(
                metric="Negatif Enerji Dengesi (NEB)",
                observed_value=f"{animal.physiology.net_energy_balance_mcal} Mcal/gün",
                baseline_value=">= 0.0 Mcal/gün",
                impact_weight=0.30,
                description="Derin negatif enerji dengesi. Subklinik ketozis ve yağ mobilizasyonu riski."
            ))

        # 5. Computer Vision: Lameness (Topallık) & BCS (Kondisyon) Evaluation
        is_lame_alert = False
        if animal.vision:
            if animal.vision.lameness.score >= 2.5:
                is_lame_alert = animal.vision.lameness.score >= 3.0
                weight = min(0.80, 0.40 + (animal.vision.lameness.score - 2.0) * 0.20)
                xai_factors.append(XAIFactor(
                    metric="3D Kamera Yürüyüş Analizi (Topallık)",
                    observed_value=f"Skor {animal.vision.lameness.score:.1f} ({animal.vision.lameness.affected_hoof or 'Asimetri'})",
                    baseline_value="Skor 1.0 (Düz Sırt Çizgisi)",
                    impact_weight=round(weight, 2),
                    description=animal.vision.lameness.clinical_interpretation
                ))
            if animal.vision.bcs.score < 2.75:
                xai_factors.append(XAIFactor(
                    metric="3D Derinlik Kamera BCS Taraması",
                    observed_value=f"{animal.vision.bcs.score:.2f} (Düşük Kondisyon)",
                    baseline_value="3.00 - 3.25 (Optimal)",
                    impact_weight=0.35,
                    description=animal.vision.bcs.clinical_interpretation
                ))

        # 6. Rumen Biochemical & SARA Acidosis Evaluation
        is_sara_alert = False
        if animal.rumen and animal.rumen.assessment.sara_risk_score >= 0.60:
            is_sara_alert = True
            xai_factors.append(XAIFactor(
                metric="Rumen pH & SARA Asidoz Alarmı",
                observed_value=f"pH {animal.rumen.telemetry.rumen_ph:.2f} ({animal.rumen.assessment.hours_below_ph_5_8} sa < 5.8)",
                baseline_value="pH 6.20 - 6.80 (A:P > 2.5)",
                impact_weight=0.65,
                description=animal.rumen.assessment.clinical_interpretation
            ))

        # 7. Robotic Milking Quarter-Level Mastitis & SCC
        is_quarter_mastitis = False
        if animal.milking_twin and animal.milking_twin.is_any_quarter_diverted:
            is_quarter_mastitis = True
            inf_q = next((q for q in animal.milking_twin.quarters.values() if q.valve_destination == "SEPARATION_DRAIN"), None)
            if inf_q:
                mastitis_score = max(mastitis_score, 0.88)
                xai_factors.append(XAIFactor(
                    metric="Robotik 4 Lob Spektroskopik Mastitis",
                    observed_value=f"{inf_q.quarter_name_tr}: SCC {inf_q.somatic_cell_count:,} / İletkenlik {inf_q.conductivity_ms_cm} mS/cm",
                    baseline_value="<150.000 SCC / <5.5 mS/cm",
                    impact_weight=0.75,
                    description=f"Robot sağım ünitesi {inf_q.quarter_name_tr} lobunda klinik enfeksiyon saptayarak bu lobun {inf_q.yield_kg} kg sütünü otomatik atık vanasına tahliye etti."
                ))

        # 8. Environmental Heat Stress
        thi = zone.thi_index
        if thi >= 79:
            heat_stress = "SEVERE"
        elif thi >= 72:
            heat_stress = "MODERATE"
        elif thi >= 68:
            heat_stress = "MILD"
        else:
            heat_stress = "NONE"

        # 9. Calving & Dystocia Assessment (Faz 14)
        is_dystocia_alert = False
        is_calving_imminent = False
        if animal.calving:
            calv = animal.calving
            if calv.dystocia_assessment.alert_level == "CRITICAL_DYSTOCIA_ALARM":
                is_dystocia_alert = True
                xai_factors.append(XAIFactor(
                    metric="Distosi (Güç Doğum) Acil Müdahale Alarmı",
                    observed_value=f"2. Evre {calv.dystocia_assessment.stage_2_duration_minutes} dk / Pozisyon: {calv.dystocia_assessment.calf_presentation}",
                    baseline_value="2. Evre <70 dk / NORMAL_ANTERIOR (Ön Geliş)",
                    impact_weight=0.95,
                    description=calv.dystocia_assessment.recommended_action
                ))
            elif calv.dystocia_assessment.stage == "STAGE_1_CERVIX_DILATION":
                is_calving_imminent = True
                xai_factors.append(XAIFactor(
                    metric="Doğum Başlangıcı (1. Evre Servikal Sancı)",
                    observed_value=f"Isı Düşüşü: -{calv.telemetry.temp_drop_c:.2f}°C / Kuyruk Sancı Frekansı: {calv.telemetry.tail_raising_frequency_per_hr} kez/saat",
                    baseline_value="38.6°C / <5 kez/saat",
                    impact_weight=0.70,
                    description=calv.dystocia_assessment.recommended_action
                ))

        # Final Decision Synthesis
        mastitis_score = min(0.99, round(mastitis_score, 2))
        estrus_score = min(0.99, round(estrus_score, 2))

        if mastitis_score >= 0.70 or is_lame_alert or is_sara_alert or is_quarter_mastitis or is_dystocia_alert:
            status = "CRITICAL"
            action = "DIVERT_TO_TREATMENT_PEN"
            animal.gate_assignment = "TREATMENT_PEN"
            self.sorting_gate.status = "ROUTING_TREATMENT"
            self.sorting_gate.last_diverted_animal_id = animal.id
            if is_dystocia_alert:
                self.sorting_gate.last_reason = "Distosi (Güç Doğum) Acil Müdahale Alarmı"
            elif is_quarter_mastitis:
                self.sorting_gate.last_reason = "Robotik Çeyrek Meme Mastitis Alarmı"
            elif is_sara_alert:
                self.sorting_gate.last_reason = f"SARA Asidoz Alarmı (pH {animal.rumen.telemetry.rumen_ph:.2f})"
            elif is_lame_alert:
                self.sorting_gate.last_reason = f"Topallık Skoru {animal.vision.lameness.score:.1f} (Tırnak Bakım Sevk)"
            else:
                self.sorting_gate.last_reason = f"Yüksek Mastitis Riski (%{int(mastitis_score*100)})"
            self.sorting_gate.last_updated = datetime.now()
        elif is_calving_imminent:
            status = "WARNING"
            action = "DIVERT_TO_TREATMENT_PEN"
            animal.gate_assignment = "TREATMENT_PEN"
            self.sorting_gate.status = "ROUTING_TREATMENT"
            self.sorting_gate.last_diverted_animal_id = animal.id
            self.sorting_gate.last_reason = "Doğum Eli Kulağında (Doğumhane Sevk)"
            self.sorting_gate.last_updated = datetime.now()
        elif estrus_score >= 0.75:
            status = "WARNING"
            action = "INSPECT_FOR_INSEMINATION"
            animal.gate_assignment = "BARN_RETURN"

            # Faz 13: Genomik Eşleştirme Önerisi
            if animal.pedigree:
                matches = GenomicBreedingEngine.evaluate_mating_pairs_for_cow(animal.id)
                if matches:
                    top_m = matches[0]
                    xai_factors.append(XAIFactor(
                        metric="Akıllı Genomik Boğa Eşleştirmesi",
                        observed_value=f"Önerilen Boğa: {top_m.bull.bull_name} (NM$ ${top_m.bull.gebv.net_merit_dollars:,.0f})",
                        baseline_value=f"Akrabalık: %{top_m.progeny_inbreeding_f_pct:.2f} (<%6.25 Güvenli)",
                        impact_weight=0.85,
                        description=(
                            f"Kızgınlık tespit edildi. {top_m.recommendation_type}: "
                            f"Tahmini yavru Net Merit: ${top_m.expected_progeny_net_merit:,.0f} (+{top_m.expected_progeny_milk_kg:,.0f} kg süt). "
                            f"{top_m.mating_rationale}"
                        )
                    ))
        elif mastitis_score >= 0.35 or heat_stress in ["MODERATE", "SEVERE"] or animal.physiology.net_energy_balance_mcal < -4.0:
            status = "WARNING"
            action = "ACTIVATE_MISTING" if heat_stress == "SEVERE" else "NONE"
            animal.gate_assignment = "BARN_RETURN"
        else:
            status = "HEALTHY"
            action = "NONE"
            animal.gate_assignment = "BARN_RETURN"

        animal.dss = DSSAssessment(
            mastitis_risk_score=mastitis_score,
            heat_stress_level=heat_stress,
            estrus_probability=estrus_score,
            overall_health_status=status,
            recommended_action=action,
            xai_explanations=xai_factors
        )

    def tick(self):
        """Advance the digital twin simulation by one time step"""
        self.simulation_tick += 1
        self.current_time += timedelta(minutes=15)

        # Update barn zones
        for zone in self.zones:
            if zone.zone_id == "ZONE-TREATMENT":
                continue
            if not self.active_scenario or self.active_scenario != "heatwave":
                zone.temperature_c = max(18.0, min(26.0, zone.temperature_c + random.uniform(-0.3, 0.3)))
                zone.relative_humidity_pct = max(45.0, min(65.0, zone.relative_humidity_pct + random.uniform(-0.5, 0.5)))
            self.evaluate_zone_climate(zone)

        # Update animals
        for animal in self.animals:
            zone = next((z for z in self.zones if z.zone_id == animal.current_zone), self.zones[0])
            
            if animal.dss.overall_health_status == "HEALTHY":
                animal.telemetry.activity_index = max(30, min(55, animal.telemetry.activity_index + random.randint(-2, 2)))
                animal.telemetry.rumination_minutes_2h = max(22, min(32, animal.telemetry.rumination_minutes_2h + random.randint(-1, 1)))
                animal.telemetry.body_temperature_c = round(max(38.3, min(38.8, animal.telemetry.body_temperature_c + random.uniform(-0.05, 0.05)), 1))

            # Recalculate physiology
            eval_metrics = PhysiologicalEngine.evaluate_energy_and_emissions(
                body_weight_kg=animal.physiology.body_weight_kg,
                actual_yield_kg=animal.latest_milking.yield_kg * 2.0,
                milk_fat_pct=3.85,
                dim=animal.days_in_milk,
                ration=self.current_ration
            )
            animal.physiology.dry_matter_intake_kg = eval_metrics["dmi_kg"]
            animal.physiology.net_energy_balance_mcal = eval_metrics["energy_balance_mcal"]
            animal.physiology.enteric_methane_g_day = eval_metrics["methane_g_day"]
            animal.physiology.methane_intensity_g_per_kg_milk = eval_metrics["methane_intensity"]
            animal.physiology.carbon_equivalent_kg_co2e = eval_metrics["co2_equivalent_kg"]

            self.evaluate_animal_dss(animal, zone)

    def trigger_scenario(self, scenario_type: str, target_animal_id: Optional[str] = None):
        """Inject specific real-world anomalies into the Digital Twin"""
        self.active_scenario = scenario_type

        if scenario_type == "heatwave":
            for zone in self.zones:
                if zone.zone_id != "ZONE-TREATMENT":
                    zone.temperature_c = 34.5
                    zone.relative_humidity_pct = 76.0
                    self.evaluate_zone_climate(zone)
            for animal in self.animals:
                zone = next((z for z in self.zones if z.zone_id == animal.current_zone), self.zones[0])
                self.evaluate_animal_dss(animal, zone)

        elif scenario_type == "mastitis":
            target_id = target_animal_id or "TR-34-102"
            animal = next((a for a in self.animals if a.id == target_id), None)
            if animal:
                animal.milking_twin = RoboticMilkingEngine.simulate_quarter_milking(
                    animal.id,
                    total_session_yield_kg=animal.daily_average_yield / 2.0,
                    is_mastitis_induced=True,
                    infected_quarter="LR",
                    severity=1.35
                )
                animal.latest_milking.conductivity_ms_cm = 6.85
                animal.latest_milking.yield_kg = round(animal.daily_average_yield * 0.35, 1)  # sharp drop
                animal.telemetry.rumination_minutes_2h = 11
                animal.telemetry.body_temperature_c = 39.5
                animal.telemetry.activity_index = 26
                zone = next((z for z in self.zones if z.zone_id == animal.current_zone), self.zones[0])
                self.evaluate_animal_dss(animal, zone)

        elif scenario_type == "estrus":
            target_id = target_animal_id or "TR-34-105"
            animal = next((a for a in self.animals if a.id == target_id), None)
            if animal:
                animal.telemetry.activity_index = 115
                animal.telemetry.rumination_minutes_2h = 18
                animal.telemetry.lying_time_hours = 8.0
                zone = next((z for z in self.zones if z.zone_id == animal.current_zone), self.zones[0])
                self.evaluate_animal_dss(animal, zone)

        elif scenario_type == "ration_optimize":
            self.apply_ration_strategy("BALANCED_PARETO")
            for animal in self.animals:
                zone = next((z for z in self.zones if z.zone_id == animal.current_zone), self.zones[0])
                self.evaluate_animal_dss(animal, zone)

        elif scenario_type == "lameness":
            target_id = target_animal_id or "TR-34-104"
            animal = next((a for a in self.animals if a.id == target_id), None)
            if animal:
                animal.vision = ComputerVisionTwinEngine.evaluate_cow_vision(
                    animal.id, bcs_target=3.10, is_lame=True, lameness_severity=3.5
                )
                animal.telemetry.activity_index = 24  # Reduced walking due to hoof pain
                animal.telemetry.lying_time_hours = 14.5  # Excess lying time
                zone = next((z for z in self.zones if z.zone_id == animal.current_zone), self.zones[0])
                self.evaluate_animal_dss(animal, zone)

        elif scenario_type == "sara":
            target_id = target_animal_id or "TR-34-103"
            animal = next((a for a in self.animals if a.id == target_id), None)
            if animal:
                animal.rumen = RumenBiochemicalEngine.simulate_rumen_state(
                    animal.id, concentrate_pct=58.0, rumination_minutes_2h=11, is_acidosis_induced=True, severity=1.35
                )
                animal.telemetry.rumination_minutes_2h = 11
                animal.latest_milking.yield_kg = round(animal.latest_milking.yield_kg * 0.88, 1)  # milk fat/yield depression
                zone = next((z for z in self.zones if z.zone_id == animal.current_zone), self.zones[0])
                self.evaluate_animal_dss(animal, zone)

        elif scenario_type == "calving_imminent":
            target_id = target_animal_id or "TR-34-106"
            animal = next((a for a in self.animals if a.id == target_id), None)
            if animal:
                animal.calving = CalvingDystociaEngine.evaluate_cow_calving(
                    cow_id=animal.id, cow_name=animal.name, gestation_days=283, scenario="imminent"
                )
                animal.telemetry.body_temperature_c = 37.85
                animal.telemetry.rumination_minutes_2h = 14
                zone = next((z for z in self.zones if z.zone_id == animal.current_zone), self.zones[0])
                self.evaluate_animal_dss(animal, zone)

        elif scenario_type == "dystocia":
            target_id = target_animal_id or "TR-34-106"
            animal = next((a for a in self.animals if a.id == target_id), None)
            if animal:
                animal.calving = CalvingDystociaEngine.evaluate_cow_calving(
                    cow_id=animal.id, cow_name=animal.name, gestation_days=283, scenario="dystocia"
                )
                animal.telemetry.body_temperature_c = 37.80
                animal.telemetry.rumination_minutes_2h = 8
                animal.telemetry.activity_index = 85
                zone = next((z for z in self.zones if z.zone_id == animal.current_zone), self.zones[0])
                self.evaluate_animal_dss(animal, zone)

        elif scenario_type == "colostrum_brix":
            target_id = target_animal_id or "TR-34-102"
            animal = next((a for a in self.animals if a.id == target_id), None)
            if animal:
                animal.calving = CalvingDystociaEngine.evaluate_cow_calving(
                    cow_id=animal.id, cow_name=animal.name, gestation_days=284, scenario="calved"
                )
                zone = next((z for z in self.zones if z.zone_id == animal.current_zone), self.zones[0])
                self.evaluate_animal_dss(animal, zone)

        elif scenario_type == "reset":
            self.active_scenario = None
            self.__init__()

    def apply_ration_strategy(self, strategy_id: str) -> dict:
        if strategy_id not in ["MAX_PROFIT", "ECO_LOW_METHANE", "BALANCED_PARETO"]:
            raise ValueError(f"Geçersiz rasyon stratejisi: {strategy_id}")
        self.active_ration_strategy = strategy_id
        report = TMRRationOptimizer.generate_optimization_plans(active_strategy_id=strategy_id)
        plan = next(p for p in report.plans if p.strategy_id == strategy_id)

        self.current_ration.roughage_pct = plan.roughage_pct
        self.current_ration.concentrate_pct = plan.concentrate_pct
        self.current_ration.crude_protein_pct = plan.crude_protein_pct
        self.current_ration.neutral_detergent_fiber_pct = plan.ndf_pct

        if strategy_id == "ECO_LOW_METHANE":
            self.current_ration.fat_supplement_pct = 3.2
        elif strategy_id == "BALANCED_PARETO":
            self.current_ration.fat_supplement_pct = 1.8
        else:
            self.current_ration.fat_supplement_pct = 0.5

        # Sürüdeki hayvanların fizyolojik verilerini yeni rasyonla güncelle
        for animal in self.animals:
            # Rasyonun sağladığı süt verim etkisi
            yield_multiplier = plan.predicted_milk_yield_kg / 32.0
            actual_yield = round(animal.daily_average_yield * yield_multiplier, 1)

            eval_metrics = PhysiologicalEngine.evaluate_energy_and_emissions(
                body_weight_kg=animal.physiology.body_weight_kg,
                actual_yield_kg=actual_yield,
                milk_fat_pct=3.85,
                dim=animal.days_in_milk,
                ration=self.current_ration
            )
            animal.physiology.dry_matter_intake_kg = eval_metrics["dmi_kg"]
            animal.physiology.net_energy_balance_mcal = eval_metrics["energy_balance_mcal"]

            # 3-NOP / Tannin / Lipit metan azaltım etkisi
            mitigated_ch4 = round(eval_metrics["methane_g_day"] * (1.0 - (plan.carbon_reduction_pct / 100.0)), 1)
            animal.physiology.enteric_methane_g_day = mitigated_ch4
            animal.physiology.methane_intensity_g_per_kg_milk = round(mitigated_ch4 / max(1.0, actual_yield), 2)
            animal.physiology.carbon_equivalent_kg_co2e = round((mitigated_ch4 / 1000.0) * 28.0, 2)

            # Rumen profili güncellemesi
            if animal.rumen and not (self.active_scenario == "sara" and animal.id == "TR-34-103"):
                is_acid = (strategy_id == "MAX_PROFIT" and animal.days_in_milk < 60)
                animal.rumen = RumenBiochemicalEngine.simulate_rumen_state(
                    animal_id=animal.id,
                    concentrate_pct=self.current_ration.concentrate_pct,
                    rumination_minutes_2h=animal.telemetry.rumination_minutes_2h,
                    is_acidosis_induced=is_acid
                )

        return {
            "status": "success",
            "applied_strategy": strategy_id,
            "plan": plan
        }

    def manual_gate_override(self, new_status: str):
        if new_status in ["IDLE", "ROUTING_NORMAL", "ROUTING_TREATMENT"]:
            self.sorting_gate.status = new_status
            self.sorting_gate.last_updated = datetime.now()

    def get_sustainability_kpis(self) -> FarmSustainabilityKPIs:
        total_methane_g = sum(a.physiology.enteric_methane_g_day for a in self.animals)
        total_methane_kg = round(total_methane_g / 1000.0, 2)
        total_co2e_kg = round(total_methane_kg * 28.0, 2)
        total_milk_kg = sum(a.latest_milking.yield_kg * 2.0 for a in self.animals)
        total_dmi_kg = sum(a.physiology.dry_matter_intake_kg for a in self.animals)

        avg_intensity = round(total_methane_g / max(1.0, total_milk_kg), 1)
        fcr = round(total_milk_kg / max(1.0, total_dmi_kg), 2)

        return FarmSustainabilityKPIs(
            total_daily_methane_kg=total_methane_kg,
            total_co2e_kg=total_co2e_kg,
            avg_methane_intensity=avg_intensity,
            feed_conversion_efficiency=fcr
        )

    def get_full_state(self) -> FarmTwinState:
        total_milk = sum(a.latest_milking.yield_kg * 2.0 for a in self.animals)
        total_dmi = sum(a.physiology.dry_matter_intake_kg for a in self.animals)
        mastitis_cases = sum(1 for a in self.animals if a.dss.mastitis_risk_score > 0.6)
        estrus_cases = sum(1 for a in self.animals if a.dss.estrus_probability > 0.7)
        is_opt = (self.current_ration.fat_supplement_pct > 2.0 or self.active_scenario == "ration_optimize")

        fin_output = FarmFinancialEngine.calculate_economics(
            herd_size=len(self.animals),
            daily_total_milk_kg=total_milk,
            daily_total_dmi_kg=total_dmi,
            roughage_pct=self.current_ration.roughage_pct,
            concentrate_pct=self.current_ration.concentrate_pct,
            is_ration_optimized=is_opt,
            subclinical_cases_caught_early=max(1, mastitis_cases),
            estrus_detected_timely=max(1, estrus_cases)
        )

        # Biyogaz & Kojenerasyon Enerji İkizi
        active_fans = sum(3 for z in self.zones if z.ventilation_fans_active)
        is_heat = any(z.thi_index >= 72 for z in self.zones)
        energy_profile = CircularBiogasEnergyEngine.simulate_farm_energy(
            herd_size=80,
            active_fans_count=max(2, active_fans),
            is_heat_wave=is_heat
        )

        # Otonom Ahır Robot Filosu İkizi
        robotics_profile = robotics_fleet_engine.tick_robot_fleet()

        # Doğumhane, Distosi & Buzağı İkizi (Faz 14)
        maternity_summary = CalvingDystociaEngine.get_farm_maternity_summary(active_scenario=self.active_scenario)

        # Genomik Seleksiyon & Çiftleştirme İkizi (Faz 13)
        genomics_summary = GenomicBreedingEngine.get_herd_genomic_summary()

        # Çiftlik Cihazları & IoT Donanım Filosu İkizi (Faz 18)
        treated_count = len(edge_gateway.state.active_treatments) if edge_gateway.state else 0
        crit_cows = sum(1 for a in self.animals if a.dss.overall_health_status == "CRITICAL")
        max_thi = max((z.thi_index for z in self.zones), default=70.0)
        avg_temp = sum(z.temperature_c for z in self.zones) / max(1, len(self.zones))
        avg_rh = sum(z.relative_humidity_pct for z in self.zones) / max(1, len(self.zones))
        devices_profile = farm_devices_engine.tick_all_devices(
            ambient_temp_c=avg_temp,
            ambient_rh_pct=avg_rh,
            thi_index=max_thi,
            treated_cows_count=treated_count,
            active_critical_cows=crit_cows,
            heatwave_active=(self.active_scenario == "heatwave")
        )

        return FarmTwinState(
            farm_name="AgriTwin Akıllı Süt Çiftliği Dijital İkizi (Faz 4: Endüstriyel)",
            simulation_tick=self.simulation_tick,
            simulation_running=self.simulation_running,
            current_time=self.current_time,
            active_scenario=self.active_scenario,
            barn_zones=self.zones,
            animals=self.animals,
            sorting_gate=self.sorting_gate,
            current_ration=self.current_ration,
            active_ration_strategy=self.active_ration_strategy,
            sustainability=self.get_sustainability_kpis(),
            financials=fin_output,
            edge_gateway=edge_gateway.state,
            energy=energy_profile,
            robotics=robotics_profile,
            maternity=maternity_summary,
            genomics=genomics_summary,
            devices=devices_profile
        )

# Global singleton instance
simulator_engine = FarmSimulator()
