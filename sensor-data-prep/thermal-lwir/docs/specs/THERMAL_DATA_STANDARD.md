# Thermal Data Specification (ICD - Interface Control Document)

**JIRA Task**: VRD-28 - Define Thermal Data Specification (ICD)
**Epic**: VRD-26 - Sensor Domain: Thermal Infrared (LWIR) & Night-Time Tracking Resilience
**Version**: 1.0
**Date**: 2026-01-11
**Status**: LOCKED

---

## 1. Executive Summary

This document defines the **Radiometric Thermal Data Standard** for the Veridical Perception sensor fusion system. Unlike standard 8-bit image formats (JPEG, PNG) which destroy temperature information through lossy compression, this specification mandates **16-bit grayscale format** with radiometric calibration to preserve absolute temperature measurements.

### Key Requirements

- **File Format**: 16-bit TIFF (uncompressed) or Raw Binary (Gray16)
- **Bit Depth**: 14-bit valid data (0-16383 counts), stored in 16-bit container
- **Radiometric Mapping**: Linear temperature calibration
- **Metadata**: JSON sidecar with thermal contrast grade and slew-to-cue status

---

## 2. File Format Specification

### 2.1 Primary Format: 16-bit TIFF (Radiometric)

**Format**: Tagged Image File Format (TIFF)
**Encoding**: Uncompressed, single-channel grayscale
**Bit Depth**: 16-bit unsigned integer (uint16)
**Byte Order**: Little-endian (Intel format)

#### TIFF Tags (Mandatory)

| Tag ID | Tag Name | Value | Description |
|--------|----------|-------|-------------|
| 256 | ImageWidth | Variable | Image width in pixels (e.g., 640) |
| 257 | ImageLength | Variable | Image height in pixels (e.g., 512) |
| 258 | BitsPerSample | 16 | 16 bits per pixel |
| 259 | Compression | 1 | No compression (raw data) |
| 262 | PhotometricInterpretation | 1 | BlackIsZero (0=cold, 65535=hot) |
| 273 | StripOffsets | Variable | Byte offset to image data |
| 277 | SamplesPerPixel | 1 | Single channel (grayscale) |
| 278 | RowsPerStrip | Variable | Typically full image height |
| 284 | PlanarConfiguration | 1 | Chunky format |
| 339 | SampleFormat | 1 | Unsigned integer |

#### File Naming Convention

```
thermal_<timestamp>_<sensor_id>_<scene_temp_range>.tiff
```

**Example**:
```
thermal_20260111T153045Z_BOSON640_N40_P60.tiff
```

Where:
- `timestamp`: ISO 8601 format (UTC)
- `sensor_id`: Sensor model identifier (e.g., BOSON640, HADRON640R)
- `scene_temp_range`: N40_P60 = -40 deg C to +60 deg C scene range

### 2.2 Alternative Format: Raw Binary (Gray16)

**Format**: Headerless raw binary
**Encoding**: 16-bit unsigned integers, row-major order
**Extension**: `.raw` or `.gray16`

#### Binary Structure

```
[Pixel(0,0)][Pixel(0,1)]...[Pixel(0,W-1)]
[Pixel(1,0)][Pixel(1,1)]...[Pixel(1,W-1)]
...
[Pixel(H-1,0)][Pixel(H-1,1)]...[Pixel(H-1,W-1)]
```

Where:
- Each pixel = 2 bytes (uint16, little-endian)
- Total file size = Width × Height × 2 bytes

**Required Companion File**: `<filename>.json` metadata (see Section 4)

---

## 3. Radiometric Calibration

### 3.1 Temperature Mapping (14-bit Dynamic Range)

The thermal sensor outputs **14-bit radiometric data** (0-16383 counts), representing absolute temperature after internal calibration.

#### Linear Calibration Formula

```
T_celsius = (Pixel_Value - Offset) * Scale_Factor
```

**Standard Calibration Parameters** (FLIR Boson 640):

| Parameter | Symbol | Value | Units |
|-----------|--------|-------|-------|
| **Minimum Scene Temp** | T_min | -40 | deg C |
| **Maximum Scene Temp** | T_max | +550 | deg C |
| **Valid Pixel Range** | [P_min, P_max] | [0, 16383] | counts |
| **Scale Factor** | k | 0.036 | deg C/count |
| **Offset** | b | -40 | deg C |

#### Calculation

```
T = Pixel_Value * 0.036 - 40
```

**Examples**:
- Pixel Value = 0 → T = -40 deg C
- Pixel Value = 8192 → T = 254.9 deg C
- Pixel Value = 16383 → T = 549.8 deg C

### 3.2 Inverse Mapping (Temperature to Pixel Value)

```
Pixel_Value = (T_celsius + 40) / 0.036
```

**Clamping**: Values outside [0, 16383] are clipped to valid range.

### 3.3 Alternative Calibration (User-Defined)

For custom scene temperature ranges, use:

```
Scale_Factor = (T_max - T_min) / 16383
Offset = T_min

T_celsius = Pixel_Value * Scale_Factor + Offset
```

**Example** (Narrow Range: 0-100 deg C):
- Scale Factor = (100 - 0) / 16383 = 0.0061 deg C/count
- Offset = 0 deg C
- Resolution = 0.0061 deg C (improved precision)

---

## 4. Metadata Standard (JSON Sidecar)

### 4.1 File Structure

Each thermal TIFF/raw file MUST have an accompanying JSON file with identical basename:

```
thermal_20260111T153045Z_BOSON640_N40_P60.tiff
thermal_20260111T153045Z_BOSON640_N40_P60.json  <- Metadata
```

### 4.2 Mandatory Fields

```json
{
  "format_version": "1.0",
  "sensor": {
    "model": "FLIR Boson 640",
    "type": "uncooled_microbolometer",
    "serial_number": "BOSON640-12345",
    "spectral_range_um": [8.0, 14.0],
    "resolution": {
      "width": 640,
      "height": 512
    },
    "pixel_pitch_um": 12.0,
    "netd_mk": 50.0,
    "frame_rate_hz": 60.0
  },
  "radiometric": {
    "bit_depth": 14,
    "scale_factor_deg_c_per_count": 0.036,
    "offset_deg_c": -40.0,
    "scene_temp_min_deg_c": -40.0,
    "scene_temp_max_deg_c": 550.0,
    "calibration_date": "2026-01-11T00:00:00Z",
    "calibration_method": "factory_blackbody"
  },
  "capture": {
    "timestamp": "2026-01-11T15:30:45.123456Z",
    "exposure_time_us": 8000,
    "gain_db": 0.0,
    "fpa_temperature_c": 25.3,
    "lens_focal_length_mm": 9.1,
    "f_number": 1.0
  },
  "environment": {
    "ambient_temp_c": 22.5,
    "humidity_percent": 45.0,
    "atmospheric_transmission": 0.98,
    "weather_condition": "clear",
    "visibility_m": 10000
  },
  "thermal_analysis": {
    "thermal_contrast_grade": 0.85,
    "max_target_temp_c": 48.2,
    "min_background_temp_c": 8.5,
    "delta_t_deg_c": 39.7,
    "snr_db": 28.5,
    "detection_confidence": 0.92
  },
  "slew_to_cue": {
    "slew_to_cue_active": true,
    "radar_cue_received": true,
    "radar_azimuth_deg": 45.2,
    "radar_elevation_deg": 12.8,
    "radar_range_m": 850.0,
    "turret_pan_deg": 45.5,
    "turret_tilt_deg": 13.1,
    "search_pattern_active": false
  },
  "targets": [
    {
      "target_id": "TGT001",
      "bbox": [245, 180, 280, 215],
      "centroid": [262, 197],
      "max_temp_c": 48.2,
      "mean_temp_c": 42.5,
      "classification": "drone_motor",
      "confidence": 0.89
    }
  ]
}
```

### 4.3 Field Definitions

#### 4.3.1 `thermal_contrast_grade` (Critical Field)

**Definition**: Quality metric for thermal detection reliability (0.0 to 1.0)

**Calculation**:
```python
delta_T = max_target_temp - min_background_temp

if delta_T < 5.0:
    grade = 0.0  # Below detection threshold
elif delta_T < 10.0:
    grade = (delta_T - 5.0) / 5.0  # Linear ramp 0.0 -> 1.0
else:
    grade = 1.0  # Excellent contrast
```

**Interpretation**:
- **grade >= 0.8**: Excellent thermal contrast, primary sensor
- **grade 0.5-0.8**: Good contrast, reliable detection
- **grade 0.3-0.5**: Marginal contrast, use with caution
- **grade < 0.3**: Poor contrast, **Thermal Crossover** event, rely on Radar

**Use Case**: During dawn/dusk thermal crossover, this flag signals the Fusion Engine to downweight thermal detections.

#### 4.3.2 `slew_to_cue_active` (Handshake Flag)

**Definition**: Boolean indicating whether the thermal camera is responding to a radar cue.

**State Machine**:
1. **false**: Thermal camera in autonomous scan mode
2. **true**: Thermal camera slaved to radar detection, performing localized search

**Workflow**:
```
Radar detects target at (Az=45deg, El=13deg, Range=850m)
  -> Sends cue to Thermal Turret
  -> Turret slews to (Pan=45deg, Tilt=13deg)
  -> slew_to_cue_active = true
  -> Thermal performs spiral search pattern
  -> Target acquired (hot spot detected)
  -> Thermal locks onto target
  -> Hands off to Visual camera for precision tracking
```

---

## 5. Data Quality Requirements

### 5.1 Radiometric Accuracy

| Specification | Requirement | Verification Method |
|---------------|-------------|---------------------|
| **Absolute Accuracy** | +/- 5 deg C or 5% of reading | Blackbody calibration |
| **Uniformity (FPA)** | < 2% RMS variation | Flat-field correction |
| **Temporal Stability** | < 1 deg C drift per hour | Shutter recalibration |
| **Linearity** | R^2 > 0.99 | Multi-point calibration |

### 5.2 Thermal Noise (NETD)

**Requirement**: NETD < 50 mK (Noise Equivalent Temperature Difference)

**Definition**: The temperature difference that produces SNR = 1

**Verification**:
```python
def calculate_netd(image, blackbody_temp):
    """
    Measure NETD from blackbody reference image.

    Args:
        image: 16-bit thermal image of uniform blackbody
        blackbody_temp: Known temperature (deg C)

    Returns:
        netd_mk: Noise equivalent temperature difference (mK)
    """
    mean_value = np.mean(image)
    std_value = np.std(image)

    # Convert pixel std to temperature std
    temp_std = std_value * scale_factor  # deg C
    netd_mk = temp_std * 1000  # Convert to mK

    return netd_mk
```

### 5.3 Bad Pixel Handling

**Requirement**: < 0.1% defective pixels (dead or hot pixels)

**Correction**: Apply bad pixel map (BPM) to replace defective pixels with median of neighbors.

---

## 6. Processing Pipeline

### 6.1 Raw to Calibrated Temperature

```python
import numpy as np
from PIL import Image

def load_thermal_tiff(filepath):
    """
    Load 16-bit thermal TIFF and convert to temperature map.

    Args:
        filepath: Path to thermal TIFF file

    Returns:
        temp_map: 2D array of temperatures (deg C)
    """
    # Load 16-bit TIFF
    img = Image.open(filepath)
    pixel_values = np.array(img, dtype=np.uint16)

    # Apply radiometric calibration
    scale_factor = 0.036  # deg C/count
    offset = -40.0        # deg C

    temp_map = pixel_values * scale_factor + offset

    return temp_map
```

### 6.2 Temperature to Pixel Value (Simulation)

```python
def temperature_to_pixel_value(temp_celsius):
    """
    Convert temperature to 14-bit pixel value.

    Args:
        temp_celsius: Temperature in deg C (scalar or array)

    Returns:
        pixel_value: 14-bit uint16 value (0-16383)
    """
    scale_factor = 0.036
    offset = -40.0

    pixel_value = (temp_celsius - offset) / scale_factor
    pixel_value = np.clip(pixel_value, 0, 16383).astype(np.uint16)

    return pixel_value
```

---

## 7. Thermal Contrast Grade Algorithm

### 7.1 Implementation

```python
def calculate_thermal_contrast_grade(image, target_mask, background_mask):
    """
    Calculate thermal contrast quality grade.

    Args:
        image: 2D temperature map (deg C)
        target_mask: Boolean mask for target pixels
        background_mask: Boolean mask for background pixels

    Returns:
        grade: Contrast quality (0.0 to 1.0)
        metrics: Dictionary of diagnostic metrics
    """
    # Extract temperatures
    target_temps = image[target_mask]
    background_temps = image[background_mask]

    # Calculate delta T
    max_target_temp = np.max(target_temps)
    mean_target_temp = np.mean(target_temps)
    min_background_temp = np.min(background_temps)
    mean_background_temp = np.mean(background_temps)

    delta_T = max_target_temp - min_background_temp

    # Calculate grade
    if delta_T < 5.0:
        grade = 0.0  # Below detection threshold
    elif delta_T < 10.0:
        grade = (delta_T - 5.0) / 5.0  # Linear ramp
    else:
        grade = 1.0  # Excellent contrast

    # Calculate SNR
    target_std = np.std(target_temps)
    background_std = np.std(background_temps)
    snr = delta_T / (target_std + background_std + 1e-6)
    snr_db = 10 * np.log10(snr + 1e-6)

    metrics = {
        'max_target_temp_c': max_target_temp,
        'mean_target_temp_c': mean_target_temp,
        'min_background_temp_c': min_background_temp,
        'mean_background_temp_c': mean_background_temp,
        'delta_t_deg_c': delta_T,
        'snr_db': snr_db,
        'thermal_contrast_grade': grade
    }

    return grade, metrics
```

---

## 8. Slew-to-Cue Interface Protocol

### 8.1 Data Flow

```
[Radar] ----(Cue Message)----> [Thermal Turret Controller]
           |
           v
    {
      "timestamp": "2026-01-11T15:30:45Z",
      "target_id": "TRK001",
      "latitude": 37.7749,
      "longitude": -122.4194,
      "altitude_m": 150.0,
      "azimuth_deg": 45.2,
      "elevation_deg": 12.8,
      "range_m": 850.0,
      "uncertainty_m": 10.0
    }
           |
           v
    [Coordinate Transform: Radar -> Turret]
           |
           v
    [Turret Slew Command: Pan=45.5deg, Tilt=13.1deg]
           |
           v
    [Thermal Search Pattern: Spiral scan ±2deg]
           |
           v
    [Hot Spot Detection: Target acquired]
           |
           v
    [Thermal Lock: Centroid tracking]
           |
           v
    [Visual Handoff: Precise pixel-level tracking]
```

### 8.2 Metadata Fields

**Required in JSON**:
- `slew_to_cue_active`: Boolean (true when responding to radar cue)
- `radar_cue_received`: Boolean (true if radar message received)
- `radar_azimuth_deg`: Radar-reported azimuth
- `radar_elevation_deg`: Radar-reported elevation
- `radar_range_m`: Radar-reported range
- `turret_pan_deg`: Actual turret pan angle
- `turret_tilt_deg`: Actual turret tilt angle
- `search_pattern_active`: Boolean (true during spiral search)

---

## 9. Storage and Archival

### 9.1 Disk Space Requirements

**Example**: FLIR Boson 640 @ 60 fps (uncompressed)

| Parameter | Value |
|-----------|-------|
| Resolution | 640 × 512 pixels |
| Bit Depth | 16-bit |
| Frame Size | 640 × 512 × 2 = 655,360 bytes = 640 KB |
| Frame Rate | 60 fps |
| Data Rate | 38.4 MB/s |
| 1 minute | 2.3 GB |
| 1 hour | 138 GB |

**Recommendation**: Use lossless compression (PNG 16-bit) for archival:
- Compression ratio: ~2:1 for thermal data
- Reduced storage: ~69 GB/hour

### 9.2 Compression Options

**Lossless** (Preserves radiometry):
- PNG 16-bit: Good compression, widely supported
- TIFF LZW: Moderate compression, TIFF-native
- HDF5: Scientific format, supports metadata

**Lossy** (NOT RECOMMENDED):
- JPEG: Destroys temperature data
- JPEG2000: Better than JPEG, but still lossy

---

## 10. VRD-28 Acceptance Criteria Verification

### AC-1: Artifact Created

**Requirement**: `docs/specs/THERMAL_DATA_STANDARD.md` exists

**Status**: ✅ COMPLETE (this document)

### AC-2: Radiometry Locked

**Requirement**: Conversion formula from Pixel_Value to Degrees_Celsius is documented

**Status**: ✅ COMPLETE (Section 3.1)

**Formula**:
```
T_celsius = Pixel_Value * 0.036 - 40.0
```

### AC-3: Handshake Defined

**Requirement**: JSON sidecar includes `slew_to_cue_active` status flag

**Status**: ✅ COMPLETE (Section 4.3.2)

**Implementation**: See JSON schema in Section 4.2

---

## 11. References

1. **FLIR Boson Datasheet**: Teledyne FLIR Boson 640 Specifications
2. **TIFF Specification**: Adobe TIFF 6.0 Standard
3. **Radiometric Calibration**: "Infrared Thermography" - Vollmer & Möllmann (2017)
4. **Blackbody Physics**: Planck's Law, Stefan-Boltzmann Law

---

## 12. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-11 | Veridical Sensor Team | Initial release |

---

**Document Status**: LOCKED
**Approval**: Ready for VRD-29 Implementation
**Next Task**: VRD-29 - Implement `simulate_thermal.py`
