# Thermal LWIR Sensor Simulation

**JIRA Epic**: VRD-26 - Sensor Domain: Thermal Infrared (LWIR) & Night-Time Tracking Resilience
**TRL Level**: TRL-4 (Laboratory Validation)
**Status**: COMPLETE (18/18 Acceptance Criteria Met)

---

## Overview

This directory contains the complete thermal LWIR (Long-Wave Infrared, 8-14 micrometers) sensor simulation for the Veridical Perception counter-UAS system. The simulation models a FLIR Boson 640-class uncooled microbolometer, demonstrating all-weather tracking capability in degraded conditions (night, fog) where visual sensors fail.

### Key Capabilities

- **Physics-Based Simulation**: Stefan-Boltzmann blackbody radiation, Mie scattering fog attenuation
- **Radiometric Output**: 14-bit TIFF with temperature calibration (0.036 deg C/count)
- **All-Weather Performance**: 78x better CNR than visual in night, 9x better in fog
- **Slew-to-Cue Integration**: Coordinate transformation from radar tracks (VRD-32) to turret commands
- **Thermal Crossover Handling**: Metadata flag signals when to rely on radar during dawn/dusk

---

## Directory Structure

```
thermal-lwir/
├── README.md                           # This file
├── data/
│   └── raw/
│       └── thermal_flir/               # FLIR ADAS dataset (user download required)
├── docs/
│   ├── discovery/
│   │   └── THERMAL_DATASET_DISCOVERY.md    # Physics models, dataset audit
│   ├── specs/
│   │   ├── THERMAL_DATA_STANDARD.md        # ICD for 14-bit radiometric TIFF
│   │   └── THERMAL_PHYSICS.csv             # Temperature lookup table
│   └── evidence/
│       ├── VRD31_Night_Comparison.png      # Night validation (visual vs. thermal)
│       ├── VRD31_Fog_Comparison.png        # Fog validation (visual vs. thermal)
│       ├── VRD31_Validation_Summary.json   # CNR metrics
│       └── VRD26_EPIC_ACCEPTANCE_CRITERIA_VERIFICATION.md  # Full verification doc
├── src/
│   ├── simulations/
│   │   └── simulate_thermal.py         # Main thermal simulation script
│   ├── control/
│   │   └── slew_to_cue.py              # Radar-to-turret coordinate transformation
│   └── validation/
│       └── vrd31_all_weather_validation.py  # CNR validation (night + fog)
├── output/
│   ├── thermal_clear_night.tiff        # 16-bit radiometric TIFF (clear night)
│   ├── thermal_fog.tiff                # 16-bit radiometric TIFF (fog)
│   ├── search_pattern_1.png            # Spiral search visualization
│   └── turret_command_1.json           # Slew-to-cue command example
└── config/
    └── (reserved for future sensor parameters)
```

---

## Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install numpy matplotlib pillow scipy
```

### 0. Analyze FLIR ADAS Dataset (VRD-27)

**Verify Dataset Acquisition**:
```bash
cd sensor-data-prep/thermal-lwir
python src/validation/analyze_flir_dataset.py
```

**Output**:
- `output/FLIR_Dataset_Samples.png` (6 sample thermal images)
- `output/FLIR_Intensity_Distribution.png` (intensity histogram)
- `output/FLIR_Dataset_Analysis.json` (statistical summary)

**Verification**:
- Confirms 11,886 thermal frames acquired (far exceeds 100 frame requirement)
- Extracts intensity statistics from real thermal data
- Validates VRD-27 AC-1 acceptance criterion

---

### 1. Generate Thermal Imagery (VRD-29)

**Clear Night Scenario**:
```bash
cd sensor-data-prep/thermal-lwir
python src/simulations/simulate_thermal.py
```

**Output**:
- `output/thermal_clear_night.tiff` (16-bit TIFF, 640x512 pixels)
- `output/thermal_clear_night.json` (radiometric metadata)
- `output/thermal_clear_night_visualization.png` (colormap visualization)

**Fog Scenario**:
```bash
python src/simulations/simulate_thermal.py --fog --visibility 200
```

**Output**:
- `output/thermal_fog.tiff` (fog-attenuated thermal image)
- `output/thermal_fog.json` (fog attenuation parameters)

**Parameters**:
- `--fog`: Enable fog injection
- `--visibility <meters>`: Meteorological visibility (default: 100m)
- `--target-range <meters>`: Distance to target (default: 500m)
- `--output-dir <path>`: Output directory (default: output)

---

### 2. Slew-to-Cue Coordinate Transformation (VRD-30)

**Test Coordinate Transformations**:
```bash
python src/control/slew_to_cue.py
```

**Output**:
- `output/turret_command_1.json` (North target, 1km range)
- `output/turret_command_2.json` (East target, 500m range)
- `output/search_pattern_1.png` (spiral search visualization)
- `output/search_pattern_2.png`

**Verification**:
- North target (1km, 100m altitude): Az=0.00deg, El=5.71deg (error < 0.001deg)
- East target (500m, 50m altitude): Az=90.00deg, El=5.71deg (error < 0.001deg)

---

### 3. All-Weather Validation (VRD-31)

**Generate Visual vs. Thermal Comparisons**:
```bash
python src/validation/vrd31_all_weather_validation.py
```

**Output**:
- `output/VRD31_Night_Comparison.png` (side-by-side: visual black, thermal clear)
- `output/VRD31_Fog_Comparison.png` (side-by-side: visual grey noise, thermal visible)
- `output/VRD31_Validation_Summary.json` (CNR metrics)

**Results**:
- **Night**: Thermal CNR = 78.2x better than visual
- **Fog (200m)**: Thermal CNR = 9.0x better than visual

---

## Integration with Radar (VRD-32)

The thermal sensor receives slew-to-cue commands from the radar track output:

### Workflow

1. **Radar Output** (from `passive-radar` project):
   ```csv
   # radar_tracks.csv
   Timestamp,TrackID,Azimuth_Deg,Elevation_Deg,Range_m,Confidence
   2026-01-11T15:10:59Z,TRK001,45.2,12.8,850.0,0.92
   ```

2. **Slew-to-Cue Conversion**:
   ```python
   from slew_to_cue import SlewToCueController

   controller = SlewToCueController(
       turret_lat=37.7749,
       turret_lon=-122.4194,
       turret_alt_m=50.0
   )

   radar_track = {
       'latitude': 37.7840,
       'longitude': -122.4194,
       'altitude_m': 150.0,
       'uncertainty_m': 10.0
   }

   turret_cmd = controller.radar_track_to_turret_command(radar_track)
   # Output: {'pan_deg': 0.0, 'tilt_deg': 5.71, 'search_pattern': [...]}
   ```

3. **Thermal Acquisition**:
   - Turret slews to commanded Pan/Tilt angle
   - Executes spiral search pattern (±2 deg cone)
   - Detects hot spot (drone motor at 50 deg C)
   - Locks onto target for precision tracking

---

## Thermal Physics Models

### Blackbody Radiation

**Stefan-Boltzmann Law**:
```
P = epsilon * sigma * A * T^4
```

Where:
- epsilon = Emissivity (0.95 for drone motors)
- sigma = 5.67e-8 W/m^2/K^4
- T = Absolute temperature (Kelvin)

### Temperature Ranges (from THERMAL_PHYSICS.csv)

| Target | Temperature | Delta T (vs. Sky) | Detection |
|--------|-------------|-------------------|-----------|
| Drone Motor | 40-60 deg C | +40 deg C | EASY |
| Drone Battery | 30-45 deg C | +28 deg C | EASY |
| Bird Surface | 25-32 deg C | +18 deg C | MODERATE |
| Cold Sky | 0-10 deg C | Baseline | N/A |

### Fog Attenuation (LWIR Advantage)

**Beer-Lambert Law**:
```
I(d) = I_0 * exp(-beta * d)
```

**Extinction Coefficients**:
- Visible (0.55 micrometers): beta = 20-80 km^-1 (dense fog)
- LWIR (10 micrometers): beta = 5-20 km^-1 (4x lower attenuation)

**Implication**: Thermal sensors "see through" fog 4x better than visual cameras.

---

## Radiometric Data Format

### 16-bit TIFF Specification

**Bit Depth**: 14-bit valid data (0-16383 counts)
**File Format**: Uncompressed TIFF, single-channel grayscale
**Byte Order**: Little-endian

### Temperature Calibration

**Pixel to Temperature**:
```
T_celsius = Pixel_Value * 0.036 - 40.0
```

**Temperature to Pixel** (for simulation):
```
Pixel_Value = (T_celsius + 40.0) / 0.036
```

**Range**: -40 to +550 deg C

---

## Metadata Standard (JSON Sidecar)

Each thermal TIFF file has an accompanying JSON file with:

### Critical Fields

**Thermal Contrast Grade** (0.0 to 1.0):
```json
{
  "thermal_analysis": {
    "thermal_contrast_grade": 1.00,
    "delta_t_deg_c": 49.70
  }
}
```

**Interpretation**:
- `grade >= 0.8`: Excellent contrast, thermal is primary sensor
- `grade < 0.3`: Thermal crossover (dawn/dusk), rely on radar

**Slew-to-Cue Status**:
```json
{
  "slew_to_cue": {
    "slew_to_cue_active": true,
    "radar_azimuth_deg": 45.2,
    "turret_pan_deg": 45.5,
    "search_pattern_active": false
  }
}
```

---

## Dataset Acquisition (VRD-27)

### FLIR ADAS Thermal Dataset

**Source**: Kaggle
**URL**: https://www.kaggle.com/datasets/samdazel/teledyne-flir-adas-thermal-dataset-v2
**Size**: 26,000+ thermal/RGB image pairs
**License**: Free for research

### Download Instructions

```bash
# Install Kaggle CLI
pip install kaggle

# Configure API credentials (get from kaggle.com/account)
# Place kaggle.json in ~/.kaggle/ (Linux/Mac) or %USERPROFILE%\.kaggle\ (Windows)

# Download dataset
cd sensor-data-prep/thermal-lwir
kaggle datasets download -d samdazel/teledyne-flir-adas-thermal-dataset-v2

# Extract
unzip teledyne-flir-adas-thermal-dataset-v2.zip -d data/raw/thermal_flir/
```

**Expected Output**: 26,000+ TIFF files in `data/raw/thermal_flir/`

---

## Validation Results (VRD-31)

### Acceptance Criteria Summary

| Criteria | Target | Achieved | Status |
|----------|--------|----------|--------|
| Night CNR Ratio | >= 3x | 78.2x | ✅ PASS |
| Fog CNR Ratio | >= 3x | 9.0x | ✅ PASS |
| Coordinate Error | < ±5 pixels | < 0.001 deg | ✅ PASS |
| Hot Spot Temp | > 40 deg C | 52.7 deg C | ✅ PASS |
| Fog Penetration | Visible target | Delta T = 4.28 deg C | ✅ PASS |

### Visual Evidence

See `docs/evidence/VRD31_Night_Comparison.png` and `docs/evidence/VRD31_Fog_Comparison.png` for side-by-side comparisons showing thermal superiority in degraded conditions.

---

## References

### Primary Sources

1. **FLIR Boson Datasheet**: Teledyne FLIR Boson 640 Specifications
2. **MDPI Fog Attenuation**: https://www.mdpi.com/2076-3417/9/14/2843
3. **FLIR ADAS Dataset**: https://www.kaggle.com/datasets/samdazel/teledyne-flir-adas-thermal-dataset-v2
4. **LWIR Basics**: https://www.lightpath.com/blog/what-is-lwir-a-beginners-guide-to-long-wave-infrared-imaging

### Documentation

- **Discovery**: `docs/discovery/THERMAL_DATASET_DISCOVERY.md`
- **ICD Spec**: `docs/specs/THERMAL_DATA_STANDARD.md`
- **Verification**: `docs/evidence/VRD26_EPIC_ACCEPTANCE_CRITERIA_VERIFICATION.md`

---


