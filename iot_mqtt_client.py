"""
AgriTwin Donanım & Sensör Entegrasyon Test Harness (IoT MQTT / REST Client)
Boyun tasmaları, pedometreler ve sağım robotu telemetrisini simüle eden donanım istemcisi.
"""

import sys
import time
import random
import json
import urllib.request
from datetime import datetime

# Ensure utf-8 output on Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

API_BASE = "http://127.0.0.1:8000"

def simulate_hardware_sensor_feed(cow_id="TR-34-101", cycles=3):
    print(f"📡 [IoT Hardware Gateway] {cow_id} için boyun tasması ve süt telemetrisi başlatılıyor...")

    for i in range(1, cycles + 1):
        telemetry_sample = {
            "device_id": f"COLLAR-SN-{cow_id.replace('TR-34-', '')}",
            "animal_id": cow_id,
            "timestamp": datetime.now().isoformat(),
            "accelerometer_raw": {
                "steps_last_hour": random.randint(38, 48),
                "head_tilt_angle_deg": round(random.uniform(15.0, 35.0), 1)
            },
            "rumination_microphone": {
                "chews_per_minute": random.randint(55, 62),
                "rumination_minutes_2h": random.randint(24, 28)
            },
            "bolus_thermometer_c": round(random.uniform(38.4, 38.7), 2),
            "milking_flow_sensor": {
                "electrical_conductivity_ms_cm": round(random.uniform(5.1, 5.3), 2),
                "flow_rate_kg_min": 2.4
            }
        }

        print(f"  [Döngü {i}/{cycles}] Telemetri Paketi Üretildi: "
              f"Adım: {telemetry_sample['accelerometer_raw']['steps_last_hour']} | "
              f"Geviş: {telemetry_sample['rumination_microphone']['rumination_minutes_2h']} dk | "
              f"İletkenlik: {telemetry_sample['milking_flow_sensor']['electrical_conductivity_ms_cm']} mS/cm")

        # Advance digital twin tick via REST
        try:
            req = urllib.request.Request(f"{API_BASE}/api/simulate/tick", method="POST")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                print(f"  -> Dijital İkize Senkronize Edildi (Tick #{data.get('tick')})")
        except Exception as e:
            print(f"  -> Bağlantı Uyarısı: {e}")

        time.sleep(1)

    print("✅ [IoT Hardware Gateway] Telemetri test seansı başarıyla tamamlandı.")

if __name__ == "__main__":
    simulate_hardware_sensor_feed()
