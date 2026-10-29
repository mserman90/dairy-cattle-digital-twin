import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
from simulator import simulator_engine
from models import FarmTwinState
from physiological_models import RationComposition
from icar_ade import ICARADEAdapter
from edge_gateway import edge_gateway
from report_generator import FarmAuditReportGenerator
from ai_advisor import AgriTwinAIAdvisor
from spatial_rtls import rtls_engine
from ration_optimizer import TMRRationOptimizer
from calving_twin import CalvingDystociaEngine
from genomic_breeding_twin import GenomicBreedingEngine

class AssistantQueryRequest(BaseModel):
    query: str

class ApplyRationRequest(BaseModel):
    strategy_id: str

class SwitchPersonaRequest(BaseModel):
    persona_id: str = "vet"

class PrescribeRequest(BaseModel):
    animal_id: str
    drug: str = "Sefalosporin İntramammar"
    withdrawal_days: int = 5

app = FastAPI(
    title="AgriTwin - Süt Sığırcılığı Dijital İkizi API (Faz 2 & 3)",
    description="ICAR ADE uyumlu telemetri, inSiliCow & RuFaS Fizyolojik Simülasyon, Wood Laktasyon Modeli ve IPCC Tier 2 Metan Hesaplama",
    version="2.0.0"
)

# Models for requests
class ScenarioRequest(BaseModel):
    scenario: str
    animal_id: Optional[str] = None

class GateOverrideRequest(BaseModel):
    status: str

class HvacOverrideRequest(BaseModel):
    zone_id: str
    fan_active: bool
    misting_active: bool

@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")

@app.get("/api/state", response_model=FarmTwinState)
def get_state():
    return simulator_engine.get_full_state()

@app.post("/api/simulate/tick")
def advance_tick():
    simulator_engine.tick()
    return {"message": "Tick advanced successfully", "tick": simulator_engine.simulation_tick}

@app.post("/api/simulate/scenario")
def trigger_scenario(req: ScenarioRequest):
    valid_scenarios = [
        "heatwave", "mastitis", "estrus", "ration_optimize", "lameness", "sara",
        "dystocia", "calving_imminent", "colostrum_brix", "reset"
    ]
    if req.scenario not in valid_scenarios:
        raise HTTPException(status_code=400, detail=f"Invalid scenario. Allowed: {valid_scenarios}")
    simulator_engine.trigger_scenario(req.scenario, req.animal_id)
    return {"message": f"Scenario '{req.scenario}' triggered", "active_scenario": simulator_engine.active_scenario}

@app.post("/api/gate/override")
def gate_override(req: GateOverrideRequest):
    simulator_engine.manual_gate_override(req.status)
    return {"message": f"Gate status set to {req.status}", "gate": simulator_engine.sorting_gate}

@app.post("/api/zone/hvac")
def hvac_override(req: HvacOverrideRequest):
    zone = next((z for z in simulator_engine.zones if z.zone_id == req.zone_id), None)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    zone.ventilation_fans_active = req.fan_active
    zone.misting_active = req.misting_active
    return {"message": f"HVAC updated for {req.zone_id}", "zone": zone}

@app.get("/api/export/icar-ade")
def export_icar_ade():
    """Hayvanların anlık telemetri ve sağlık olaylarını ICAR ADE v2 formatında JSON olarak dışa aktarır"""
    ade_json = ICARADEAdapter.export_to_icar_ade(simulator_engine.animals)
    return JSONResponse(
        content=ade_json,
        headers={"Content-Disposition": "attachment; filename=ICAR_ADE_DairyTwin_Export.json"}
    )

@app.get("/api/animal/{animal_id}/wood-curve")
def get_animal_wood_curve(animal_id: str):
    animal = next((a for a in simulator_engine.animals if a.id == animal_id), None)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    return {
        "animal_id": animal.id,
        "name": animal.name,
        "lactation_number": animal.lactation_number,
        "days_in_milk": animal.days_in_milk,
        "actual_yield": animal.latest_milking.yield_kg * 2.0,
        "wood_params": animal.physiology.wood_params,
        "peak_dim": animal.physiology.peak_dim,
        "peak_yield": animal.physiology.peak_yield,
        "curve_points": animal.lactation_curve
    }

@app.post("/api/ration/update")
def update_ration(ration: RationComposition):
    simulator_engine.current_ration = ration
    for a in simulator_engine.animals:
        simulator_engine.tick()
    return {
        "message": "Ration updated and herd physiology recalculated",
        "sustainability": simulator_engine.get_sustainability_kpis(),
        "ration": simulator_engine.current_ration
    }

@app.post("/api/edge/toggle-connection")
def toggle_edge_connection():
    st = edge_gateway.toggle_connection()
    return {"message": f"Edge connection is now {'ONLINE' if st.is_online else 'OFFLINE (Buffer Mode)'}", "edge": st}

@app.post("/api/veterinary/prescribe")
def prescribe_treatment(req: PrescribeRequest):
    treatment = edge_gateway.add_treatment(req.animal_id, req.drug, req.withdrawal_days)
    return {
        "message": f"{req.animal_id} için tedavi reçetesi işlendi. Süt tankı kilidi ve atık süt tahliyesi devreye alındı.",
        "treatment": treatment
    }

@app.get("/api/report/daily")
def get_daily_audit_report():
    """Veteriner ve çiftlik müdürleri için günlük kapsamlı denetim raporunu Markdown formatında sunar"""
    report_md = FarmAuditReportGenerator.generate_daily_audit_markdown()
    return {"format": "markdown", "report": report_md}

@app.post("/api/assistant/ask")
def ask_ai_assistant(req: AssistantQueryRequest):
    """Doğal dilde çiftlik ve veterinerlik sorularına dijital ikiz üzerinden yanıt verir"""
    return AgriTwinAIAdvisor.answer_query(req.query)

@app.get("/api/spatial/grid")
def get_spatial_grid():
    """Barınak mikroklima ızgarası (8x5) ve ineklerin RTLS (x,y) koordinatlarını döner"""
    zone_a = next((z for z in simulator_engine.zones if z.zone_id == "ZONE-A"), simulator_engine.zones[0])
    zone_b = next((z for z in simulator_engine.zones if z.zone_id == "ZONE-B"), simulator_engine.zones[1])
    fans_on = zone_a.ventilation_fans_active or zone_b.ventilation_fans_active
    is_heat = zone_a.thi_index >= 72 or zone_b.thi_index >= 72

    cells = rtls_engine.compute_grid(
        base_temp_a=zone_a.temperature_c,
        base_temp_b=zone_b.temperature_c,
        rh_pct=zone_a.relative_humidity_pct,
        fans_active=fans_on
    )
    positions = rtls_engine.update_animal_positions(
        animals=simulator_engine.animals,
        heat_stress_active=is_heat,
        fans_active=fans_on
    )
    return {
        "width_m": rtls_engine.width_m,
        "height_m": rtls_engine.height_m,
        "cells": cells,
        "positions": positions,
        "fans": rtls_engine.fan_locations
    }

@app.get("/api/ration/optimize")
def get_ration_optimization():
    """Çok amaçlı TMR rasyon formülasyonu ve Pareto frontier analiz raporunu sunar"""
    return TMRRationOptimizer.generate_optimization_plans(
        active_strategy_id=simulator_engine.active_ration_strategy
    )

@app.post("/api/ration/apply")
def apply_ration_strategy(req: ApplyRationRequest):
    """Seçilen rasyon optimizasyon stratejisini sürüye uygular"""
    result = simulator_engine.apply_ration_strategy(req.strategy_id)
    return {
        "message": f"Rasyon stratejisi '{req.strategy_id}' sürüye başarıyla uygulandı.",
        "result": result
    }

@app.get("/api/energy/biogas")
def get_biogas_energy_status():
    """Çiftlik atık, biyogaz anaerobik çürütücü ve kojenerasyon elektrik üretim ikizi raporu"""
    state = simulator_engine.get_full_state()
    return state.energy

class RobotCommandRequest(BaseModel):
    robot_id: str
    command: str = "START_MISSION"

@app.get("/api/robotics/fleet")
def get_robotics_fleet():
    """Ahır içi otonom yem itici ve gübre vakum robot filosu ikizi telemetrisi"""
    state = simulator_engine.get_full_state()
    return state.robotics

@app.post("/api/robotics/command")
def send_robot_command(req: RobotCommandRequest):
    """Otonom ahır robotuna görev talimatı gönderir"""
    return {
        "status": "COMMAND_DISPATCHED",
        "robot_id": req.robot_id,
        "command": req.command,
        "message": f"{req.robot_id} için '{req.command}' talimatı otonom navigasyona iletildi."
    }

class ColostrumEvaluateRequest(BaseModel):
    cow_id: str = "TR-34-106"
    yield_liters: float = 6.5
    brix_pct: float = 24.5

@app.get("/api/calving/summary")
def get_calving_maternity_summary():
    """Doğumhane, doğum tahmini, distosi alarmı ve buzağıhane genel durumu"""
    state = simulator_engine.get_full_state()
    return state.maternity

@app.post("/api/calving/colostrum")
def evaluate_colostrum_sample(req: ColostrumEvaluateRequest):
    """Optik Brix refraktometre kolostrum kalite analizi ve FPT bağışıklık değerlendirmesi"""
    return CalvingDystociaEngine.evaluate_colostrum(
        cow_id=req.cow_id,
        yield_liters=req.yield_liters,
        brix_pct=req.brix_pct
    )

@app.get("/api/calving/{animal_id}/telemetry")
def get_cow_calving_telemetry(animal_id: str):
    """Spesifik bir ineğin doğum sancısı, vücut ısısı ve distosi ikiz profili"""
    animal = next((a for a in simulator_engine.animals if a.id == animal_id), None)
    if not animal:
        raise HTTPException(status_code=404, detail="İnek bulunamadı")
    if animal.calving:
        return animal.calving
    return CalvingDystociaEngine.evaluate_cow_calving(
        cow_id=animal.id,
        cow_name=animal.name,
        gestation_days=282,
        scenario=None
    )

@app.get("/api/genomics/summary")
def get_genomics_summary():
    """Sürü genel genomik damızlık değeri (gEBV / NM$), inbreeding ve eşleştirme özeti"""
    state = simulator_engine.get_full_state()
    return state.genomics

@app.get("/api/genomics/bulls")
def get_ai_bull_catalog():
    """Elit yapay tohumlama boğa kataloğu (gEBV, TPI, fiyat, resesif taşıyıcılık)"""
    return GenomicBreedingEngine.BULL_CATALOG

@app.get("/api/genomics/mating/{cow_id}")
def get_mating_recommendations_for_cow(cow_id: str):
    """Belirli bir inek için akrabalık ve genetik kısıtları denetleyerek sıralanmış boğa önerileri"""
    return GenomicBreedingEngine.evaluate_mating_pairs_for_cow(cow_id)

@app.get("/api/demo/personas")
def get_demo_personas():
    """Demo kullanıcı profillerini ve yetkilerini döner"""
    return {
        "active_persona": "vet",
        "personas": [
            {
                "id": "vet",
                "name": "Dr. Mehmet Yılmaz",
                "role": "Baş Veteriner Hekim & Sürü Danışmanı",
                "avatar": "🩺",
                "department": "Sürü Sağlığı & Biyogüvenlik",
                "permissions": ["Reçete Yazma", "Karantina Kilidi", "Doğum & Distosi Müdahalesi", "Brix Kolostrum Onayı"]
            },
            {
                "id": "manager",
                "name": "Selim Aksoy",
                "role": "Çiftlik Yöneticisi & Zooteknist",
                "avatar": "🚜",
                "department": "Operasyon & TMR Rasyon Yönetimi",
                "permissions": ["Pareto Rasyon Uygulama", "Robot Filo Kontrolü", "Ayırma Kapısı Yönlendirme", "Finansal ROI"]
            },
            {
                "id": "energy",
                "name": "Müh. Emre Demir",
                "role": "Biyogaz & Yenilenebilir Enerji Mühendisi",
                "avatar": "⚡",
                "department": "Döngüsel Ekonomi & Kojenerasyon (CHP)",
                "permissions": ["CHP Jeneratör Ayarı", "Biyogaz Basınç İzleme", "Şebeke Elektrik Satışı", "Karbon Kredisi"]
            },
            {
                "id": "genetics",
                "name": "Selin Kaya",
                "role": "Genetik Islah & Suni Tohumlama Danışmanı",
                "avatar": "🧬",
                "department": "Genomik Damızlık & Akıllı Çiftleştirme",
                "permissions": ["Net Merit ($NM$) Seleksiyonu", "Akrabalık (Inbreeding) Denetimi", "Dişi Ayrıştırılmış Boğa Kataloğu"]
            }
        ]
    }

@app.post("/api/demo/switch-persona")
def switch_demo_persona(req: SwitchPersonaRequest):
    """Aktif demo kullanıcısını değiştirir"""
    persona_id = req.persona_id
    return {"status": "success", "active_persona": persona_id}

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
