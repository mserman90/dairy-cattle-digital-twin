import pytest
from physiological_models import (
    WoodCurveParams, PhysiologicalEngine, RationComposition
)
from financial_roi import FarmFinancialEngine, FinancialParameters
from edge_gateway import EdgeGatewayEngine
from icar_ade import ICARADEAdapter
from simulator import simulator_engine

def test_wood_lactation_curve():
    params = WoodCurveParams(a=24.2, b=0.24, c=0.0039)
    peak_dim, peak_yield = PhysiologicalEngine.get_peak_stats(params)
    assert 50 <= peak_dim <= 70, f"Peak DIM unexpected: {peak_dim}"
    assert 35.0 <= peak_yield <= 55.0, f"Peak yield unexpected: {peak_yield}"

    # Day 100 yield should be positive and realistic
    yield_100 = PhysiologicalEngine.calculate_wood_yield(params, 100)
    assert 25.0 <= yield_100 <= 55.0

def test_energy_and_methane_emissions():
    ration = RationComposition(roughage_pct=55.0, concentrate_pct=43.5, fat_supplement_pct=1.5)
    metrics = PhysiologicalEngine.evaluate_energy_and_emissions(
        body_weight_kg=650.0,
        actual_yield_kg=35.0,
        milk_fat_pct=3.8,
        dim=90,
        ration=ration
    )
    assert 18.0 <= metrics["dmi_kg"] <= 28.0, "DMI out of physiological range"
    assert 300.0 <= metrics["methane_g_day"] <= 550.0, "Enteric methane out of IPCC range"
    assert 8.0 <= metrics["methane_intensity"] <= 16.0, "Methane intensity out of range"
    assert metrics["co2_equivalent_kg"] > 5.0

def test_financial_roi_engine():
    fin = FarmFinancialEngine.calculate_economics(
        herd_size=80,
        daily_total_milk_kg=2400.0,
        daily_total_dmi_kg=1800.0,
        roughage_pct=58.0,
        concentrate_pct=42.0,
        is_ration_optimized=False,
        subclinical_cases_caught_early=2,
        estrus_detected_timely=3
    )
    assert fin.daily_gross_milk_revenue > 30000.0
    assert fin.daily_net_margin_over_feed > 0.0
    assert 0.5 <= fin.estimated_payback_period_years <= 1.8, f"Payback period unexpected: {fin.estimated_payback_period_years}"

def test_edge_gateway_offline_resilience():
    edge = EdgeGatewayEngine()
    assert edge.state.is_online is True

    # Simulate offline mode
    edge.toggle_connection()
    assert edge.state.is_online is False
    assert edge.state.connection_mode == "OFFLINE_EDGE_FALLBACK"

    # Send high conductivity packet -> verify local failsafe
    actuation = edge.process_telemetry_packet({"animal_id": "TR-34-102"}, conductivity=6.8)
    assert actuation == "LOCAL_FAILSAFE_ROUTING_TREATMENT"
    assert edge.state.offline_buffered_packets == 1
    assert edge.state.local_fail_safe_actuations_count == 1

    # Reconnect
    edge.toggle_connection()
    assert edge.state.is_online is True
    assert edge.state.offline_buffered_packets == 0

def test_icar_ade_export():
    doc = ICARADEAdapter.export_to_icar_ade(simulator_engine.animals)
    assert "header" in doc
    assert "records" in doc
    assert len(doc["records"]) == len(simulator_engine.animals)
    first = doc["records"][0]
    assert first["animal"]["country_code"] == "TR"
    assert len(first["milk_recordings"]) > 0
from ai_advisor import AgriTwinAIAdvisor
from spatial_rtls import SpatialRTLSEngine

def test_ai_advisor():
    # Health query
    res_health = AgriTwinAIAdvisor.answer_query("Hangi inekler hasta veya revire ayrıldı?")
    assert "query" in res_health
    assert "answer" in res_health
    assert len(res_health["answer"]) > 20

    # Financial query
    res_fin = AgriTwinAIAdvisor.answer_query("Yem maliyetimiz ve ROI ne durumda?")
    assert "Finansal" in res_fin["answer"] or "TL" in res_fin["answer"]

def test_spatial_rtls_grid():
    engine = SpatialRTLSEngine()
    cells = engine.compute_grid(base_temp_a=24.0, base_temp_b=24.5, rh_pct=60.0, fans_active=True)
    assert len(cells) == 40  # 8 x 5
    assert all(c.thi_index > 0 for c in cells)

    # Test animal positions
    positions = engine.update_animal_positions(
        animals=simulator_engine.animals,
        heat_stress_active=True,
        fans_active=True
    )
    assert len(positions) == len(simulator_engine.animals)
    first_cow = positions[0]
    assert 0 <= first_cow.x_m <= 40.0
    assert 0 <= first_cow.y_m <= 25.0
from vision_twin import ComputerVisionTwinEngine

def test_vision_twin_lameness_and_bcs():
    # 1. Healthy cow
    vis_healthy = ComputerVisionTwinEngine.evaluate_cow_vision("TR-34-101", bcs_target=3.25, is_lame=False)
    assert vis_healthy.lameness.score == 1.0
    assert vis_healthy.lameness.back_curvature_index < 0.15
    assert vis_healthy.bcs.score == 3.25
    assert vis_healthy.bcs.condition_category == "OPTIMAL"
    assert len(vis_healthy.spine_curvature_points) > 5

    # 2. Lame cow (sole ulcer)
    vis_lame = ComputerVisionTwinEngine.evaluate_cow_vision("TR-34-104", bcs_target=3.10, is_lame=True, lameness_severity=3.6)
    assert vis_lame.lameness.score >= 3.0
    assert vis_lame.lameness.back_curvature_index > 0.40
    assert vis_lame.lameness.affected_hoof is not None
    # Verify spine arching elevation is positive at center (parabolic arch)
    mid_spine = vis_lame.spine_curvature_points[len(vis_lame.spine_curvature_points)//2]
    assert mid_spine.z_elevation_cm > 2.0

from rumen_twin import RumenBiochemicalEngine

def test_rumen_biochemical_sara():
    # 1. Healthy cow rumen fermentation
    rumen_healthy = RumenBiochemicalEngine.simulate_rumen_state(
        animal_id="TR-34-101",
        concentrate_pct=40.0,
        rumination_minutes_2h=28,
        is_acidosis_induced=False
    )
    assert rumen_healthy.telemetry.rumen_ph >= 6.1
    assert rumen_healthy.assessment.acidosis_stage == "NORMAL"
    assert rumen_healthy.assessment.sara_risk_score < 0.20
    assert rumen_healthy.assessment.buffer_supplement_needed is False
    assert len(rumen_healthy.hourly_ph_curve) == 24

    # 2. Induced SARA cow rumen fermentation
    rumen_sara = RumenBiochemicalEngine.simulate_rumen_state(
        animal_id="TR-34-103",
        concentrate_pct=65.0,
        rumination_minutes_2h=12,
        is_acidosis_induced=True,
        severity=1.2
    )
    assert rumen_sara.telemetry.rumen_ph < 5.8
    assert rumen_sara.assessment.acidosis_stage in ["SARA_ACIDOSIS", "ACUTE_ACIDOSIS"]
    assert rumen_sara.assessment.sara_risk_score > 0.60
    assert rumen_sara.assessment.hours_below_ph_5_8 > 3.0
    assert rumen_sara.assessment.buffer_supplement_needed is True
    assert rumen_sara.telemetry.acetate_to_propionate_ratio < 2.0

from ration_optimizer import TMRRationOptimizer

def test_ration_multi_objective_optimization():
    # 1. Generate multi-objective plans
    report = TMRRationOptimizer.generate_optimization_plans(active_strategy_id="BALANCED_PARETO")
    assert len(report.plans) == 3
    assert len(report.pareto_frontier) == 3

    p_profit = next(p for p in report.plans if p.strategy_id == "MAX_PROFIT")
    p_eco = next(p for p in report.plans if p.strategy_id == "ECO_LOW_METHANE")
    p_pareto = next(p for p in report.plans if p.strategy_id == "BALANCED_PARETO")

    # 2. Economic check: MAX_PROFIT has lower feed cost per kg DM
    cost_profit_kg = p_profit.daily_feed_cost_per_cow / p_profit.total_dmi_kg
    cost_eco_kg = p_eco.daily_feed_cost_per_cow / p_eco.total_dmi_kg
    assert cost_profit_kg < cost_eco_kg

    # 3. Environmental check: ECO_LOW_METHANE cuts enteric methane by > 30%
    assert p_eco.carbon_reduction_pct >= 30.0
    assert p_eco.enteric_methane_g_day < p_profit.enteric_methane_g_day

    # 4. Balanced Pareto check: Safe SARA buffering and good IOFC
    assert p_pareto.daily_iofc_per_cow > 340.0
    assert p_pareto.ndf_pct >= 28.0

    # 5. Apply strategy to simulator
    res = simulator_engine.apply_ration_strategy("ECO_LOW_METHANE")
    assert res["status"] == "success"
    assert simulator_engine.active_ration_strategy == "ECO_LOW_METHANE"
    assert simulator_engine.current_ration.fat_supplement_pct > 2.0

    # Total herd daily methane should be significantly lower under ECO strategy
    kpis = simulator_engine.get_sustainability_kpis()
    assert kpis.total_daily_methane_kg < 2.50

from robotic_milking_twin import RoboticMilkingEngine

def test_robotic_quarter_milking_twin():
    # 1. Healthy cow 4-quarter milking
    session_healthy = RoboticMilkingEngine.simulate_quarter_milking(
        animal_id="TR-34-101",
        total_session_yield_kg=16.0,
        is_mastitis_induced=False
    )
    assert len(session_healthy.quarters) == 4
    assert set(session_healthy.quarters.keys()) == {"RF", "RR", "LF", "LR"}
    assert session_healthy.is_any_quarter_diverted is False
    assert session_healthy.diverted_waste_kg == 0.0
    assert session_healthy.accepted_to_tank_kg > 15.0
    for q in session_healthy.quarters.values():
        assert q.valve_destination == "MAIN_TANK"
        assert q.somatic_cell_count < 200000
        assert q.conductivity_ms_cm < 5.6

    # 2. Infected cow (Left Rear quarter mastitis)
    session_infected = RoboticMilkingEngine.simulate_quarter_milking(
        animal_id="TR-34-102",
        total_session_yield_kg=14.0,
        is_mastitis_induced=True,
        infected_quarter="LR",
        severity=1.3
    )
    assert session_infected.is_any_quarter_diverted is True
    assert session_infected.diverted_waste_kg > 0.0
    assert session_infected.accepted_to_tank_kg > 0.0  # 3 healthy quarters still accepted!
    lr_q = session_infected.quarters["LR"]
    assert lr_q.valve_destination == "SEPARATION_DRAIN"
    assert lr_q.somatic_cell_count > 500000
    assert lr_q.conductivity_ms_cm > 6.5
    assert session_infected.quarters["RF"].valve_destination == "MAIN_TANK"

    # 3. Simulator integration check
    simulator_engine.trigger_scenario("mastitis", target_animal_id="TR-34-102")
    cow_102 = next(a for a in simulator_engine.animals if a.id == "TR-34-102")
    assert cow_102.milking_twin is not None
    assert cow_102.milking_twin.is_any_quarter_diverted is True
    assert cow_102.dss.overall_health_status == "CRITICAL"
    assert cow_102.gate_assignment == "TREATMENT_PEN"

from biogas_energy_twin import CircularBiogasEnergyEngine

def test_biogas_energy_circular_twin():
    # 1. Simulate 80-head farm energy twin
    en = CircularBiogasEnergyEngine.simulate_farm_energy(herd_size=80, active_fans_count=4, is_heat_wave=False)
    assert en.manure.total_manure_kg_day > 4000.0
    assert en.digester.daily_biogas_production_m3 > 180.0
    assert en.digester.methane_content_pct > 60.0
    assert en.chp.daily_electricity_generated_kwh > en.consumption.total_consumption_kwh_day
    assert en.chp.is_net_zero_energy is True
    assert en.chp.self_sufficiency_ratio_pct > 150.0  # Surplus energy generated
    assert en.chp.net_grid_export_kwh > 200.0
    assert en.fertilizer.annual_chemical_fertilizer_saving_tl > 300000.0

    # 2. Simulator integration state check
    state = simulator_engine.get_full_state()
    assert state.energy is not None
    assert state.energy.chp.daily_electricity_generated_kwh > 400.0

from barn_robotics_twin import BarnRoboticsEngine

def test_barn_robotics_fleet_twin():
    engine = BarnRoboticsEngine()
    profile = engine.tick_robot_fleet(cows_near_pusher=False, cows_near_collector=False)

    # 1. Feed Pusher check
    assert profile.pusher.robot_id == "ROBOT-PUSHER-JUNO"
    assert profile.pusher.status == "PUSHING"
    assert profile.pusher.y_m == 12.5
    assert profile.pusher.speed_m_sec > 0.0
    assert profile.pusher.auger_rpm > 0
    assert profile.pusher.battery_pct > 50.0
    assert profile.pusher.dmi_boost_pct > 2.0

    # 2. Manure Collector check
    assert profile.collector.robot_id == "ROBOT-MANURE-VAC"
    assert profile.collector.status == "VACUUMING"
    assert profile.collector.water_spray_active is True
    assert profile.collector.tank_fill_pct > 0.0
    assert profile.collector.daily_manure_collected_kg > 1000.0
    assert profile.collector.lameness_reduction_pct >= 25.0

    # 3. Obstacle avoidance check
    stopped_profile = engine.tick_robot_fleet(cows_near_pusher=True, cows_near_collector=True)
    assert stopped_profile.pusher.status == "OBSTACLE_AVOIDANCE"
    assert stopped_profile.pusher.speed_m_sec == 0.0
    assert stopped_profile.collector.status == "OBSTACLE_AVOIDANCE"

    # 4. Simulator integration state
    state = simulator_engine.get_full_state()
    assert state.robotics is not None
    assert state.robotics.fleet_economic_value_annual_tl > 100000.0

from calving_twin import CalvingDystociaEngine
from report_generator import FarmAuditReportGenerator

def test_calving_dystocia_and_colostrum_twin():
    # 1. Colostrum optical Brix & IgG testing
    col_high = CalvingDystociaEngine.evaluate_colostrum("TR-34-106", yield_liters=6.5, brix_pct=24.5)
    assert col_high.quality_grade == "EXCELLENT_GREEN"
    assert col_high.igg_concentration_g_per_l > 70.0
    assert col_high.fpt_risk == "LOW_PROTECTED"

    col_poor = CalvingDystociaEngine.evaluate_colostrum("TR-34-105", yield_liters=4.0, brix_pct=15.0)
    assert col_poor.quality_grade == "POOR_RED"
    assert col_poor.fpt_risk == "HIGH_FAILURE_OF_PASSIVE_TRANSFER"

    # 2. Imminent calving evaluation
    twin_imm = CalvingDystociaEngine.evaluate_cow_calving("TR-34-106", "Nazlı", 283, scenario="imminent")
    assert twin_imm.telemetry.temp_drop_detected is True
    assert twin_imm.telemetry.temp_drop_c >= 0.5
    assert twin_imm.dystocia_assessment.stage == "STAGE_1_CERVIX_DILATION"
    assert twin_imm.dystocia_assessment.alert_level == "OBSERVE"

    # 3. Dystocia emergency evaluation
    twin_dys = CalvingDystociaEngine.evaluate_cow_calving("TR-34-106", "Nazlı", 283, scenario="dystocia")
    assert twin_dys.dystocia_assessment.alert_level == "CRITICAL_DYSTOCIA_ALARM"
    assert twin_dys.dystocia_assessment.stage_2_duration_minutes > 70
    assert twin_dys.dystocia_assessment.calf_presentation == "POSTERIOR_BREECH"
    assert twin_dys.dystocia_assessment.calving_ease_score == 3
    assert twin_dys.telemetry.tail_tilt_angle_deg > 60.0

    # 4. Simulator scenario trigger & XAI integration
    simulator_engine.trigger_scenario("dystocia", target_animal_id="TR-34-106")
    cow_106 = next(a for a in simulator_engine.animals if a.id == "TR-34-106")
    assert cow_106.calving is not None
    assert cow_106.calving.dystocia_assessment.alert_level == "CRITICAL_DYSTOCIA_ALARM"
    assert cow_106.dss.overall_health_status == "CRITICAL"
    assert cow_106.gate_assignment == "TREATMENT_PEN"
    assert simulator_engine.sorting_gate.status == "ROUTING_TREATMENT"
    assert "Distosi" in simulator_engine.sorting_gate.last_reason

    # 5. Maternity summary & audit report
    state = simulator_engine.get_full_state()
    assert state.maternity is not None
    assert state.maternity.dystocia_emergencies_count >= 1

    report_md = FarmAuditReportGenerator.generate_daily_audit_markdown()
    assert "Doğumhane, Distosi Erken Uyarı" in report_md

    # 6. AI Advisor answering
    resp = AgriTwinAIAdvisor.answer_query("doğumhane durumu ve distosi alarmı var mı?")
    assert resp["category"] == "DYSTOCIA_EMERGENCY"
    assert "DİSTOSİ (GÜÇ DOĞUM) ACİL ALARMI" in resp["answer"]

from genomic_breeding_twin import GenomicBreedingEngine

def test_genomic_breeding_and_inbreeding_twin():
    # 1. Herd genomic summary
    summary = GenomicBreedingEngine.get_herd_genomic_summary()
    assert summary.total_genotyped_cows == 6
    assert summary.avg_herd_net_merit > 650.0
    assert summary.avg_herd_inbreeding_pct < 6.25  # Herd is within safe inbreeding limit
    assert summary.available_catalog_bulls_count >= 4
    assert summary.top_herd_cow_id == "TR-34-102"

    # 2. Lethal Recessive Defect Screening (HCD conflict test)
    # TR-34-104 is HCD carrier. Renegade is also HCD carrier. Mating must be forbidden!
    recs_104 = GenomicBreedingEngine.evaluate_mating_pairs_for_cow("TR-34-104")
    renegade_match = next(r for r in recs_104 if r.bull.bull_id == "US-BULL-RENEGADE")
    assert renegade_match.recessive_conflict is True
    assert renegade_match.inbreeding_status == "FORBIDDEN_RED"
    assert "HCD" in renegade_match.conflict_details

    # Top recommended bull for TR-34-104 must NOT be Renegade
    top_bull_104 = recs_104[0]
    assert top_bull_104.bull.bull_id != "US-BULL-RENEGADE"
    assert top_bull_104.recessive_conflict is False
    assert top_bull_104.progeny_inbreeding_f_pct < 6.25

    # 3. Elite Donor cow strategy (Sexed Female Semen)
    recs_102 = GenomicBreedingEngine.evaluate_mating_pairs_for_cow("TR-34-102")
    top_bull_102 = recs_102[0]
    assert top_bull_102.recommendation_type == "SEXED_FEMALE_SEMEN"
    assert top_bull_102.expected_progeny_net_merit > 850.0

    # 4. Estrus XAI integration in simulator
    simulator_engine.trigger_scenario("estrus", target_animal_id="TR-34-105")
    cow_105 = next(a for a in simulator_engine.animals if a.id == "TR-34-105")
    assert cow_105.dss.estrus_probability >= 0.75
    genomic_xai = next((x for x in cow_105.dss.xai_explanations if "Genomik" in x.metric), None)
    assert genomic_xai is not None
    assert "Önerilen Boğa" in genomic_xai.observed_value

    # 5. Full state & Daily audit report
    state = simulator_engine.get_full_state()
    assert state.genomics is not None
    assert state.genomics.avg_herd_net_merit > 600.0

    report_md = FarmAuditReportGenerator.generate_daily_audit_markdown()
    assert "Genomik Seleksiyon, Pedigri & Akıllı Çiftleştirme" in report_md

    # 6. AI Advisor answering
    resp_cow = AgriTwinAIAdvisor.answer_query("Benekli için hangi boğa öneriliyor ve akrabalık katsayısı nedir?")
    assert resp_cow["category"] == "COW_MATING_RECOMMENDATION"
    assert "DG Captain" in resp_cow["answer"] or "AltaZarek" in resp_cow["answer"]
    assert "Net Merit" in resp_cow["answer"]

    resp_herd = AgriTwinAIAdvisor.answer_query("Sürü genomik ve inbreeding durumu nedir?")
    assert resp_herd["category"] == "HERD_GENOMICS_SUMMARY"
    assert "Net Merit" in resp_herd["answer"]

def test_demo_personas_and_modes():
    """Demo kullanıcı rolleri ve yetkilerinin doğrulanması"""
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)

    res = client.get("/api/demo/personas")
    assert res.status_code == 200
    data = res.json()
    assert "personas" in data
    assert len(data["personas"]) == 4

    roles = [p["id"] for p in data["personas"]]
    assert "vet" in roles
    assert "manager" in roles
    assert "energy" in roles
    assert "genetics" in roles

    switch_res = client.post("/api/demo/switch-persona", json={"persona_id": "manager"})
    assert switch_res.status_code == 200
    assert switch_res.json()["active_persona"] == "manager"

def test_farm_devices_fleet_simulation():
    """Tüm 12 donanım/cihazın fiziksel simülasyonu ve telemetrisi doğrulanır"""
    from farm_devices_twin import farm_devices_engine
    state = simulator_engine.get_full_state()
    assert state.devices is not None
    assert len(state.devices.devices) == 12
    assert state.devices.total_active_devices >= 10
    assert state.devices.total_fleet_power_kw > 0.0

    # Check key devices exist in dictionary
    devices_dict = state.devices.devices
    assert "DEV-AMS-01" in devices_dict
    assert "DEV-JUNO-01" in devices_dict
    assert "DEV-DISCOVERY-01" in devices_dict
    assert "DEV-GATE-01" in devices_dict
    assert "DEV-HVLS-FANS" in devices_dict
    assert "DEV-MISTING-SYS" in devices_dict
    assert "DEV-DIGESTER-01" in devices_dict
    assert "DEV-CHP-GEN" in devices_dict
    assert "DEV-CAM-3D" in devices_dict
    assert "DEV-BOLUS-NET" in devices_dict
    assert "DEV-CALF-FEEDER" in devices_dict
    assert "DEV-EDGE-GATEWAY" in devices_dict

    # Verify device specific metrics
    ams = devices_dict["DEV-AMS-01"]
    assert ams.status in ["RUNNING", "IDLE", "CLEANING"]
    assert "Lazer Pozisyonlama" in ams.key_metrics or "Memelik Lazer Pozisyonu" in ams.key_metrics or len(ams.key_metrics) > 0

    # Test tick updates power and metrics
    fleet = farm_devices_engine.tick_all_devices(ambient_temp_c=28.0, thi_index=79.0, heatwave_active=True)
    assert fleet.total_fleet_power_kw > 0
    assert fleet.devices["DEV-HVLS-FANS"].status == "RUNNING"
    assert "350 RPM" in fleet.devices["DEV-HVLS-FANS"].key_metrics.get("Fan Devri (VFD)", "") or "350 RPM" in fleet.devices["DEV-HVLS-FANS"].operational_mode







