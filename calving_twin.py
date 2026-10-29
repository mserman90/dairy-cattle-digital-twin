"""
AgriTwin: Doğum, Buzağılama, Distosi Erken Uyarı ve Buzağı Yaşam Döngüsü İkizi
(Calving Prediction, Dystocia Early Warning, Colostrum Brix & Calf Life-Cycle Twin)

Bilimsel & Fizyolojik Modeller:
1. Doğum Öncesi Sıcaklık Kinetiği (Core Body Temperature Drop):
   - Doğuma 24-48 saat kala kanda progesteron (P4) çekilmesi ve PGF2a artışıyla
     vücut iç sıcaklığı 0.5 - 0.9°C düşer (38.6°C -> 37.7 - 37.9°C).
2. Kuyruk Açısı ve İvmeölçer Kasılma Analizi (Tail Tilt & Contraction Accelerometer):
   - Moocall / Dairymaster tipi kuyruk sensörü ile kuyruk kaldırma açısı (0-85°) ve
     saatteki kuyruk kalkma frekansı (>30 kez/saat) ile 1. ve 2. evre doğum sancıları algılanır.
3. Distosi (Güç Doğum) DSS & Calving Ease Scoring (CES 1-5):
   - 2. Evre (aktif ıkınma / fötus çıkışı) süresi >70 dakikayı aştığında veya
     geliş anomalisi (makat, boyun bükülmesi) saptandığında acil veteriner alarmı tetiklenir.
4. Optik Brix Refraktometre & Kolostrum IgG / FPT Riski:
   - Brix >= %22 (>= 50 g/L IgG): Üstün Kalite (Yeşil). Pasif transfer yetmezliği (FPT) riski yok.
   - Brix < %18: Kalitesiz (Kırmızı). Kolostrum Bankasından donmuş yedek kolostrum zorunlu.
   - İlk 2 saatte 4 Litre (%10 vücut ağırlığı) içirilme protokolü.
5. Yeni Doğan Buzağı Dijital İkizi (Calf Twin & APGAR Vigor Score):
   - Vigor skoru (1-10), ilk ayağa kalkma süresi, serum total protein (STP >= 5.5 g/dL)
     ve günlük canlı ağırlık artışı (ADG: 0.85 kg/gün) büyüme projeksiyonu.
"""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime, timedelta
import random
from pydantic import BaseModel, Field

class CalvingSensorTelemetry(BaseModel):
    cow_id: str
    body_temperature_c: float = Field(..., description="Anlık vücut iç sıcaklığı (°C)")
    baseline_temp_c: float = Field(38.6, description="Bireysel normal bazal sıcaklık (°C)")
    temp_drop_c: float = Field(..., description="Sıcaklık düşüş miktarı (baseline - current, °C)")
    temp_drop_detected: bool = Field(..., description=">=0.5°C düşüş var mı? (24-48 saat penceresi)")
    tail_tilt_angle_deg: float = Field(..., description="Kuyruk dikilme açısı (0° - 85°)")
    tail_raising_frequency_per_hr: int = Field(..., description="Saatteki kuyruk kaldırma sayısı (sancı frekansı)")
    rumination_drop_pct: float = Field(..., description="Geviş getirme azalma yüzdesi (%)")
    restlessness_index: float = Field(..., description="Yatıp-kalkma huzursuzluk indeksi (0.0 - 1.0)")
    pelvic_ligament_relaxation: Literal["RIGID", "MODERATE_RELAXATION", "FULL_RELAXATION"] = Field(
        ..., description="Pelvis çatı bağları gevşeme durumu"
    )
    teat_strutting_score: Literal["FLACCID", "MODERATE_FILL", "ENGORGED_LEAKING"] = Field(
        ..., description="Meme dolgunluğu ve kolostrum damlama durumu"
    )

class DystociaRiskAssessment(BaseModel):
    stage: Literal[
        "PRE_CALVING_WINDOW",
        "STAGE_1_CERVIX_DILATION",
        "STAGE_2_ACTIVE_EXPULSION",
        "STAGE_3_PLACENTA",
        "POST_CALVING_STABLE"
    ]
    stage_2_duration_minutes: int = Field(0, description="2. Evre aktif ıkınma süresi (dakika)")
    calf_presentation: Literal["NORMAL_ANTERIOR", "POSTERIOR_BREECH", "HEAD_DEVIATION", "TWIN_ENTANGLED"] = "NORMAL_ANTERIOR"
    calving_ease_score: int = Field(1, description="Doğum Kolaylık Skoru (1=Kolay/Kendi, 2=Hafif Yardım, 3=Mekanik/Distosi, 4=Sezaryen, 5=Fetotomi)")
    dystocia_risk_score: float = Field(0.0, description="Distosi (Güç Doğum) Risk Skoru (0.0 - 1.0)")
    alert_level: Literal["NORMAL", "OBSERVE", "CRITICAL_DYSTOCIA_ALARM"] = "NORMAL"
    estimated_hours_to_calving: Optional[float] = None
    recommended_action: str
    xai_rationale: List[str] = []

class ColostrumBrixAssessment(BaseModel):
    cow_id: str
    colostrum_harvest_liters: float = Field(..., description="İlk sağım kolostrum miktarı (L)")
    brix_refractometer_pct: float = Field(..., description="Dijital Brix Refraktometre Değeri (%)")
    igg_concentration_g_per_l: float = Field(..., description="Hesaplanan İmmünoglobulin G konsantrasyonu (g/L)")
    quality_grade: Literal["EXCELLENT_GREEN", "ADEQUATE_YELLOW", "POOR_RED"]
    fpt_risk: Literal["LOW_PROTECTED", "MODERATE", "HIGH_FAILURE_OF_PASSIVE_TRANSFER"]
    feeding_protocol: str
    colostrum_bank_action: str

class NewbornCalfProfile(BaseModel):
    calf_id: str = Field(..., description="Buzağı kulak küpe no")
    dam_id: str = Field(..., description="Anne kulak küpe no")
    sire_id: str = Field("US-BULL-ALTA-ZAREK", description="Boğa pedigrisi")
    birth_timestamp: datetime
    gender: Literal["FEMALE", "MALE"]
    birth_weight_kg: float = Field(..., description="Doğum canlı ağırlığı (kg)")
    vigor_apgar_score_1_10: int = Field(..., description="APGAR Canlılık / Vigor Skoru (1-10)")
    time_to_stand_minutes: int = Field(..., description="Ayağa kalkma süresi (dakika)")
    suckling_reflex: Literal["STRONG", "MODERATE", "WEAK"]
    colostrum_received_liters: float = Field(4.0, description="İlk 2 saatte içirilen kaliteli kolostrum (L)")
    serum_total_protein_g_dl: float = Field(..., description="Serum Total Protein (Hedef >= 5.5 g/dL)")
    target_adg_kg_day: float = Field(0.85, description="Hedef Günlük Canlı Ağırlık Artışı (kg/gün)")
    current_weight_kg: float
    health_status: Literal["THRIVING", "MONITORING", "CRITICAL"] = "THRIVING"

class CowCalvingTwin(BaseModel):
    cow_id: str
    cow_name: str
    gestation_days: int = Field(282, description="Gebelik Günü (Normal: 279-285 gün)")
    telemetry: CalvingSensorTelemetry
    dystocia_assessment: DystociaRiskAssessment
    colostrum: Optional[ColostrumBrixAssessment] = None
    calf: Optional[NewbornCalfProfile] = None

class FarmMaternitySummary(BaseModel):
    timestamp: datetime
    maternity_pen_capacity: int = 6
    cows_in_maternity_pen: int
    cows_in_24h_calving_window: int
    active_labors_count: int
    dystocia_emergencies_count: int
    colostrum_bank_stock_liters: float = Field(42.5, description="-20°C Dondurulmuş Kaliteli (>22% Brix) Kolostrum Rezervi (L)")
    nursery_calves_count: int
    avg_calf_vigor_score: float
    calving_twins: List[CowCalvingTwin]
    status_summary: str


class CalvingDystociaEngine:
    """
    Doğum, Distosi Erken Uyarı ve Buzağı Yaşam Döngüsü Simülasyon Motoru
    """

    @staticmethod
    def calculate_igg_from_brix(brix_pct: float) -> float:
        """
        Brix % refraktometre değerinden IgG (g/L) hesabı.
        22.0% Brix ~= 50.0 g/L IgG eşiği.
        Empirik Formül: IgG (g/L) = max(10.0, round((brix_pct - 10.0) * 4.167 + 20.0, 1))
        Örnek:
          - %15.0 Brix -> 40.8 g/L
          - %18.0 Brix -> 53.3 g/L
          - %22.0 Brix -> 70.0 g/L
          - %25.0 Brix -> 82.5 g/L
        """
        if brix_pct <= 10.0:
            return 12.0
        igg = (brix_pct - 10.0) * 4.167 + 20.0
        return round(igg, 1)

    @classmethod
    def evaluate_colostrum(cls, cow_id: str, yield_liters: float, brix_pct: float) -> ColostrumBrixAssessment:
        igg = cls.calculate_igg_from_brix(brix_pct)

        if brix_pct >= 22.0:
            grade = "EXCELLENT_GREEN"
            fpt = "LOW_PROTECTED"
            protocol = f"Üstün Kalite ({brix_pct:.1f}% Brix / {igg:.1f} g/L IgG). Doğumdan sonraki ilk 2 saat içinde 4.0 Litre biberonla içiriniz."
            bank = f"Sağılan toplam {yield_liters:.1f} L'nin 4.0 L'si buzağıya verildi; kalan {max(0.0, yield_liters - 4.0):.1f} L yedek porsiyon olarak -20°C Kolostrum Bankasında dondurularak etiketlendi."
        elif brix_pct >= 18.0:
            grade = "ADEQUATE_YELLOW"
            fpt = "MODERATE"
            protocol = f"Orta Kalite ({brix_pct:.1f}% Brix / {igg:.1f} g/L IgG). İlk öğünde 4.0 Litre verilmeli, 6 saat sonra 2.0 Litre takviye edilmelidir."
            bank = "Kalite orta düzeydedir; dondurulmuş kolostrum bankası için saklanmaz, taze tüketilir."
        else:
            grade = "POOR_RED"
            fpt = "HIGH_FAILURE_OF_PASSIVE_TRANSFER"
            protocol = f"Yetersiz / Kalitesiz Kolostrum ({brix_pct:.1f}% Brix / {igg:.1f} g/L IgG). Pasif Bağışıklık Yetmezliği (FPT) riski yüksek! Buzağıya bu kolostrumu VERMEYİNİZ."
            bank = "DİKKAT: -20°C Kolostrum Bankasından >%22 Brix çözdürülmüş 4.0 Litre kaliteli kolostrum derhal temin edilmelidir."

        return ColostrumBrixAssessment(
            cow_id=cow_id,
            colostrum_harvest_liters=yield_liters,
            brix_refractometer_pct=brix_pct,
            igg_concentration_g_per_l=igg,
            quality_grade=grade,
            fpt_risk=fpt,
            feeding_protocol=protocol,
            colostrum_bank_action=bank
        )

    @classmethod
    def evaluate_cow_calving(
        cls,
        cow_id: str,
        cow_name: str,
        gestation_days: int = 282,
        scenario: Optional[str] = None
    ) -> CowCalvingTwin:
        """
        İneğin sensör telemetrisini ve distosi / doğum durumunu simüle eder.
        Senaryolar:
          - 'imminent': Doğum eli kulağında (24-48 saat penceresi, sıcaklık düşüşü, kuyruk hareketi artışı)
          - 'dystocia': Güç doğum acil durumu (2. Evre >70 dk, makat gelişi, acil veteriner alarmı)
          - 'calved': Doğum tamamlanmış, kolostrum ve buzağı ikizi oluşturulmuş
          - None: Normal geç gebelik takibi (stabil)
        """
        baseline_temp = 38.6

        if scenario == "dystocia":
            temp = 37.8
            tail_angle = 78.0
            tail_freq = 46
            rum_drop = 68.0
            restless = 0.94
            pelvic = "FULL_RELAXATION"
            teat = "ENGORGED_LEAKING"
            stage = "STAGE_2_ACTIVE_EXPULSION"
            stage_2_min = 78
            presentation = "POSTERIOR_BREECH"
            ces = 3
            dystocia_risk = 0.94
            alert = "CRITICAL_DYSTOCIA_ALARM"
            act = "🚨 ACİL VETERİNER MÜDAHALESİ GEREKLİ: 2. Evre ıkınma süresi 78 dakikadır ve yavru makat (posterior) geliş pozisyonundadır! Doğum krikosu veya veteriner çekimi başlatınız."
            xai = [
                "2. Evre aktif ıkınma süresi kritik sınır olan 70 dakikayı aşmıştır (78 dk).",
                "Kuyruk açısı 78° ve sancı frekansı 46 kez/saat ile şiddetli myometriyum kasılması devam etmektedir.",
                "Ultrasonik/palpasyon telemetrisi fetusun ters (makat) geliş pozisyonunda olduğunu doğrulamıştır.",
                "Anne yorgunluğu ve yavru anoksi riski nedeniyle acil obstetrik müdahale şarttır."
            ]
            colostrum = None
            calf = None

        elif scenario == "imminent":
            temp = 37.85
            tail_angle = 48.0
            tail_freq = 28
            rum_drop = 48.0
            restless = 0.78
            pelvic = "FULL_RELAXATION"
            teat = "ENGORGED_LEAKING"
            stage = "STAGE_1_CERVIX_DILATION"
            stage_2_min = 0
            presentation = "NORMAL_ANTERIOR"
            ces = 1
            dystocia_risk = 0.15
            alert = "OBSERVE"
            act = "👀 DOĞUM ELİ KULAĞINDA (6-18 SAAT): İneği doğumhane temiz altlıklı bireysel doğum bölmesine alınız. Kamera gözetimini başlatınız."
            xai = [
                f"Vücut sıcaklığında -{baseline_temp - temp:.2f}°C belirgin düşüş tespit edildi (Progesteron P4 çekilme fazı).",
                f"Kuyruk kalkma frekansı saatte {tail_freq} adede yükselmiş olup 1. evre servikal dilatasyon sancıları başlamıştır.",
                "Geviş getirme süresi %48 azalmış ve huzursuzluk indeksi 0.78'e çıkmıştır.",
                "Pelvis bağları tam gevşemiş ve meme kolostrum ile dolup damlamaya başlamıştır."
            ]
            colostrum = None
            calf = None

        elif scenario == "calved":
            temp = 38.4
            tail_angle = 12.0
            tail_freq = 3
            rum_drop = 15.0
            restless = 0.20
            pelvic = "MODERATE_RELAXATION"
            teat = "MODERATE_FILL"
            stage = "POST_CALVING_STABLE"
            stage_2_min = 38
            presentation = "NORMAL_ANTERIOR"
            ces = 1
            dystocia_risk = 0.05
            alert = "NORMAL"
            act = "✅ DOĞUM BAŞARIYLA TAMAMLANDI: Kolostrum sağılmış ve buzağıya içirilmiştir. İnek ve buzağı vital parametreleri stabildir."
            xai = [
                "Doğum 38 dakikalık normal 2. evre ıkınma ile komplikasyonsuz gerçekleşmiştir (CES 1).",
                "Kolostrum optik refraktometre Brix skoru %24.5 ile üstün kalitedir (78.0 g/L IgG).",
                "Buzağı ilk 45 dakikada ayağa kalkmış ve APGAR Vigor skoru 9/10 ölçülmüştür."
            ]
            colostrum = cls.evaluate_colostrum(cow_id=cow_id, yield_liters=6.8, brix_pct=24.5)
            calf = NewbornCalfProfile(
                calf_id=f"TR-06-CALF-{cow_id.split('-')[-1]}",
                dam_id=cow_id,
                sire_id="US-BULL-ALTA-ZAREK",
                birth_timestamp=datetime.now() - timedelta(hours=3),
                gender="FEMALE",
                birth_weight_kg=42.0,
                vigor_apgar_score_1_10=9,
                time_to_stand_minutes=42,
                suckling_reflex="STRONG",
                colostrum_received_liters=4.0,
                serum_total_protein_g_dl=6.2,
                target_adg_kg_day=0.88,
                current_weight_kg=42.0,
                health_status="THRIVING"
            )

        else:
            # Standart geç kuru dönem / stabil takip
            temp = 38.55
            tail_angle = 8.0
            tail_freq = 3
            rum_drop = 5.0
            restless = 0.12
            pelvic = "RIGID"
            teat = "MODERATE_FILL"
            stage = "PRE_CALVING_WINDOW"
            stage_2_min = 0
            presentation = "NORMAL_ANTERIOR"
            ces = 1
            dystocia_risk = 0.04
            alert = "NORMAL"
            act = "Stabil geç gebelik takibi devam ediyor. Tahmini doğuma 3-5 gün vardır."
            xai = [
                f"Vücut sıcaklığı {temp:.2f}°C ile bazal düzeydedir (henüz progesteron düşüşü başlamamıştır).",
                "Kuyruk açısı ve aktivite normal dinlenme normlarındadır.",
                "Pelvis çatı bağları henüz sert ve gergindir."
            ]
            colostrum = None
            calf = None

        temp_delta = round(baseline_temp - temp, 2)
        drop_detected = temp_delta >= 0.50

        telemetry = CalvingSensorTelemetry(
            cow_id=cow_id,
            body_temperature_c=temp,
            baseline_temp_c=baseline_temp,
            temp_drop_c=temp_delta,
            temp_drop_detected=drop_detected,
            tail_tilt_angle_deg=tail_angle,
            tail_raising_frequency_per_hr=tail_freq,
            rumination_drop_pct=rum_drop,
            restlessness_index=restless,
            pelvic_ligament_relaxation=pelvic,
            teat_strutting_score=teat
        )

        dystocia_assessment = DystociaRiskAssessment(
            stage=stage,
            stage_2_duration_minutes=stage_2_min,
            calf_presentation=presentation,
            calving_ease_score=ces,
            dystocia_risk_score=dystocia_risk,
            alert_level=alert,
            estimated_hours_to_calving=6.0 if scenario == "imminent" else (0.0 if scenario in ["dystocia", "calved"] else 72.0),
            recommended_action=act,
            xai_rationale=xai
        )

        return CowCalvingTwin(
            cow_id=cow_id,
            cow_name=cow_name,
            gestation_days=gestation_days,
            telemetry=telemetry,
            dystocia_assessment=dystocia_assessment,
            colostrum=colostrum,
            calf=calf
        )

    @classmethod
    def get_farm_maternity_summary(cls, active_scenario: Optional[str] = None) -> FarmMaternitySummary:
        """
        Çiftliğin doğumhane ve buzağıhane genel dijital ikiz durumunu üretir.
        """
        # Sürüdeki temsili gebe ve taze inekler
        cows_data = [
            {"id": "TR-34-106", "name": "Nazlı", "gestation": 283, "scen": active_scenario if active_scenario in ["dystocia", "calving_imminent", "colostrum_brix"] else "imminent"},
            {"id": "TR-34-104", "name": "Yıldız", "gestation": 279, "scen": None},
            {"id": "TR-34-102", "name": "Benekli", "gestation": 284, "scen": "calved"}
        ]

        twins: List[CowCalvingTwin] = []
        for c in cows_data:
            s = c["scen"]
            if s == "calving_imminent":
                s = "imminent"
            elif s == "dystocia":
                s = "dystocia"
            elif s == "colostrum_brix":
                s = "calved"
            t = cls.evaluate_cow_calving(
                cow_id=c["id"],
                cow_name=c["name"],
                gestation_days=c["gestation"],
                scenario=s
            )
            twins.append(t)

        cows_in_24h = sum(1 for t in twins if t.telemetry.temp_drop_detected or t.dystocia_assessment.stage != "PRE_CALVING_WINDOW")
        active_labors = sum(1 for t in twins if t.dystocia_assessment.stage in ["STAGE_1_CERVIX_DILATION", "STAGE_2_ACTIVE_EXPULSION"])
        dystocias = sum(1 for t in twins if t.dystocia_assessment.alert_level == "CRITICAL_DYSTOCIA_ALARM")
        calves_count = sum(1 for t in twins if t.calf is not None) + 4  # +4 buzağıhanedeki diğer buzağılar
        avg_vigor = round(
            sum((t.calf.vigor_apgar_score_1_10 if t.calf else 8.5) for t in twins) / max(1, len(twins)), 1
        )

        if dystocias > 0:
            summary = "🚨 KRİTİK ALARM: Doğumhanede acil müdahale gerektiren distosi (güç doğum) vakası tespit edildi!"
        elif active_labors > 0:
            summary = "⚠️ AKTİF DOĞUM SANCI TAKİBİ: Doğumhanede sancı çeken inekler gözlem altında."
        else:
            summary = "✅ DOĞUMHANE & BUZAĞIHANE STABİL: Tüm doğum ve buzağı vital parametreleri normaller dahilinde."

        return FarmMaternitySummary(
            timestamp=datetime.now(),
            maternity_pen_capacity=6,
            cows_in_maternity_pen=len(twins),
            cows_in_24h_calving_window=cows_in_24h,
            active_labors_count=active_labors,
            dystocia_emergencies_count=dystocias,
            colostrum_bank_stock_liters=42.5,
            nursery_calves_count=calves_count,
            avg_calf_vigor_score=avg_vigor,
            calving_twins=twins,
            status_summary=summary
        )

# Global Singleton Engine Instance
calving_engine = CalvingDystociaEngine()
