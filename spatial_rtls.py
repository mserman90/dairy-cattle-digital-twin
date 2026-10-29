import math
import random
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class GridCell(BaseModel):
    x_idx: int
    y_idx: int
    center_x_m: float
    center_y_m: float
    temperature_c: float
    relative_humidity_pct: float
    thi_index: float
    fan_influence: bool = False

class AnimalPosition(BaseModel):
    animal_id: str
    name: str
    x_m: float
    y_m: float
    health_status: str
    is_seeking_cooling: bool = False

class SpatialRTLSEngine:
    """
    UWB / BLE Real-Time Location System (RTLS) ve Barınak Mikroklima Izgara Motoru
    Barınak Boyutları: 40 metre x 25 metre (8 sütun x 5 satır = 40 hücre)
    """

    def __init__(self):
        self.width_m = 40.0
        self.height_m = 25.0
        self.cols = 8
        self.rows = 5

        # Fan coordinates (Fan A at (10, 12.5), Fan B at (30, 12.5))
        self.fan_locations = [
            {"id": "FAN-A", "x": 10.0, "y": 12.5, "active": False},
            {"id": "FAN-B", "x": 30.0, "y": 12.5, "active": False}
        ]

        # Initial cow positions inside the barn
        self.positions: Dict[str, Dict[str, float]] = {
            "TR-34-101": {"x": 8.5, "y": 14.0},
            "TR-34-102": {"x": 12.0, "y": 8.0},
            "TR-34-103": {"x": 6.0, "y": 18.0},
            "TR-34-104": {"x": 28.0, "y": 10.0},
            "TR-34-105": {"x": 32.5, "y": 16.5},
            "TR-34-106": {"x": 35.0, "y": 7.5}
        }

    def compute_grid(self, base_temp_a: float, base_temp_b: float, rh_pct: float, fans_active: bool) -> List[GridCell]:
        cells = []
        cell_w = self.width_m / self.cols
        cell_h = self.height_m / self.rows

        # Update fan states
        for f in self.fan_locations:
            f["active"] = fans_active

        for r in range(self.rows):
            for c in range(self.cols):
                cx = (c + 0.5) * cell_w
                cy = (r + 0.5) * cell_h

                # Base temp gradient (West to East)
                base_t = base_temp_a if cx < (self.width_m / 2.0) else base_temp_b

                # Cooling effect from fans
                cooling_delta = 0.0
                fan_influence = False
                for f in self.fan_locations:
                    dist = math.hypot(cx - f["x"], cy - f["y"])
                    if dist < 8.0 and f["active"]:
                        cooling_delta += (8.0 - dist) * 0.45
                        fan_influence = True

                eff_temp = max(18.0, round(base_t - cooling_delta, 1))
                # THI calculation
                thi = round((1.8 * eff_temp + 32) - (0.55 - 0.0055 * rh_pct) * (1.8 * eff_temp - 26), 1)

                cells.append(GridCell(
                    x_idx=c,
                    y_idx=r,
                    center_x_m=round(cx, 1),
                    center_y_m=round(cy, 1),
                    temperature_c=eff_temp,
                    relative_humidity_pct=rh_pct,
                    thi_index=thi,
                    fan_influence=fan_influence
                ))

        return cells

    def update_animal_positions(self, animals: List[Any], heat_stress_active: bool, fans_active: bool) -> List[AnimalPosition]:
        result = []

        for a in animals:
            pos = self.positions.get(a.id, {"x": 20.0, "y": 12.5})
            is_seeking = False

            # If heat stress is active and fans are running, cows gravitate towards nearest fan (bunching behavior)
            if heat_stress_active and fans_active:
                target_fan = self.fan_locations[0] if pos["x"] < 20.0 else self.fan_locations[1]
                dx = target_fan["x"] - pos["x"]
                dy = target_fan["y"] - pos["y"]
                dist = math.hypot(dx, dy)

                if dist > 2.5:
                    # Move towards fan
                    step = 0.8
                    pos["x"] += (dx / dist) * step + random.uniform(-0.2, 0.2)
                    pos["y"] += (dy / dist) * step + random.uniform(-0.2, 0.2)
                    is_seeking = True
            else:
                # Normal random grazing / walking within barn boundaries
                pos["x"] = max(2.0, min(self.width_m - 2.0, pos["x"] + random.uniform(-0.6, 0.6)))
                pos["y"] = max(2.0, min(self.height_m - 2.0, pos["y"] + random.uniform(-0.6, 0.6)))

            self.positions[a.id] = pos
            result.append(AnimalPosition(
                animal_id=a.id,
                name=a.name,
                x_m=round(pos["x"], 1),
                y_m=round(pos["y"], 1),
                health_status=a.dss.overall_health_status,
                is_seeking_cooling=is_seeking
            ))

        return result

# Global RTLS singleton
rtls_engine = SpatialRTLSEngine()
