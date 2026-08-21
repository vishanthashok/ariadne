"""Extended Kalman Filter for visual-inertial fusion."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np


def measurement_noise_from_confidence(confidence: float) -> float:
    if confidence > 0.8:
        return 50.0
    if confidence >= 0.5:
        return 200.0
    return 1000.0


@dataclass
class EKFState:
    lat: float
    lon: float
    vn: float
    ve: float
    heading: float
    P: np.ndarray
    innovation: Optional[np.ndarray] = None


class VisualInertialEKF:
    """State: [lat, lon, vn, ve, heading]."""

    def __init__(
        self,
        lat0: float,
        lon0: float,
        heading0: float = 0.0,
        vn0: float = 0.0,
        ve0: float = 0.0,
    ):
        self.x = np.array([lat0, lon0, vn0, ve0, heading0], dtype=np.float64)
        self.P = np.diag([100.0, 100.0, 25.0, 25.0, 5.0]).astype(np.float64)
        self.Q = np.diag([1e-10, 1e-10, 0.5, 0.5, 0.1]).astype(np.float64)

    def _meters_to_deg(self, lat: float, dn: float, de: float) -> tuple[float, float]:
        dlat = dn / 111_320.0
        dlon = de / (111_320.0 * max(0.2, math.cos(math.radians(lat))))
        return dlat, dlon

    def predict(self, imu_reading: dict, dt: float = 0.1) -> EKFState:
        """Propagate with IMU (simplified strapdown)."""
        ax = float(imu_reading.get("ax", 0.0))
        ay = float(imu_reading.get("ay", 0.0))
        gz = float(imu_reading.get("gz", 0.0))

        lat, lon, vn, ve, heading = self.x
        # Rotate body accel to NED (approx, ignore pitch/roll)
        hrad = math.radians(heading)
        an = ax * math.cos(hrad) - ay * math.sin(hrad)
        ae = ax * math.sin(hrad) + ay * math.cos(hrad)

        vn = vn + an * dt
        ve = ve + ae * dt
        heading = (heading + math.degrees(gz) * dt) % 360.0
        dlat, dlon = self._meters_to_deg(lat, vn * dt, ve * dt)
        lat = lat + dlat
        lon = lon + dlon

        self.x = np.array([lat, lon, vn, ve, heading], dtype=np.float64)

        # Simple linear process noise inflation
        F = np.eye(5)
        F[0, 2] = dt / 111_320.0
        F[1, 3] = dt / (111_320.0 * max(0.2, math.cos(math.radians(lat))))
        F[4, 4] = 1.0
        self.P = F @ self.P @ F.T + self.Q * dt

        return self.get_state()

    def update(
        self,
        lat_meas: float,
        lon_meas: float,
        confidence: float,
    ) -> EKFState:
        R_m = measurement_noise_from_confidence(confidence)
        # Convert meter noise to deg approx
        lat = self.x[0]
        R = np.diag(
            [
                (R_m / 111_320.0) ** 2,
                (R_m / (111_320.0 * max(0.2, math.cos(math.radians(lat))))) ** 2,
            ]
        )
        H = np.zeros((2, 5))
        H[0, 0] = 1.0
        H[1, 1] = 1.0
        z = np.array([lat_meas, lon_meas], dtype=np.float64)
        y = z - H @ self.x
        S = H @ self.P @ H.T + R
        K = self.P @ H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        self.P = (np.eye(5) - K @ H) @ self.P
        return self.get_state(innovation=y)

    def step(
        self,
        imu_reading: dict,
        visual_estimate: Optional[tuple[float, float]] = None,
        visual_confidence: Optional[float] = None,
        dt: float = 0.1,
    ) -> EKFState:
        state = self.predict(imu_reading, dt=dt)
        if visual_estimate is not None and visual_confidence is not None and visual_confidence >= 0.3:
            state = self.update(visual_estimate[0], visual_estimate[1], visual_confidence)
        return state

    def get_state(self, innovation: Optional[np.ndarray] = None) -> EKFState:
        return EKFState(
            lat=float(self.x[0]),
            lon=float(self.x[1]),
            vn=float(self.x[2]),
            ve=float(self.x[3]),
            heading=float(self.x[4]),
            P=self.P.copy(),
            innovation=innovation,
        )

    def error_radius_m(self) -> float:
        # 1-sigma ellipse approx from lat/lon covariance
        lat = self.x[0]
        var_n = self.P[0, 0] * (111_320.0**2)
        var_e = self.P[1, 1] * ((111_320.0 * max(0.2, math.cos(math.radians(lat)))) ** 2)
        return float(math.sqrt(max(var_n, 0) + max(var_e, 0)))
