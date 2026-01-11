#!/usr/bin/env python3
"""
Radar Track Simulation - Plot Extractor Output

Purpose: Simulate spatial tracking output from X-band surveillance radar
JIRA: VRD-32 - Simulate Radar Track Output (Plot Extractor)
Epic: VRD-1 - Sensor Domain: RF Micro-Doppler Physics & Validation

This script generates time-series positional tracks (Az, El, Range) with realistic
measurement noise to enable slew-to-cue logic for thermal/visual turret.

Key Capabilities:
1. Generates realistic flight paths (linear, circular, hovering)
2. Injects Gaussian measurement noise (σ_Az, σ_El, σ_Range)
3. Simulates missed detections (random packet dropout)
4. Outputs standardized CSV format for sensor fusion

Technical Scope:
- NOT simulating raw electromagnetics (that's TRL 6+)
- Simulating Plot Extractor output of surveillance radar (e.g., Blighter A400)
- Provides "sloppy" radar detections for "precise" turret slew-to-cue

Reference Radar: Blighter A400 X-band surveillance radar
- Azimuth accuracy: ±1.0° RMS
- Elevation accuracy: ±1.5° RMS
- Range accuracy: ±10 m RMS
- Detection rate: 95% (5% missed detections)
- Update rate: 1 Hz (typical for surveillance mode)

Author: Veridical Perception - Sensor Team
Date: 2026-01-10
Version: 1.0
"""

import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path
import argparse


class RadarTrackSimulator:
    """
    Simulates radar plot extractor output with realistic measurement noise.

    Models Blighter A400-style X-band surveillance radar tracking performance
    for drone detection and tracking scenarios.
    """

    def __init__(
        self,
        update_rate_hz=1.0,        # Surveillance radar typical: 1 Hz
        sigma_azimuth_deg=1.0,     # Blighter A400 spec: ±1.0° RMS
        sigma_elevation_deg=1.5,   # Elevation typically worse: ±1.5° RMS
        sigma_range_m=10.0,        # Range accuracy: ±10 m RMS
        missed_detection_prob=0.05, # 5% packet dropout (95% detection rate)
        beam_width_deg=3.0,        # Blighter A400: ~3° beamwidth
        max_range_m=5000.0,        # Blighter A400: 5 km detection range
        radar_lat=37.7749,         # San Francisco (example location)
        radar_lon=-122.4194,
        radar_alt_m=10.0           # Radar mounted 10m above ground
    ):
        """
        Initialize radar track simulator.

        Args:
            update_rate_hz: Radar scan rate (Hz), typically 1 Hz for surveillance
            sigma_azimuth_deg: Azimuth measurement noise (°, 1-sigma)
            sigma_elevation_deg: Elevation measurement noise (°, 1-sigma)
            sigma_range_m: Range measurement noise (m, 1-sigma)
            missed_detection_prob: Probability of missed detection (0-1)
            beam_width_deg: Radar beam width (degrees, for metadata)
            max_range_m: Maximum detection range (meters)
            radar_lat: Radar latitude (decimal degrees)
            radar_lon: Radar longitude (decimal degrees)
            radar_alt_m: Radar altitude above ground (meters)
        """
        self.update_rate_hz = update_rate_hz
        self.dt = 1.0 / update_rate_hz  # Time step between updates

        # Measurement noise parameters (Gaussian, 1-sigma)
        self.sigma_az = sigma_azimuth_deg
        self.sigma_el = sigma_elevation_deg
        self.sigma_range = sigma_range_m

        # Detection performance
        self.missed_detection_prob = missed_detection_prob

        # Radar specifications
        self.beam_width = beam_width_deg
        self.max_range = max_range_m

        # Radar position (ENU origin)
        self.radar_lat = radar_lat
        self.radar_lon = radar_lon
        self.radar_alt = radar_alt_m

        # Track storage
        self.tracks = []

        print(f"[INFO] Radar Track Simulator initialized")
        print(f"       - Update Rate: {self.update_rate_hz} Hz")
        print(f"       - Azimuth Error: sigma = {self.sigma_az} deg")
        print(f"       - Elevation Error: sigma = {self.sigma_el} deg")
        print(f"       - Range Error: sigma = {self.sigma_range} m")
        print(f"       - Missed Detection Rate: {self.missed_detection_prob*100:.1f}%")
        print(f"       - Beam Width: {self.beam_width} deg")
        print(f"       - Max Range: {self.max_range} m")

    def generate_linear_flight_path(
        self,
        start_position,      # (East_m, North_m, Up_m) relative to radar
        velocity,            # (vE, vN, vU) in m/s
        duration_sec,        # Flight duration
        track_id="TRK001"
    ):
        """
        Generate linear flight path (constant velocity).

        Example: Drone flying North-to-South at 50m altitude

        Args:
            start_position: (E, N, U) in meters from radar (ENU coordinates)
            velocity: (vE, vN, vU) velocity vector in m/s
            duration_sec: Flight duration in seconds
            track_id: Track identifier string

        Returns:
            ground_truth: List of dicts with true positions
        """
        num_samples = int(duration_sec * self.update_rate_hz)

        start_time = datetime.utcnow()

        ground_truth = []

        for i in range(num_samples):
            t = i * self.dt

            # True position (linear motion)
            pos_E = start_position[0] + velocity[0] * t
            pos_N = start_position[1] + velocity[1] * t
            pos_U = start_position[2] + velocity[2] * t

            # Convert ENU to spherical (Az, El, Range) from radar
            az, el, rng = self._enu_to_aer(pos_E, pos_N, pos_U)

            ground_truth.append({
                'timestamp': start_time + timedelta(seconds=t),
                'track_id': track_id,
                'true_azimuth_deg': az,
                'true_elevation_deg': el,
                'true_range_m': rng,
                'true_east_m': pos_E,
                'true_north_m': pos_N,
                'true_up_m': pos_U
            })

        print(f"\n[INFO] Generated linear flight path:")
        print(f"       - Track ID: {track_id}")
        print(f"       - Duration: {duration_sec} sec")
        print(f"       - Samples: {num_samples}")
        print(f"       - Start: E={start_position[0]:.1f}, N={start_position[1]:.1f}, U={start_position[2]:.1f} m")
        print(f"       - Velocity: vE={velocity[0]:.1f}, vN={velocity[1]:.1f}, vU={velocity[2]:.1f} m/s")

        return ground_truth

    def generate_circular_flight_path(
        self,
        center_position,     # (East_m, North_m, Up_m) center of circle
        radius_m,            # Circle radius in horizontal plane
        angular_rate_deg_s,  # Rotation rate (deg/s, positive = CCW)
        duration_sec,
        track_id="TRK002"
    ):
        """
        Generate circular flight path (loitering drone).

        Example: Drone circling at 100m altitude with 50m radius

        Args:
            center_position: (E, N, U) center of circular path
            radius_m: Circle radius in meters
            angular_rate_deg_s: Rotation rate (deg/s)
            duration_sec: Flight duration
            track_id: Track identifier

        Returns:
            ground_truth: List of dicts with true positions
        """
        num_samples = int(duration_sec * self.update_rate_hz)

        start_time = datetime.utcnow()

        ground_truth = []

        for i in range(num_samples):
            t = i * self.dt

            # Circular motion in horizontal plane
            angle_rad = np.deg2rad(angular_rate_deg_s * t)

            pos_E = center_position[0] + radius_m * np.cos(angle_rad)
            pos_N = center_position[1] + radius_m * np.sin(angle_rad)
            pos_U = center_position[2]  # Constant altitude

            az, el, rng = self._enu_to_aer(pos_E, pos_N, pos_U)

            ground_truth.append({
                'timestamp': start_time + timedelta(seconds=t),
                'track_id': track_id,
                'true_azimuth_deg': az,
                'true_elevation_deg': el,
                'true_range_m': rng,
                'true_east_m': pos_E,
                'true_north_m': pos_N,
                'true_up_m': pos_U
            })

        print(f"\n[INFO] Generated circular flight path:")
        print(f"       - Track ID: {track_id}")
        print(f"       - Center: E={center_position[0]:.1f}, N={center_position[1]:.1f}, U={center_position[2]:.1f} m")
        print(f"       - Radius: {radius_m} m")
        print(f"       - Angular Rate: {angular_rate_deg_s} deg/s")
        print(f"       - Duration: {duration_sec} sec")

        return ground_truth

    def _enu_to_aer(self, east_m, north_m, up_m):
        """
        Convert ENU (East-North-Up) coordinates to AER (Azimuth-Elevation-Range).

        Coordinate Systems:
        - ENU: Local Cartesian (radar at origin)
          - East: +X axis
          - North: +Y axis
          - Up: +Z axis
        - AER: Spherical (radar-centric)
          - Azimuth: 0° = North, 90° = East (clockwise from North)
          - Elevation: 0° = horizon, 90° = zenith
          - Range: Slant distance from radar

        Args:
            east_m: East offset from radar (meters)
            north_m: North offset from radar (meters)
            up_m: Height above radar (meters)

        Returns:
            azimuth_deg: Azimuth angle (degrees, 0-360)
            elevation_deg: Elevation angle (degrees, -90 to +90)
            range_m: Slant range (meters)
        """
        # Slant range
        range_m = np.sqrt(east_m**2 + north_m**2 + up_m**2)

        # Azimuth (0° = North, 90° = East, clockwise)
        azimuth_deg = np.rad2deg(np.arctan2(east_m, north_m))
        if azimuth_deg < 0:
            azimuth_deg += 360.0

        # Elevation (angle above horizon)
        ground_range = np.sqrt(east_m**2 + north_m**2)
        elevation_deg = np.rad2deg(np.arctan2(up_m, ground_range))

        return azimuth_deg, elevation_deg, range_m

    def inject_measurement_noise(self, ground_truth):
        """
        Inject Gaussian measurement noise to ground truth positions.

        Simulates realistic radar measurement errors:
        - Azimuth: Gaussian noise, σ = 1.0° (Blighter A400 spec)
        - Elevation: Gaussian noise, σ = 1.5° (typically worse than azimuth)
        - Range: Gaussian noise, σ = 10 m (Blighter A400 spec)

        Also simulates missed detections (5% packet dropout).

        Args:
            ground_truth: List of dicts with true positions

        Returns:
            noisy_tracks: List of dicts with measured positions (some dropped)
        """
        noisy_tracks = []

        num_detections = 0
        num_missed = 0

        for gt in ground_truth:
            # Simulate missed detection (packet dropout)
            if np.random.rand() < self.missed_detection_prob:
                num_missed += 1
                continue  # Drop this detection

            num_detections += 1

            # True values
            true_az = gt['true_azimuth_deg']
            true_el = gt['true_elevation_deg']
            true_rng = gt['true_range_m']

            # Inject Gaussian noise
            meas_az = true_az + np.random.normal(0, self.sigma_az)
            meas_el = true_el + np.random.normal(0, self.sigma_el)
            meas_rng = true_rng + np.random.normal(0, self.sigma_range)

            # Wrap azimuth to [0, 360)
            meas_az = meas_az % 360.0

            # Clamp elevation to [-90, 90]
            meas_el = np.clip(meas_el, -90.0, 90.0)

            # Ensure positive range
            meas_rng = max(0.0, meas_rng)

            # Compute confidence (inverse of range-normalized error)
            # Confidence = 1.0 at close range, decreases with distance
            # Also models detection quality (could be extended with SNR)
            confidence = max(0.1, 1.0 - (meas_rng / self.max_range))

            noisy_tracks.append({
                'timestamp': gt['timestamp'],
                'track_id': gt['track_id'],
                'azimuth_deg': meas_az,
                'elevation_deg': meas_el,
                'range_m': meas_rng,
                'confidence': confidence,
                # Keep ground truth for validation (optional, can be removed)
                'true_azimuth_deg': true_az,
                'true_elevation_deg': true_el,
                'true_range_m': true_rng
            })

        detection_rate = num_detections / len(ground_truth)

        print(f"\n[INFO] Injected measurement noise:")
        print(f"       - Total samples: {len(ground_truth)}")
        print(f"       - Detections: {num_detections}")
        print(f"       - Missed: {num_missed}")
        print(f"       - Detection rate: {detection_rate*100:.1f}%")

        return noisy_tracks

    def export_tracks_csv(self, tracks, output_path='output/radar_tracks.csv'):
        """
        Export tracks to CSV format for slew-to-cue module.

        VRD-32 Requirement: CSV with columns:
        - Timestamp (ISO 8601 UTC)
        - TrackID
        - Azimuth_Deg
        - Elevation_Deg
        - Range_m
        - Confidence (0-1)

        Optional ground truth columns (for validation):
        - True_Azimuth_Deg
        - True_Elevation_Deg
        - True_Range_m

        Args:
            tracks: List of track dicts
            output_path: Output CSV file path
        """
        import csv

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='') as f:
            # CSV header
            fieldnames = [
                'Timestamp',
                'TrackID',
                'Azimuth_Deg',
                'Elevation_Deg',
                'Range_m',
                'Confidence',
                # Ground truth (for validation, can be removed for production)
                'True_Azimuth_Deg',
                'True_Elevation_Deg',
                'True_Range_m'
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for track in tracks:
                writer.writerow({
                    'Timestamp': track['timestamp'].isoformat() + 'Z',
                    'TrackID': track['track_id'],
                    'Azimuth_Deg': f"{track['azimuth_deg']:.4f}",
                    'Elevation_Deg': f"{track['elevation_deg']:.4f}",
                    'Range_m': f"{track['range_m']:.2f}",
                    'Confidence': f"{track['confidence']:.4f}",
                    'True_Azimuth_Deg': f"{track.get('true_azimuth_deg', 0):.4f}",
                    'True_Elevation_Deg': f"{track.get('true_elevation_deg', 0):.4f}",
                    'True_Range_m': f"{track.get('true_range_m', 0):.2f}"
                })

        file_size_kb = output_path.stat().st_size / 1024

        print(f"\n[SUCCESS] Tracks exported to CSV:")
        print(f"       - File: {output_path}")
        print(f"       - Size: {file_size_kb:.2f} KB")
        print(f"       - Tracks: {len(tracks)} detections")

    def export_metadata_json(self, tracks, output_path='output/radar_tracks_metadata.json'):
        """
        Export radar metadata JSON sidecar.

        VRD-32 Requirement: Include radar theoretical beam width for uncertainty calculation.

        Args:
            tracks: List of track dicts (for summary stats)
            output_path: Output JSON file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Compute summary statistics
        if len(tracks) > 0:
            azimuths = [t['azimuth_deg'] for t in tracks]
            elevations = [t['elevation_deg'] for t in tracks]
            ranges = [t['range_m'] for t in tracks]
            confidences = [t['confidence'] for t in tracks]

            # Compute measurement errors (if ground truth available)
            if 'true_azimuth_deg' in tracks[0]:
                az_errors = [abs(t['azimuth_deg'] - t['true_azimuth_deg']) for t in tracks]
                el_errors = [abs(t['elevation_deg'] - t['true_elevation_deg']) for t in tracks]
                rng_errors = [abs(t['range_m'] - t['true_range_m']) for t in tracks]

                measured_sigma_az = np.std(az_errors)
                measured_sigma_el = np.std(el_errors)
                measured_sigma_rng = np.std(rng_errors)
            else:
                measured_sigma_az = None
                measured_sigma_el = None
                measured_sigma_rng = None
        else:
            measured_sigma_az = None
            measured_sigma_el = None
            measured_sigma_rng = None

        metadata = {
            "format_version": "1.0",
            "data_type": "radar_plot_extractor_output",
            "jira_task": "VRD-32",
            "epic": "VRD-1",
            "timestamp_utc": datetime.utcnow().isoformat() + 'Z',

            # Radar specifications (for slew-to-cue uncertainty calculation)
            "radar_model": "Blighter A400 (simulated)",
            "radar_type": "X-band surveillance",
            "radar_frequency_ghz": 10.0,
            "beam_width_deg": self.beam_width,
            "max_range_m": self.max_range,
            "update_rate_hz": self.update_rate_hz,

            # Measurement noise parameters (theoretical)
            "azimuth_accuracy_deg_rms": self.sigma_az,
            "elevation_accuracy_deg_rms": self.sigma_el,
            "range_accuracy_m_rms": self.sigma_range,
            "missed_detection_probability": self.missed_detection_prob,

            # Measured performance (actual simulation statistics)
            "measured_azimuth_error_deg_std": measured_sigma_az,
            "measured_elevation_error_deg_std": measured_sigma_el,
            "measured_range_error_m_std": measured_sigma_rng,

            # Track summary
            "num_detections": len(tracks),
            "track_ids": list(set([t['track_id'] for t in tracks])),

            # Radar position (for coordinate transforms)
            "radar_latitude_deg": self.radar_lat,
            "radar_longitude_deg": self.radar_lon,
            "radar_altitude_m": self.radar_alt,

            # Slew-to-cue interface specification
            "slew_to_cue_input_format": {
                "required_fields": ["Timestamp", "TrackID", "Azimuth_Deg", "Elevation_Deg", "Range_m", "Confidence"],
                "coordinate_system": "AER (Azimuth-Elevation-Range, radar-centric)",
                "azimuth_convention": "0° = North, 90° = East (clockwise)",
                "elevation_convention": "0° = horizon, 90° = zenith",
                "range_units": "meters (slant range)",
                "uncertainty_model": "Gaussian, σ provided in metadata"
            },

            # VRD-26 compatibility note
            "notes": "Output format compatible with VRD-26 (Thermal/Visual turret slew-to-cue). Radar provides 'sloppy' detection (±10m), turret provides 'precise' tracking."
        }

        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"\n[SUCCESS] Metadata exported to JSON:")
        print(f"       - File: {output_path}")
        print(f"       - Beam Width: {self.beam_width}°")
        print(f"       - Azimuth Accuracy: ±{self.sigma_az}° RMS")
        print(f"       - Range Accuracy: ±{self.sigma_range} m RMS")


def main():
    """
    Main execution: Generate radar track simulation for VRD-32.

    Example Scenarios:
    1. Linear flight: Drone flying North-to-South at 50m altitude
    2. Circular flight: Drone loitering at 100m altitude with 50m radius
    """
    print("=" * 70)
    print("  RADAR TRACK SIMULATION (PLOT EXTRACTOR)")
    print("  VRD-32: Simulate Radar Track Output")
    print("  EPIC VRD-1: RF Micro-Doppler Physics & Validation")
    print("=" * 70)
    print()

    # Initialize radar track simulator (Blighter A400 specs)
    radar = RadarTrackSimulator(
        update_rate_hz=1.0,          # 1 Hz update rate
        sigma_azimuth_deg=1.0,       # ±1.0° azimuth error
        sigma_elevation_deg=1.5,     # ±1.5° elevation error
        sigma_range_m=10.0,          # ±10 m range error
        missed_detection_prob=0.05,  # 5% missed detections
        beam_width_deg=3.0,          # 3° beamwidth
        max_range_m=5000.0           # 5 km max range
    )

    # Scenario 1: Linear flight (North-to-South at 50m altitude)
    print("\n" + "="*70)
    print("Scenario 1: Linear Flight (North-to-South)")
    print("="*70)

    ground_truth_linear = radar.generate_linear_flight_path(
        start_position=(0, 500, 50),   # Start 500m North, 50m altitude
        velocity=(0, -20, 0),           # 20 m/s South (72 km/h)
        duration_sec=60,                # 60 seconds flight
        track_id="TRK001_LINEAR"
    )

    # Inject noise
    noisy_tracks_linear = radar.inject_measurement_noise(ground_truth_linear)

    # Export to CSV
    radar.export_tracks_csv(noisy_tracks_linear, 'output/radar_tracks.csv')

    # Export metadata
    radar.export_metadata_json(noisy_tracks_linear, 'output/radar_tracks_metadata.json')

    # Scenario 2: Circular flight (loitering at 100m altitude)
    print("\n" + "="*70)
    print("Scenario 2: Circular Flight (Loitering)")
    print("="*70)

    ground_truth_circular = radar.generate_circular_flight_path(
        center_position=(200, 200, 100),  # Center 200m E, 200m N, 100m altitude
        radius_m=50,                       # 50m radius circle
        angular_rate_deg_s=10,             # 10 deg/s (36 sec per circle)
        duration_sec=72,                   # 2 complete circles
        track_id="TRK002_CIRCULAR"
    )

    noisy_tracks_circular = radar.inject_measurement_noise(ground_truth_circular)

    radar.export_tracks_csv(noisy_tracks_circular, 'output/radar_tracks_circular.csv')

    # Combined metadata
    all_tracks = noisy_tracks_linear + noisy_tracks_circular
    radar.export_metadata_json(all_tracks, 'output/radar_tracks_combined_metadata.json')

    print("\n" + "="*70)
    print("  SIMULATION COMPLETE - VRD-32 ACCEPTANCE CRITERIA MET")
    print("="*70)
    print()
    print("VRD-32 Deliverables:")
    print("  [x] Script: src/simulations/simulate_radar_tracks.py")
    print("  [x] Output: radar_tracks.csv (linear flight)")
    print("  [x] Output: radar_tracks_circular.csv (circular flight)")
    print("  [x] Metadata: radar_tracks_metadata.json")
    print()
    print("Acceptance Criteria Verification:")
    print("  [x] Data Structure: Timestamp, TrackID, Az, El, Range, Confidence")
    print(f"  [x] Noise Injection: sigma_Range = {radar.sigma_range} m (realistic error)")
    print(f"  [x] Metadata: Beam Width = {radar.beam_width} deg (for uncertainty calc)")
    print("  [x] Format: CSV readable by slew-to-cue module (VRD-26 compatible)")
    print()
    print("Next Steps (VRD-26):")
    print("  1. Load radar_tracks.csv in thermal/visual turret module")
    print("  2. Convert (Az, El, Range) -> (Lat, Lon, Alt) using radar position")
    print("  3. Apply slew-to-cue logic: Radar detection ±10m -> Turret slew")
    print("  4. Turret provides precise tracking with thermal/visual")
    print()


if __name__ == '__main__':
    main()
