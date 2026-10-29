"""
AgriTwin: Kapsamlı Çiftlik Cihazları & IoT Donanım Filosu İkizi
(Comprehensive Farm Devices & IoT Hardware Fleet Digital Twin)

Simüle Edilen 12 Endüstriyel & Biyolojik Cihaz:
1. Robotik Sağım İstasyonu (AMS - DeLaval VMS / Lely Astronaut):
   - 4 bağımsız çeyrek süt sayacı, hat içi spektrometre, pnömatik süt yönlendirme vanaları (Ana Tank / Atık Hattı),
   - 95°C buhar sterilizasyon döngüsü, otomatik post-dip meme dezenfektan püskürtücü, pelet konsantre yem dozajlayıcı.
2. Otonom Yem İtici Robot (Lely Juno X):
   - 85 RPM helezon döner etek, ultrasonik yem yığını profil sensörü (12-20 cm), Lityum-iyon batarya yönetimi,
   - Şarj istasyonu doklanması, engel algılama ultrasonik radarı (Obstacle avoidance).
3. Otonom Gübre Vakum Robotu (Lely Discovery Vac):
   - 350 L vakum tankı, ön yumuşatma su nozulları, diyaframlı vakum pompası,
   - Biyogaz transfer çukuruna otonom yanaşma ve hidrolik deşarj kapağı döngüsü.
4. Akıllı Otomatik Ayırma Kapısı (Pneumatic Smart Sorting Gate):
   - 3 yollu yönlendirme pistonu (Paddock A Barınak / Revir Tedavi / Tohumlama Padoku),
   - RFID anteni, optik fotosel geçiş sensörleri, sıkışma önleyici güvenlik zamanlayıcısı.
5. İntraruminal Kablosuz Bolus Sensör Ağı (Reticulum Bolus Network):
   - İyon-seçici pH elektrodu (SARA tespiti), yüksek hassasiyetli retikulum termometresi (su içme düşüşü & ateş),
   - 3 eksenli retikülorumen motilite ivmeölçeri (1.8 - 2.2 kasılma/dk), 433 MHz RF iletim döngüsü.
6. 3D Computer Vision Derinlik Kameraları (RGB-D Chute Cameras):
   - 30 FPS kızılötesi derinlik taraması, sırt kemerleşme açısı (Lameness Sprecher skalası),
   - Pelvik çukur ve kalça açısı analizi (Ferguson BCS), lens kirlilik dedektörü.
7. Değişken Hızlı HVLS Tavan Fanları (HVAC VFD Fans):
   - 4 bölge (Zone A, B, C, D) 7.3m çaplı kanatlar, THI endeksine bağlı frekans invertör devri (0 - 350 RPM),
   - Hava sirkülasyon hızı (0.2 - 2.8 m/s).
8. Yüksek Basınçlı Evaporatif Sisleme Pompası & Nozulları (Misting System):
   - 70 bar paslanmaz çelik pompa, 30 sn sisleme / 4.5 dk bekleme periyodik zamanlayıcısı,
   - Evaporatif soğutma ile hava sıcaklığını 3-5°C düşürme, nozul tıkanıklık basınç sensörü.
9. Biyogaz Anaerobik Çürütme Reaktörü & Karıştırıcı Motoru (CSTR Digester):
   - 38.5°C ceketli ısıtma sirkülasyon pompası, 45 RPM mekanik paletli karıştırıcı,
   - Biyogaz üretim debimetresi (m³/saat), emniyet aşırı basınç alevleme meşalesi (Flare valve).
10. Kojenerasyon (CHP) Gaz Motoru & Şebeke İnvertörü:
    - 1500 RPM senkron gazlı içten yanmalı motor, 38 kW elektriksel alternatör (50.0 Hz),
    - 50 kW termal sıcak su ceketi eşanjörü (85°C), yağ basıncı (4.2 bar).
11. Otomatik Buzağı Kolostrum İstasyonu & Dijital Brix Refraktometresi:
    - Optik Brix refraktometre sensörü (%0-32 Brix ⇔ IgG g/L),
    - 60°C 60 dk parti pastörizatörü, 38.5°C porsiyonlama peristaltik pompası.
12. Endüstriyel Uç Bilişim Ağ Geçidi (Industrial Edge Computing Gateway PLC/RTU):
    - Modbus TCP/RTU, OPC UA, MQTT telemetri brokerı, 15ms mikro-karar döngüsü,
    - Kırsal kesinti 72 saat çevrimdışı paket tampon belleği.
"""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
import math
import random
from pydantic import BaseModel, Field

class DeviceTelemetryItem(BaseModel):
    device_id: str
    name: str
    category: Literal["MILKING", "ROBOTICS", "SENSORS", "HVAC", "ENERGY", "CALVING", "EDGE"]
    status: Literal["RUNNING", "IDLE", "CHARGING", "ALERT", "MAINTENANCE", "DISCHARGING"]
    power_draw_kw: float
    health_pct: float
    key_metrics: Dict[str, Any]
    operational_mode: str
    last_action: str
    academic_key: str

class FarmDevicesFleetProfile(BaseModel):
    timestamp: datetime
    total_active_devices: int
    total_fleet_power_kw: float
    fleet_health_index_pct: float
    devices: Dict[str, DeviceTelemetryItem]
    status_summary: str

class FarmDevicesEngine:
    """
    Çiftlikteki Tüm Cihazların Gerçekçi Fizik & Operasyonel Simülasyon Motoru
    """

    def __init__(self):
        self.tick_count = 0
        self.fan_rpm = 0
        self.misting_active = False
        self.juno_x = 18.5
        self.juno_dir = 1.0
        self.juno_battery = 88.0
        self.feed_height_cm = 18.5
        self.discovery_tank = 42.0
        self.discovery_battery = 76.0
        self.discovery_x = 14.0
        self.discovery_y = 8.0
        self.discovery_dir_x = 1.0
        self.discovery_dir_y = 0.5
        self.gate_state = "IDLE"
        self.gate_angle_deg = 0.0
        self.last_gate_divert_id: Optional[str] = None
        self.digester_temp = 38.5
        self.chp_rpm = 1500
        self.chp_power_kw = 35.2
        self.brix_val = 23.8

    def tick_all_devices(
        self,
        ambient_temp_c: float = 23.5,
        ambient_rh_pct: float = 55.0,
        thi_index: float = 70.5,
        treated_cows_count: int = 0,
        active_critical_cows: int = 0,
        heatwave_active: bool = False
    ) -> FarmDevicesFleetProfile:
        self.tick_count += 1
        now = datetime.now()

        # -------------------------------------------------------------
        # 1. HAVALANDIRMA (HVLS TAVAN FANLARI) & SİSLEME FİZİĞİ
        # -------------------------------------------------------------
        if heatwave_active or thi_index >= 78.0:
            self.fan_rpm = 350
            fan_mode = "Maksimum Soğutma (350 RPM - VFD Tam Yük)"
            fan_power = 6.4
            self.misting_active = (self.tick_count % 3 == 0)  # 30 sn açık, bekleme
            misting_mode = "Periyodik Sisleme Aktif (70 Bar Evaporatif Puf)" if self.misting_active else "Sisleme Bekleme Döngüsü"
            misting_power = 2.2 if self.misting_active else 0.1
        elif thi_index >= 72.0:
            self.fan_rpm = 220
            fan_mode = "Orta Hız Sirkülasyon (220 RPM - VFD)"
            fan_power = 3.6
            self.misting_active = False
            misting_mode = "Beklemede (Eşik Altı)"
            misting_power = 0.0
        else:
            self.fan_rpm = 80 if ambient_temp_c > 21.0 else 0
            fan_mode = "Düşük Hız Havalandırma (80 RPM)" if self.fan_rpm > 0 else "Termonötral Bekleme (0 RPM)"
            fan_power = 0.8 if self.fan_rpm > 0 else 0.05
            self.misting_active = False
            misting_mode = "Kapalı"
            misting_power = 0.0

        # -------------------------------------------------------------
        # 2. OTONOM YEM İTİCİ (LELY JUNO X) FİZİĞİ
        # -------------------------------------------------------------
        is_juno_charging = False
        if self.juno_battery <= 20.0:
            juno_status = "CHARGING"
            is_juno_charging = True
            juno_mode = "İndüksiyonlu Şarj İstasyonunda Doluyor"
            juno_power = 0.85
            self.juno_battery = min(98.0, self.juno_battery + 2.5)
            self.juno_x = 2.0
            juno_speed = 0.0
            auger_rpm = 0
            juno_action = "Batarya şarjı tamamlanıyor (Dock x=2.0m)"
        else:
            juno_status = "RUNNING"
            juno_speed = 0.25
            auger_rpm = 85
            juno_power = 0.45
            self.juno_battery = max(15.0, self.juno_battery - 0.2)
            self.juno_x += self.juno_dir * 1.5
            if self.juno_x >= 35.5:
                self.juno_dir = -1.0
            elif self.juno_x <= 4.5:
                self.juno_dir = 1.0

            # Yem yüksekliği dinamik: Juno geçtiğinde 18.5 cm'ye yükselir
            self.feed_height_cm = round(17.5 + (math.sin(self.tick_count * 0.3) * 1.8), 1)
            juno_mode = f"Yem İtme Devriyesi ({auger_rpm} RPM Helezon)"
            juno_action = f"Orta yem yolu taranıyor (x: {self.juno_x:.1f}m, Yem: {self.feed_height_cm}cm)"

        # -------------------------------------------------------------
        # 3. OTONOM GÜBRE VAKUM ROBOTU (LELY DISCOVERY VAC) FİZİĞİ
        # -------------------------------------------------------------
        if self.discovery_tank >= 85.0:
            disc_status = "DISCHARGING"
            disc_mode = "Biyogaz Transfer Çukuruna Deşarj Ediyor"
            disc_power = 1.1
            self.discovery_x = 38.0
            self.discovery_y = 2.5
            self.discovery_tank = 8.0  # Boşaltıldı
            disc_action = "350 L gübre biyogaz reaktörüne basıldı, vana kapandı."
        elif self.discovery_battery <= 20.0:
            disc_status = "CHARGING"
            disc_mode = "Şarj İstasyonunda Doluyor"
            disc_power = 0.95
            self.discovery_battery = min(96.0, self.discovery_battery + 2.2)
            disc_action = "Li-ion batarya şarj ediliyor (Dock x=38.0m, y=2.5m)"
        else:
            disc_status = "RUNNING"
            disc_power = 0.65
            self.discovery_battery = max(18.0, self.discovery_battery - 0.25)
            self.discovery_x += self.discovery_dir_x * 1.4
            self.discovery_y += self.discovery_dir_y * 0.9
            if self.discovery_x >= 36.0 or self.discovery_x <= 4.0:
                self.discovery_dir_x *= -1.0
            if self.discovery_y >= 22.0 or self.discovery_y <= 4.0:
                self.discovery_dir_y *= -1.0
            self.discovery_tank = min(100.0, self.discovery_tank + 1.2)
            disc_mode = "Zemin Vakumlama & Ön Su Püskürtme"
            disc_action = f"Koridorda vakum devriyesi (Tank: %{self.discovery_tank:.0f})"

        # -------------------------------------------------------------
        # 4. AKILLI OTOMATİK AYIRMA KAPISI (SMART SORTING GATE)
        # -------------------------------------------------------------
        if active_critical_cows > 0:
            self.gate_state = "ROUTING_TREATMENT"
            self.gate_angle_deg = 45.0
            gate_mode = "Pnömatik Piston AÇIK: Revir Tüneline Yönlendirme"
            gate_action = "🚨 Kritik vaka tespit edildi; kapı kanadı revire açıldı."
        else:
            self.gate_state = "IDLE"
            self.gate_angle_deg = 0.0
            gate_mode = "Normal Akış: Ana Barınak Dönüş Kapısı"
            gate_action = "Tüm inekler serbest dinlenme padokuna yönlendiriliyor."

        # -------------------------------------------------------------
        # 5. ROBOTİK SAĞIM SİSTEMİ (AMS VMS / ASTRONAUT)
        # -------------------------------------------------------------
        is_valve_locked = (treated_cows_count > 0)
        ams_power = 2.45
        ams_mode = "🔒 İlaç Arınma Kilidi Aktif (Atık Süt Tahliyesi)" if is_valve_locked else "Birinci Sınıf Ana Süt Tankı Kabul Modu"
        ams_action = (
            "Antibiyotikli inek sağıldı; süt vanası atık hattına kilitlendi."
            if is_valve_locked
            else "4 lob bağımsız spektrometre ve optik süt sayaçları nominal."
        )

        # -------------------------------------------------------------
        # 6. BİYOGAZ ANAEROBİK ÇÜRÜTÜCÜ & CHP KOJENERASYON MOTORU
        # -------------------------------------------------------------
        self.digester_temp = round(38.5 + (math.sin(self.tick_count * 0.15) * 0.2), 1)
        biogas_flow_m3_h = round(8.8 + (self.discovery_tank * 0.02), 1)  # Gübreyle dinamik
        chp_power = round(35.0 + random.uniform(-0.8, 0.8), 1)
        chp_thermal_kw = round(chp_power * 1.35, 1)

        # -------------------------------------------------------------
        # 7. TELEMETRİK BOLUS & 3D DERİNLİK KAMERASI & BUZAĞI İSTASYONU
        # -------------------------------------------------------------
        bolus_transmissions = 6 * (self.tick_count % 4 + 1)
        cam_fps = 30.0
        self.brix_val = round(23.5 + (math.sin(self.tick_count * 0.2) * 0.6), 1)

        # Build Device Registry
        devices: Dict[str, DeviceTelemetryItem] = {
            "DEV-AMS-01": DeviceTelemetryItem(
                device_id="DEV-AMS-01",
                name="Robotik Sağım İstasyonu (AMS / VMS)",
                category="MILKING",
                status="ALERT" if is_valve_locked else "RUNNING",
                power_draw_kw=ams_power,
                health_pct=98.5,
                key_metrics={
                    "quarter_channels": 4,
                    "spectrometer_scc_stream": "Aktif",
                    "milk_diverter_valve": "DRAIN_WASTE" if is_valve_locked else "MAIN_TANK",
                    "post_dip_spray_psi": 42.0,
                    "steam_sterilization_c": 95.0,
                    "concentrate_auger_dispense_kg": 1.8
                },
                operational_mode=ams_mode,
                last_action=ams_action,
                academic_key="conductivity"
            ),
            "DEV-JUNO-01": DeviceTelemetryItem(
                device_id="DEV-JUNO-01",
                name="Otonom Yem İtici Robot (Lely Juno X)",
                category="ROBOTICS",
                status="CHARGING" if is_juno_charging else "RUNNING",
                power_draw_kw=juno_power,
                health_pct=96.0,
                key_metrics={
                    "x_coordinate_m": round(self.juno_x, 1),
                    "y_coordinate_m": 12.5,
                    "speed_m_sec": juno_speed,
                    "auger_skirt_rpm": auger_rpm,
                    "ultrasonic_feed_height_cm": self.feed_height_cm,
                    "battery_soc_pct": round(self.juno_battery, 1)
                },
                operational_mode=juno_mode,
                last_action=juno_action,
                academic_key="juno_robot"
            ),
            "DEV-DISCOVERY-01": DeviceTelemetryItem(
                device_id="DEV-DISCOVERY-01",
                name="Otonom Gübre Vakum Robotu (Discovery Vac)",
                category="ROBOTICS",
                status=disc_status,
                power_draw_kw=disc_power,
                health_pct=94.5,
                key_metrics={
                    "x_coordinate_m": round(self.discovery_x, 1),
                    "y_coordinate_m": round(self.discovery_y, 1),
                    "tank_fill_pct": round(self.discovery_tank, 1),
                    "tank_capacity_l": 350,
                    "water_spray_nozzles": "Aktif (3 Bar)",
                    "battery_soc_pct": round(self.discovery_battery, 1)
                },
                operational_mode=disc_mode,
                last_action=disc_action,
                academic_key="discovery_robot"
            ),
            "DEV-GATE-01": DeviceTelemetryItem(
                device_id="DEV-GATE-01",
                name="Akıllı Otomatik Ayırma Kapısı (Smart Sorting Gate)",
                category="ROBOTICS",
                status="ALERT" if active_critical_cows > 0 else "RUNNING",
                power_draw_kw=0.35,
                health_pct=99.2,
                key_metrics={
                    "pneumatic_cylinder_pressure_bar": 6.2,
                    "gate_angle_degrees": self.gate_angle_deg,
                    "rfid_read_latency_ms": 18,
                    "divert_route": "TREATMENT_PEN" if active_critical_cows > 0 else "BARN_RETURN"
                },
                operational_mode=gate_mode,
                last_action=gate_action,
                academic_key="smart_gate"
            ),
            "DEV-BOLUS-NET": DeviceTelemetryItem(
                device_id="DEV-BOLUS-NET",
                name="İntraruminal Kablosuz Bolus Sensör Ağı (6 Baş)",
                category="SENSORS",
                status="RUNNING",
                power_draw_kw=0.08,
                health_pct=100.0,
                key_metrics={
                    "active_probes": 6,
                    "rf_frequency_mhz": 433.92,
                    "reticulum_temp_c": 38.8,
                    "motility_contractions_per_min": 1.9,
                    "daily_packets_transmitted": 576 + bolus_transmissions
                },
                operational_mode="Kablosuz ISM Telemetri Yayını",
                last_action="6 ineğin işkembe pH ve iç sıcaklık telemetrisi alındı.",
                academic_key="rumen_ph"
            ),
            "DEV-CAM-3D": DeviceTelemetryItem(
                device_id="DEV-CAM-3D",
                name="3D Bilgisayarlı Görü Derinlik Kamerası (RGB-D)",
                category="SENSORS",
                status="RUNNING",
                power_draw_kw=0.25,
                health_pct=99.0,
                key_metrics={
                    "frame_rate_fps": cam_fps,
                    "point_cloud_resolution": "1280x720 IR Depth",
                    "spine_arch_curvature_pct": 8.5,
                    "lens_cleanliness_pct": 99.8,
                    "detection_model": "ResNet-50 + YOLO-Pose"
                },
                operational_mode="Çıkış Koridoru Sürekli Yürüyüş Taraması",
                last_action="Topallık ve BCS vücut kondisyon skoru nokta bulutu hesaplandı.",
                academic_key="lameness"
            ),
            "DEV-HVLS-FANS": DeviceTelemetryItem(
                device_id="DEV-HVLS-FANS",
                name="Değişken Hızlı HVLS Tavan Fanları (Zone A-D)",
                category="HVAC",
                status="RUNNING" if self.fan_rpm > 0 else "IDLE",
                power_draw_kw=fan_power,
                health_pct=97.0,
                key_metrics={
                    "active_fan_units": 4,
                    "blade_diameter_m": 7.3,
                    "inverter_vfd_rpm": self.fan_rpm,
                    "airflow_velocity_m_s": round(self.fan_rpm * 0.0075, 2),
                    "thi_trigger_threshold": 72.0
                },
                operational_mode=fan_mode,
                last_action=f"Ahır mikroklima sirkülasyonu devrede ({self.fan_rpm} RPM).",
                academic_key="thi"
            ),
            "DEV-MISTING-SYS": DeviceTelemetryItem(
                device_id="DEV-MISTING-SYS",
                name="Yüksek Basınçlı Evaporatif Sisleme Pompası",
                category="HVAC",
                status="RUNNING" if self.misting_active else "IDLE",
                power_draw_kw=misting_power,
                health_pct=98.0,
                key_metrics={
                    "line_pressure_bar": 70.0,
                    "droplet_size_microns": 15.0,
                    "evaporative_cooling_delta_c": -3.5 if self.misting_active else 0.0,
                    "duty_cycle": "30s Açık / 4.5dk Kapalı"
                },
                operational_mode=misting_mode,
                last_action="İnek sırtlarını ıslatmadan ortam havasında evaporatif buharlaşma.",
                academic_key="thi"
            ),
            "DEV-DIGESTER-01": DeviceTelemetryItem(
                device_id="DEV-DIGESTER-01",
                name="Biyogaz Anaerobik Çürütücü (CSTR Reaktör)",
                category="ENERGY",
                status="RUNNING",
                power_draw_kw=1.85,
                health_pct=98.2,
                key_metrics={
                    "fermentation_temp_c": self.digester_temp,
                    "paddle_agitator_rpm": 45,
                    "biogas_flow_rate_m3_h": biogas_flow_m3_h,
                    "ch4_methane_purity_pct": 62.5,
                    "slurry_daily_intake_kg": 3600.0,
                    "flare_valve_status": "NORMAL (Basınç < 25 mbar)"
                },
                operational_mode="Mezofilik Anaerobik Fermantasyon (38.5°C)",
                last_action=f"Discovery'den gelen taze gübre fermente ediliyor ({biogas_flow_m3_h} m³/sa).",
                academic_key="biogas_chp"
            ),
            "DEV-CHP-GEN": DeviceTelemetryItem(
                device_id="DEV-CHP-GEN",
                name="Kojenerasyon (CHP) Gaz Motoru & Şebeke İnvertörü",
                category="ENERGY",
                status="RUNNING",
                power_draw_kw=0.0,  # Üretici cihaz
                health_pct=99.0,
                key_metrics={
                    "engine_synchronous_rpm": self.chp_rpm,
                    "electrical_output_kw": chp_power,
                    "thermal_heat_recovery_kw": chp_thermal_kw,
                    "grid_frequency_hz": 50.0,
                    "oil_pressure_bar": 4.2,
                    "net_grid_export_kw": round(chp_power - 8.2, 1)
                },
                operational_mode=f"Şebeke Senkron Üretim ({chp_power} kW Elektrik + {chp_thermal_kw} kW Isı)",
                last_action="Biyogaz yakılarak çiftlik enerjisi ve şebeke satışı sağlanıyor.",
                academic_key="biogas_chp"
            ),
            "DEV-CALF-FEEDER": DeviceTelemetryItem(
                device_id="DEV-CALF-FEEDER",
                name="Otomatik Buzağı Kolostrum İstasyonu & Brix Sensörü",
                category="CALVING",
                status="RUNNING",
                power_draw_kw=0.45,
                health_pct=99.5,
                key_metrics={
                    "optical_brix_refractometer_pct": self.brix_val,
                    "colostrum_igg_concentration_g_l": round(self.brix_val * 2.35, 1),
                    "pasteurizer_temp_c": 60.0,
                    "portion_temp_c": 38.5,
                    "fpt_protection_level": "Mükemmel (IgG > 50 g/L)"
                },
                operational_mode="Otomatik İmmünglobulin Kalite Kontrolü",
                last_action=f"Kolostrum Brix %{self.brix_val} ölçüldü; FPT koruması sağlandı.",
                academic_key="brix"
            ),
            "DEV-EDGE-GATEWAY": DeviceTelemetryItem(
                device_id="DEV-EDGE-GATEWAY",
                name="Endüstriyel Uç Bilişim Ağ Geçidi (Edge IoT Unit)",
                category="EDGE",
                status="RUNNING",
                power_draw_kw=0.15,
                health_pct=100.0,
                key_metrics={
                    "micro_cycle_latency_ms": 12,
                    "mqtt_packet_rate_per_sec": 48,
                    "offline_buffer_capacity_hours": 72,
                    "connected_controllers": 11,
                    "modbus_opc_status": "Online"
                },
                operational_mode="Düşük Gecikmeli Yerel Eşleme (Local Decision Loop)",
                last_action="11 ahır cihazı ve sensör düğümü 12ms döngüyle senkronize ediliyor.",
                academic_key="edge_computing"
            )
        }

        total_power = sum(d.power_draw_kw for d in devices.values())
        avg_health = sum(d.health_pct for d in devices.values()) / len(devices)

        summary = (
            f"🎛️ Çiftlik Cihaz Filosu Tam Otonom: 12 Endüstriyel Cihaz Canlı Devrede! "
            f"AMS sağım robotu {ams_mode.split()[0]} modunda, Juno orta yem yolunda (x={self.juno_x:.1f}m), "
            f"Discovery gübre vakumu (Tank %{self.discovery_tank:.0f}), HVLS fanlar ({self.fan_rpm} RPM), "
            f"CHP kojenerasyon ünitesi {chp_power} kW temiz elektrik üreterek tüm filoyu besliyor."
        )

        return FarmDevicesFleetProfile(
            timestamp=now,
            total_active_devices=len(devices),
            total_fleet_power_kw=round(total_power, 2),
            fleet_health_index_pct=round(avg_health, 1),
            devices=devices,
            status_summary=summary
        )

# Global singleton
farm_devices_engine = FarmDevicesEngine()
