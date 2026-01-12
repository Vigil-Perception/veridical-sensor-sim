# Polarimetric Physics Specification: Stokes Vectors & Material Classification

**Project**: VERIDICAL Counter-UAS Sensor Fusion
**Epic**: VRD-6 - Sensor Domain: Polarimetric Classification & Material Veto Layer
**Ticket**: VRD-8 - Define Polarimetric Physics Specification
**Date**: 2026-01-12
**Version**: 1.0
**Status**: COMPLETE

---

## 1. Stokes Parameter Mathematics

### 1.1 Fundamental Equations

The Sony IMX250MZR Polarsens sensor captures four polarization states using a 2x2 pixel mosaic. The Stokes parameters are calculated as follows:

**Intensity Measurements**:
- I₀° = Intensity through 0° polarizer
- I₄₅° = Intensity through 45° polarizer
- I₉₀° = Intensity through 90° polarizer
- I₁₃₅° = Intensity through 135° polarizer

**Stokes Parameters**:
```
S₀ = I₀° + I₉₀°                    (Total Intensity)
S₁ = I₀° - I₉₀°                    (Horizontal/Vertical Polarization)
S₂ = I₄₅° - I₁₃₅°                  (±45° Diagonal Polarization)
```

### 1.2 Degree of Linear Polarization (DoLP)

**Formula**:
```
            ___________
           / 2     2
DoLP =  √  S₁  + S₂
        ─────────────
              S₀
```

**Expressed as percentage**:
```
DoLP% = 100 × sqrt(S₁² + S₂²) / S₀
```

**Range**: 0% (unpolarized) to 100% (fully linearly polarized)
**Typical outdoor values**: 1-15%

### 1.3 Angle of Linear Polarization (AoLP)

**Formula**:
```
           1        S₂
AoLP = ─── arctan(───)
       2        S₁
```

**Range**: 0° to 180°
**Usage**: False-color visualization (maps to Hue in HSV colorspace)

### 1.4 Polarization Demosaicing

The 2x2 pixel block produces one DoLP value per 4 pixels:

```
Input:  2448 x 2048 pixel Bayer-like mosaic
Output: 1224 x 1024 DoLP map (2x2 binning)
```

For full-resolution output, bilinear interpolation reconstructs missing polarization states.

---

## 2. Boresight Alignment Model

### 2.1 Geometry Definition

The Polarimetric sensor is physically separated from the Thermal sensor by a baseline distance. This creates a **parallax offset** that must be corrected.

**Coordinate Transformation**:
```
(u_polar, v_polar) = (u_thermal + dx, v_thermal + dy)
```

Where:
- `(u_thermal, v_thermal)` = Target pixel coordinates from Thermal sensor (VRD-26)
- `(dx, dy)` = Boresight offset in pixels
- `(u_polar, v_polar)` = Corrected target coordinates for Polarimetric sensor

### 2.2 Calibration Structure

**File**: `config/sensor_calibration.json`

```json
{
  "boresight_offset_pixels": {
    "dx": 50,
    "dy": -20
  },
  "baseline_separation_mm": 150.0,
  "focus_distance_m": "infinity",
  "sensor_intrinsics": {
    "polarimetric_resolution": [2448, 2048],
    "thermal_resolution": [640, 512],
    "polarimetric_fov_deg": [28.5, 23.7],
    "polarimetric_focal_length_mm": 25.0,
    "polarimetric_pixel_size_um": 3.45
  },
  "polarization_calibration": {
    "extinction_ratio_at_525nm": 300.0,
    "polarizer_angles_deg": [0, 45, 90, 135],
    "transmission_efficiency": 0.95
  },
  "operational_limits": {
    "min_ambient_lux": 200,
    "min_solar_elevation_deg": 15,
    "max_target_range_m": 2000
  }
}
```

### 2.3 TRL-4 Simplification

**Assumption**: Fixed infinity focus
- Parallax offset (dx, dy) is **constant** for all targets >500m
- No range-dependent parallax correction required for TRL-4 validation
- Future TRL-5 will implement stereo ranging using baseline geometry

---

## 3. Veto Function Specification

### 3.1 Input Structure

**Required Data**:
```python
{
  "roi_bounds": {
    "x_min": int,
    "x_max": int,
    "y_min": int,
    "y_max": int
  },
  "roi_offset": {
    "roi_center_x": int,
    "roi_center_y": int
  },
  "thermal_coordinates": {
    "u_thermal": int,
    "v_thermal": int
  }
}
```

### 3.2 Operation Logic

**Step 1: Apply Parallax Correction**
```python
u_polar = thermal_coordinates['u_thermal'] + boresight_offset['dx']
v_polar = thermal_coordinates['v_thermal'] + boresight_offset['dy']
```

**Step 2: Extract ROI**
```python
roi_dolp = dolp_map[
    roi_bounds['y_min']:roi_bounds['y_max'],
    roi_bounds['x_min']:roi_bounds['x_max']
]
```

**Step 3: Compute Target DoLP**
```python
# Use top 10% brightest pixels to isolate target from background
intensity_threshold = percentile(roi_intensity, 90)
target_mask = roi_intensity >= intensity_threshold
target_dolp_mean = mean(roi_dolp[target_mask])
background_dolp_mean = mean(roi_dolp[~target_mask])
contrast_ratio = target_dolp_mean / background_dolp_mean
```

**Step 4: Classification Decision Tree**
```python
if contrast_ratio < 2.0:
    classification = "UNKNOWN"
    confidence = "LOW"
    veto_decision = "INSUFFICIENT_CONTRAST"
elif target_dolp_mean > 10.0:
    classification = "DRONE"
    confidence = "HIGH"
    veto_decision = "CONFIRM"
elif target_dolp_mean >= 8.0:
    classification = "DRONE"
    confidence = "MEDIUM"
    veto_decision = "CONFIRM"
elif target_dolp_mean >= 5.0:
    classification = "UNKNOWN"
    confidence = "LOW"
    veto_decision = "REQUIRE_FUSION"
elif target_dolp_mean >= 3.0:
    classification = "BIRD"
    confidence = "MEDIUM"
    veto_decision = "REJECT"
else:
    classification = "BIRD"
    confidence = "HIGH"
    veto_decision = "REJECT"
```

### 3.3 Output Format

**Classification Object**:
```json
{
  "classification": "DRONE" | "BIRD" | "UNKNOWN",
  "confidence": "HIGH" | "MEDIUM" | "LOW",
  "veto_decision": "CONFIRM" | "REJECT" | "REQUIRE_FUSION" | "INSUFFICIENT_CONTRAST",
  "metrics": {
    "dolp_target_pct": float,
    "dolp_background_pct": float,
    "contrast_ratio": float
  },
  "global_coordinates": {
    "thermal_x": int,
    "thermal_y": int,
    "polarimetric_x": int,
    "polarimetric_y": int
  },
  "quality_flags": {
    "ambient_lux": float,
    "solar_elevation_deg": float,
    "quality_metric": "HIGH" | "MEDIUM" | "LOW"
  }
}
```

---

## 4. Material Classification Thresholds

### 4.1 DoLP-Based Discrimination Table

| DoLP Range | Material Category | Confidence | Veto Decision |
|------------|-------------------|------------|---------------|
| **>10%** | High-Specular (Man-Made) | HIGH | CONFIRM |
| **8-10%** | Medium-Specular (Man-Made) | MEDIUM | CONFIRM |
| **5-8%** | Ambiguous | LOW | REQUIRE_FUSION |
| **3-5%** | Diffuse (Biological) | MEDIUM | REJECT |
| **<3%** | Highly Diffuse (Biological) | HIGH | REJECT |

### 4.2 Contrast Ratio Requirement

**Minimum Contrast**: 2.0x (target DoLP / background DoLP)
- Below 2.0x → Flag as `INSUFFICIENT_CONTRAST`
- Defers to Thermal/Radar sensors for final decision

### 4.3 Physical Basis

**Man-Made Materials (Drones)**:
- Specular reflection from smooth plastic/metal surfaces
- Preserves incident polarization → High DoLP
- Examples: ABS plastic fuselage, carbon fiber, aluminum

**Biological Materials (Birds)**:
- Subsurface scattering in feathers/skin
- Depolarizes incident light → Low DoLP
- Examples: Bird plumage, tree foliage, grass

---

## 5. HDF5 Output Format (Hyper-Cube Structure)

### 5.1 Dataset Hierarchy

**File Structure**: `polarimetry_output.h5`

```
/intensity          (1224, 1024, uint16)  # S₀ total intensity
/dolp               (1224, 1024, float32) # Degree of Linear Polarization
/aolp               (1224, 1024, float32) # Angle of Linear Polarization (radians)
/S1                 (1224, 1024, float32) # Horizontal-Vertical polarization
/S2                 (1224, 1024, float32) # ±45° polarization
/metadata           (Group)
  ├─ acquisition_timestamp      (string)
  ├─ sensor_model               (string) "Sony_IMX250MZR"
  ├─ solar_elevation_deg        (float32)
  ├─ ambient_lux                (float32)
  ├─ quality_metric             (string) "HIGH"|"MEDIUM"|"LOW"
  ├─ boresight_offset           (int32, 2) [dx, dy]
  └─ roi_center                 (int32, 2) [u, v]
```

### 5.2 Alternative: Multi-Page TIFF

For simpler integration, data can be exported as multi-page TIFF:
```
Page 0: Intensity (S₀)
Page 1: DoLP
Page 2: AoLP
Page 3: S₁
Page 4: S₂
TIFF Tags: Metadata (JSON string in ImageDescription field)
```

### 5.3 JSON Sidecar (TRL-4 Implementation)

For TRL-4 validation, simplified JSON output is acceptable:
```json
{
  "timestamp": "2026-01-12T14:32:01.523Z",
  "sensor_model": "Sony_IMX250MZR",
  "classification": { ... },
  "dolp_statistics": {
    "target_mean": float,
    "target_std": float,
    "background_mean": float,
    "background_std": float,
    "contrast_ratio": float
  },
  "processing_metadata": {
    "roi_size": [width, height],
    "full_resolution": [2448, 2048],
    "computation_time_ms": float
  }
}
```

---

## 6. Environmental Constraint Handling

### 6.1 Quality Metric Calculation

**Input Parameters**:
- `ambient_lux`: Measured ambient illumination
- `solar_elevation_deg`: Sun angle above horizon
- `contrast_ratio`: Target DoLP / Background DoLP

**Logic**:
```python
def calculate_quality_metric(ambient_lux, solar_elevation_deg, contrast_ratio):
    if ambient_lux < 200 or solar_elevation_deg < 15 or contrast_ratio < 2.0:
        return "LOW"
    elif ambient_lux < 1000 or solar_elevation_deg < 30 or contrast_ratio < 3.0:
        return "MEDIUM"
    else:
        return "HIGH"
```

### 6.2 Automatic Sensor Handoff

When `quality_metric == "LOW"`:
- Polarimetric sensor loses veto authority
- Decision defers to Thermal (VRD-26) and Radar (VRD-1)
- System continues operating in degraded mode

---

## 7. Acceptance Criteria Verification

### VRD-8 Requirements

| AC # | Requirement | Status | Evidence |
|------|-------------|--------|----------|
| AC-1 | Math Defined (DoLP formula) | PASS | Section 1: DoLP = sqrt(S₁² + S₂²) / S₀ |
| AC-2 | Geometry Defined (Boresight) | PASS | Section 2: (u_polar, v_polar) transformation |
| AC-3 | Veto Logic Defined | PASS | Section 3: Classification decision tree |
| AC-4 | Output Format Defined (HDF5) | PASS | Section 5: HDF5 hyper-cube structure |
| AC-5 | Calibration Spec | PASS | Section 2.2: sensor_calibration.json |

---

## 8. Integration with Sensor Fusion Engine

### 8.1 Workflow Summary

1. **Thermal Cue** (VRD-26): Turret locks on heat signature → generates `turret_command_N.json`
2. **Parallax Correction** (VRD-33): Apply boresight offset (dx, dy)
3. **ROI Gating** (VRD-33): Extract 256x256 crop around corrected coordinates
4. **DoLP Calculation** (VRD-9): Compute Stokes parameters → DoLP map
5. **Material Classification** (VRD-8): Apply veto logic → decision
6. **Fusion Decision**: Combine Radar (motion) + Thermal (heat) + Polarimetry (material)

### 8.2 Decision Authority

**Polarimetric Veto Has Priority For**:
- **REJECT** decisions (biological clutter suppression)
- Prevents false alarms from birds that exhibit drone-like kinematics

**Radar/Thermal Have Priority For**:
- Low-light conditions (quality_metric: LOW)
- Ambiguous classifications (REQUIRE_FUSION)

