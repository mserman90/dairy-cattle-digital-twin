from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
import math
import random
from pydantic import BaseModel, Field

class SpinePoint(BaseModel):
    x_cm: float = Field(..., description="Omuzdan kuyruk sokumuna omurga mesafesi (cm)")
    z_elevation_cm: float = Field(..., description="Sırt çizgisi dikey kemerleşme / kamburluk yüksekliği (cm)")

class PelvicContourPoint(BaseModel):
    transverse_y_cm: float = Field(..., description="Kalça kemikleri enine ekseni (cm)")
    depth_mm: float = Field(..., description="3D derinlik kamerası z-mesafesi (mm)")

class LamenessAssessment(BaseModel):
    score: float = Field(..., description="Sprecher Topallık Skoru (1.0 - 5.0)")
    back_curvature_index: float = Field(..., description="Sırt Kemerleşme / Kamburluk İndeksi (0.0 - 1.0)")
    head_bob_amplitude_cm: float = Field(..., description="Yürüyüş baş sallama amplitüdü (cm)")
    gait_asymmetry_pct: float = Field(..., description="Adım uzunluğu asimetrisi (%)")
    stride_duration_sec: float = Field(..., description="Adım periyodu (saniye)")
    affected_hoof: Optional[str] = Field(None, description="Şüpheli lezyonlu tırnak (ör. Sol Arka)")
    clinical_interpretation: str

class BCSAssessment(BaseModel):
    score: float = Field(..., description="Vücut Kondisyon Skoru (BCS 1.0 - 5.0)")
    angle_hooks_to_pins_deg: float = Field(..., description="Açlık çukuru ve kalça-iğne kemiği açısı (°)")
    sacral_cavity_depth_mm: float = Field(..., description="Kuyruk sokumu çukur derinliği (mm)")
    short_rib_fat_coverage_mm: float = Field(..., description="Kısa kaburga üzeri yağ kalınlığı (mm)")
    condition_category: str = Field(..., description="OPTIMAL, NEGATIVE_ENERGY_THIN, OVERCONDITIONED_FAT")
    clinical_interpretation: str

class VisionCameraAssessment(BaseModel):
    capture_timestamp: datetime
    camera_id: str = "CAM-EXIT-CHUTE-3D"
    confidence_score: float = Field(0.94, description="YOLO & PointCloud AI Güven Skoru")
    lameness: LamenessAssessment
    bcs: BCSAssessment
    spine_curvature_points: List[SpinePoint] = []
    pelvic_depth_points: List[PelvicContourPoint] = []

class ComputerVisionTwinEngine:
    """
    Sağımhane Çıkış Koridoru 3D Derinlik ve Yürüyüş Kamerası AI Motoru
    (Overhead Time-of-Flight / Stereo Depth Vision Model)
    """

    @staticmethod
    def evaluate_cow_vision(
        animal_id: str,
        bcs_target: float = 3.25,
        is_lame: bool = False,
        lameness_severity: float = 1.0
    ) -> VisionCameraAssessment:
        now = datetime.now()

        # 1. Topallık (Lameness) Simülasyonu & 3D Sırt Profili
        if is_lame:
            lameness_score = min(5.0, max(2.5, lameness_severity))
            curvature_idx = min(0.95, round(0.35 + (lameness_score - 2.0) * 0.18, 2))
            head_bob = round(6.5 + (lameness_score - 1.0) * 3.2, 1)
            asymmetry = round(18.0 + (lameness_score - 1.0) * 12.0, 1)
            stride_sec = round(1.25 + (lameness_score - 1.0) * 0.20, 2)
            affected = "Sol Arka Dış Tırnak (Sole Ulcer / Taban Ülseri)" if lameness_score > 2.5 else "Hafif Adım Asimetrisi"

            if lameness_score >= 4.0:
                interpretation = "Belirgin Topallık (Skor 4). Ağrılı sırt kamburluğu, baş sallama ve tek ayağı belirgin koruma."
            elif lameness_score >= 3.0:
                interpretation = "Orta Topallık (Skor 3). Hem dururken hem yürürken sırt kemerli. Tırnak kesim koridoruna sevk önerilir."
            else:
                interpretation = "Hafif Topallık Başlangıcı (Skor 2). Yürürken hafif sırt eğrilmesi tespit edildi."
        else:
            lameness_score = 1.0
            curvature_idx = 0.08
            head_bob = 2.1
            asymmetry = 3.5
            stride_sec = 1.05
            affected = None
            interpretation = "Normal Yürüyüş (Skor 1). Sırt çizgisi düz, adım uzunlukları simetrik."

        # 3D Sırt çizgisi noktaları (0 cm omuz -> 160 cm sağrı)
        spine_points: List[SpinePoint] = []
        for x in range(0, 161, 20):
            # Normal inekte düz/hafif çukur; topal inekte tepe noktası 80 cm'de olan yukarı dışbükey parabol
            if is_lame:
                # Parabolik kamburluk: z = peak * sin(pi * x / 160)
                arch_height = (lameness_score - 1.0) * 3.8
                z = round(arch_height * math.sin(math.pi * x / 160.0) + random.uniform(-0.3, 0.3), 1)
            else:
                z = round(random.uniform(-0.4, 0.4), 1)
            spine_points.append(SpinePoint(x_cm=float(x), z_elevation_cm=z))

        # 2. Vücut Kondisyon Skoru (BCS) & Pelvik Derinlik Profili
        bcs = round(bcs_target, 2)
        if bcs < 2.75:
            bcs_cat = "NEGATIVE_ENERGY_THIN"
            bcs_interp = "Düşük Kondisyon (<2.75). Belirgin V-şekilli açlık çukuru. Negatif enerji dengesi ve ketozis riski."
            hook_pin_angle = 135.0  # keskin V açısı
            sacral_depth = 48.0     # derin çukur
            rib_fat = 4.2           # ince yağ örtüsü
        elif bcs > 3.75:
            bcs_cat = "OVERCONDITIONED_FAT"
            bcs_interp = "Aşırı Yağlanma (>3.75). Düz/U-şekilli leğen kemiği, karaciğer yağlanması ve buzağılama güçlüğü riski."
            hook_pin_angle = 175.0  # düzleşmiş açı
            sacral_depth = 12.0     # yağla dolmuş çukur
            rib_fat = 24.5          # kalın yağ tabakası
        else:
            bcs_cat = "OPTIMAL"
            bcs_interp = "Optimal Kondisyon (3.00 - 3.25). Sağlıklı U-şekilli kavis, dengeli laktasyon enerji rezervi."
            hook_pin_angle = 155.0
            sacral_depth = 26.0
            rib_fat = 14.0

        # Pelvik enine kesit derinlik noktaları (-40 cm sol kalça -> +40 cm sağ kalça)
        pelvic_points: List[PelvicContourPoint] = []
        for y in range(-40, 41, 10):
            # Derinlik kamerası mesafesi (mm)
            base_dist = 1450.0  # tavandan kalça kemiğine mesafe
            cavity_effect = sacral_depth * math.exp(-((y / 18.0) ** 2))
            measured_depth = round(base_dist + cavity_effect + random.uniform(-2.0, 2.0), 1)
            pelvic_points.append(PelvicContourPoint(
                transverse_y_cm=float(y),
                depth_mm=measured_depth
            ))

        return VisionCameraAssessment(
            capture_timestamp=now,
            confidence_score=0.95,
            lameness=LamenessAssessment(
                score=lameness_score,
                back_curvature_index=curvature_idx,
                head_bob_amplitude_cm=head_bob,
                gait_asymmetry_pct=asymmetry,
                stride_duration_sec=stride_sec,
                affected_hoof=affected,
                clinical_interpretation=interpretation
            ),
            bcs=BCSAssessment(
                score=bcs,
                angle_hooks_to_pins_deg=hook_pin_angle,
                sacral_cavity_depth_mm=sacral_depth,
                short_rib_fat_coverage_mm=rib_fat,
                condition_category=bcs_cat,
                clinical_interpretation=bcs_interp
            ),
            spine_curvature_points=spine_points,
            pelvic_depth_points=pelvic_points
        )
