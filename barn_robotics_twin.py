"""
AgriTwin: Otonom Ahır İçi Robot Filosu İkizi
(Autonomous Barn Robotics Fleet Twin: Feed Pusher & Manure Vacuum)

Modellenen Sistemler (Lely Juno / DeLaval OptiDuo & Lely Discovery / GEA Barn-e):
1. Otonom Yem İtici Robot (Autonomous Feed Pusher - Juno):
   - Yem yolunda her 1.5 saatte bir otonom dolaşarak yemi hayvanların önüne iter.
   - Ultrasonik sensörle yem yığını yüksekliğini ölçer.
   - Kuru Madde Tüketimini (DMI) %+3.2, süt verimini +1.1 kg/gün artırır; yem seçmeyi önler.
2. Otonom Gübre Vakum / Sıyırıcı Robotu (Autonomous Manure Vacuum - Discovery):
   - Barınak yürüyüş yollarındaki taze dışkıyı 350 litrelik tankına vakumlar.
   - Biyogaz transfer çukuruna otonom deşarj eder (Biyogaz reaktörünü taze gübreyle besler).
   - Tırnak sağlığını koruyarak topallık riskini %28, çevresel mastitisi %32 düşürür.
3. RTLS Mekânsal Koordinasyon & Güvenlik:
   - 40m x 25m barınak üzerinde gerçek zamanlı (x, y) konumları.
   - Ultrasonik/UWB inek yaklaşım sensörü ile çarpışma önleme (Obstacle Avoidance).
"""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
import math
import random
from pydantic import BaseModel, Field

class FeedPusherRobot(BaseModel):
    robot_id: str = "ROBOT-PUSHER-JUNO"
    name: str = "Juno-X Otonom Yem İtici"
    robot_type: Literal["FEED_PUSHER"] = "FEED_PUSHER"
    status: Literal["PUSHING", "CHARGING", "OBSTACLE_AVOIDANCE", "IDLE"] = "PUSHING"
    battery_pct: float = Field(88.0, description="Batarya Şarj Seviyesi (%)")
    x_m: float = Field(18.5, description="Barınak X Koordinatı (m)")
    y_m: float = Field(12.5, description="Barınak Y Koordinatı (m) - Yem Yolu")
    speed_m_sec: float = Field(0.25, description="İlerleme Hızı (m/s)")
    auger_rpm: int = Field(85, description="Helezon Döner Etek Devri (rpm)")
    feed_height_sensor_cm: float = Field(18.5, description="Ultrasonik Yem Yığını Yüksekliği (cm)")
    daily_pushes_completed: int = Field(14, description="Bugün tamamlanan yem itme seansı")
    dmi_boost_pct: float = Field(3.2, description="Kuru Madde Tüketimi (DMI) Artışı (%)")
    milk_yield_boost_kg: float = Field(1.1, description="İnek başı günlük süt verim artışı (kg)")
    charging_dock: Dict[str, float] = {"x": 2.0, "y": 12.5}
    is_charging: bool = False
    task_description: str = "Orta yem yolunda yemleri hayvanların erişim mesafesine itiyor."

class ManureCollectorRobot(BaseModel):
    robot_id: str = "ROBOT-MANURE-VAC"
    name: str = "Discovery-Vac Gübre Toplama Robotu"
    robot_type: Literal["MANURE_VACUUM"] = "MANURE_VACUUM"
    status: Literal["VACUUMING", "DUMPING", "CHARGING", "OBSTACLE_AVOIDANCE", "IDLE"] = "VACUUMING"
    battery_pct: float = Field(74.0, description="Batarya Şarj Seviyesi (%)")
    x_m: float = Field(14.0, description="Barınak X Koordinatı (m)")
    y_m: float = Field(8.0, description="Barınak Y Koordinatı (m)")
    tank_fill_pct: float = Field(42.0, description="Gübre Tankı Doluluk Oranı (%)")
    tank_capacity_liters: int = 350
    water_spray_active: bool = Field(True, description="Kaymayı önleyici ön su püskürtme memesi")
    daily_manure_collected_kg: float = Field(1250.0, description="Bugün toplanıp biyogaz çukuruna aktarılan gübre (kg)")
    lameness_reduction_pct: float = Field(28.0, description="Tırnak enfeksiyonu & topallık azaltım etkisi (%)")
    environmental_mastitis_reduction_pct: float = Field(32.0, description="Meme hijyeni ve mastitis koruma etkisi (%)")
    dump_station: Dict[str, float] = {"x": 38.0, "y": 2.5}
    is_dumping: bool = False
    task_description: str = "Bölüm A yürüyüş yolunda gübreyi vakumlayarak zemini kuru ve temiz tutuyor."

class BarnRoboticsFleetProfile(BaseModel):
    timestamp: datetime
    pusher: FeedPusherRobot
    collector: ManureCollectorRobot
    fleet_power_draw_kw: float = Field(1.65, description="Robotların anlık şarj gücü (kW - Biyogaz CHP ile karşılanır)")
    total_daily_energy_kwh: float = Field(12.4, description="Robotik filonun günlük elektrik tüketimi (kWh/gün)")
    fleet_safety_status: str = "GÜVENLİ (Engel Sensörleri Devrede, Çarpışma Riski %0)"
    fleet_economic_value_annual_tl: float = Field(182000.0, description="Verim artışı ve işçilik tasarrufu (TL/yıl)")
    status_summary: str

class BarnRoboticsEngine:
    """
    Ahır İçi Otonom Robot Filosu Simülasyon Motoru
    """

    def __init__(self):
        self.step_counter = 0
        # Yem itici robot orta yem yolunda (y=12.5, x: 4.0 - 36.0 arası) gidip gelir
        self.pusher_x = 18.5
        self.pusher_dir = 1.0  # 1: Sağa, -1: Sola

        # Gübre robotu Bölüm A ve B koridorlarında dolanır
        self.collector_x = 14.0
        self.collector_y = 8.0
        self.collector_dir_x = 1.0
        self.collector_dir_y = 0.5
        self.collector_tank = 42.0
        self.pusher_battery = 88.0
        self.collector_battery = 74.0

    def tick_robot_fleet(
        self,
        cows_near_pusher: bool = False,
        cows_near_collector: bool = False
    ) -> BarnRoboticsFleetProfile:
        self.step_counter += 1
        now = datetime.now()

        # 1. Yem İtici Robot Dinamiği
        if cows_near_pusher:
            pusher_status = "OBSTACLE_AVOIDANCE"
            pusher_desc = "İnek geçişi algılandı. Ultrasonik güvenlik sensörü devreye girdi; robot bekliyor."
            pusher_speed = 0.0
        else:
            pusher_status = "PUSHING"
            pusher_desc = "Orta yem yolunda yemleri helezon devriyle ineklerin erişim mesafesine itiyor."
            pusher_speed = 0.25
            self.pusher_x += self.pusher_dir * 1.8
            if self.pusher_x >= 35.5:
                self.pusher_dir = -1.0
            elif self.pusher_x <= 4.5:
                self.pusher_dir = 1.0

        # Batarya yavaşça azalır, şarj istasyonunda dolar
        self.pusher_battery = max(15.0, self.pusher_battery - 0.1)

        pusher_robot = FeedPusherRobot(
            status=pusher_status,
            battery_pct=round(self.pusher_battery, 1),
            x_m=round(self.pusher_x, 1),
            y_m=12.5,
            speed_m_sec=pusher_speed,
            auger_rpm=85 if pusher_speed > 0 else 0,
            feed_height_sensor_cm=round(18.5 + random.uniform(-1.5, 1.5), 1),
            daily_pushes_completed=14 + (self.step_counter // 20),
            task_description=pusher_desc
        )

        # 2. Gübre Vakum Robotu Dinamiği
        if cows_near_collector:
            collector_status = "OBSTACLE_AVOIDANCE"
            collector_desc = "İnek güvenliği için durdu. Zemin su püskürtmesi beklemede."
        elif self.collector_tank >= 90.0:
            collector_status = "DUMPING"
            collector_desc = "Tank doldu. Robot biyogaz transfer çukuruna gübre deşarjı yapıyor."
            self.collector_tank = 10.0  # Boşaldı
            self.collector_x = 38.0
            self.collector_y = 2.5
        else:
            collector_status = "VACUUMING"
            collector_desc = "Izgara yürüyüş yolunda gübreyi vakumlayarak zemini kuru ve kaymaz tutuyor."
            self.collector_x += self.collector_dir_x * 1.5
            self.collector_y += self.collector_dir_y * 1.0

            if self.collector_x >= 36.0 or self.collector_x <= 4.0:
                self.collector_dir_x *= -1.0
            if self.collector_y >= 22.0 or self.collector_y <= 4.0:
                self.collector_dir_y *= -1.0

            self.collector_tank = min(100.0, self.collector_tank + 0.8)

        self.collector_battery = max(15.0, self.collector_battery - 0.15)

        collector_robot = ManureCollectorRobot(
            status=collector_status,
            battery_pct=round(self.collector_battery, 1),
            x_m=round(self.collector_x, 1),
            y_m=round(self.collector_y, 1),
            tank_fill_pct=round(self.collector_tank, 1),
            water_spray_active=(collector_status == "VACUUMING"),
            daily_manure_collected_kg=round(1250.0 + (self.step_counter * 8.5), 1),
            task_description=collector_desc
        )

        # 80 başlık sürüde robotik yem itme (+1.1 kg süt) ve gübre sıyırmanın yıllık değeri
        annual_val = round((80 * 1.1 * 16.5 * 365.0 * 0.40) + 48000.0, 2)  # Verim kârı + işçilik ikamesi

        summary = (
            f"🤖 Otonom Ahır Robot Filosu Aktif! Yem itici robot yem yolunda (x: {pusher_robot.x_m}m) DMI'ı %+3.2 artırıyor. "
            f"Gübre vakum robotu (x: {collector_robot.x_m}m, y: {collector_robot.y_m}m, Tank: %{collector_robot.tank_fill_pct}) "
            f"topallık riskini %28 düşürerek toplanan gübreyi biyogaz reaktörüne transfer ediyor."
        )

        return BarnRoboticsFleetProfile(
            timestamp=now,
            pusher=pusher_robot,
            collector=collector_robot,
            fleet_power_draw_kw=1.65,
            total_daily_energy_kwh=12.4,
            fleet_safety_status="GÜVENLİ (Ultrasonik & UWB Çarpışma Önleme Devrede)",
            fleet_economic_value_annual_tl=annual_val,
            status_summary=summary
        )

# Global singleton engine
robotics_fleet_engine = BarnRoboticsEngine()
