# RF Data Standard - Interface Control Document (ICD)

**JIRA Ticket**: VRD-3 - Define RF Data Interface Standard
**Document ID**: VRD-ICD-001
**Version**: 1.0
**Date**: 2026-01-10
**Status**: ✅ APPROVED

---

## 1. Purpose & Scope

This Interface Control Document (ICD) defines the **strict handshake** between the RF sensor layer and the Veridical Perception Fusion Engine. It ensures **hardware agnostic** operation, allowing any compliant X-band radar (KrakenSDR, Echodyne, USRP, or simulation) to feed the fusion pipeline.

### 1.1 Design Principles
1. **Hardware Agnosticism**: Any radar producing compliant I/Q can integrate
2. **Stare Mode Support**: Specifications optimized for micro-Doppler extraction
3. **Physics Fidelity**: Sampling rates must capture blade-tip kinematics
4. **Simplicity**: Minimal overhead, maximum compatibility

---

## 2. File Format Definition

### 2.1 Primary Format: Binary Complex64 (.bin)

**Format**: Interleaved I/Q pairs, 32-bit float per component
**Extension**: `.bin`
**MIME Type**: `application/octet-stream`

**Binary Structure**:
```
[I₀][Q₀][I₁][Q₁][I₂][Q₂]...[Iₙ][Qₙ]
 4B  4B  4B  4B  4B  4B      4B  4B
```

**Data Type**:
- **C/C++**: `float` (IEEE 754 binary32)
- **Python**: `numpy.float32`
- **Total per sample**: 8 bytes (4 + 4)

**Example Creation (Python)**:
```python
import numpy as np

# Generate I/Q samples (complex64)
iq_complex = np.random.randn(4500) + 1j * np.random.randn(4500)
iq_complex = iq_complex.astype(np.complex64)

# Convert to interleaved binary
iq_interleaved = np.empty(4500 * 2, dtype=np.float32)
iq_interleaved[0::2] = iq_complex.real  # I samples
iq_interleaved[1::2] = iq_complex.imag  # Q samples

# Write to .bin file
iq_interleaved.tofile('radar_capture.bin')
```

**Example Loading (Python)**:
```python
# Read binary file
iq_interleaved = np.fromfile('radar_capture.bin', dtype=np.float32)

# Deinterleave to complex
iq_complex = iq_interleaved[0::2] + 1j * iq_interleaved[1::2]
iq_complex = iq_complex.astype(np.complex64)
```

### 2.2 Alternative Format: NumPy Archive (.npy) - OPTIONAL

**Extension**: `.npy`
**Data Type**: `numpy.complex64`
**Advantage**: Self-describing header (includes shape, dtype)

**Usage**:
```python
# Save
np.save('radar_capture.npy', iq_complex)

# Load
iq_complex = np.load('radar_capture.npy')
assert iq_complex.dtype == np.complex64
```

**Recommendation**: Use `.npy` for prototyping, `.bin` for production integration.

---

## 3. Metadata Companion File (JSON Sidecar)

### 3.1 Required Structure

**Filename Convention**: Same base name as binary file
```
radar_capture_001.bin  ──┐
                         ├─ Paired files
radar_capture_001.json ──┘
```

**Mandatory Fields**:
```json
{
  "format_version": "1.0",
  "data_format": "binary_complex64",
  "center_frequency_hz": 10000000000,
  "sample_rate_hz": 30000,
  "num_samples": 4500,
  "dwell_time_ms": 150.0,
  "timestamp_utc": "2026-01-10T12:34:56.789Z",
  "normalization": "full_scale",
  "endianness": "little"
}
```

**Field Descriptions**:
| Field | Type | Description | Constraint |
|-------|------|-------------|------------|
| `format_version` | string | ICD version | Must be "1.0" |
| `data_format` | string | Binary encoding | "binary_complex64" or "numpy_complex64" |
| `center_frequency_hz` | integer | Radar carrier freq | Typically 10e9 (X-band) |
| `sample_rate_hz` | integer | Sampling rate | **≥30,000** (Stare Mode requirement) |
| `num_samples` | integer | Total I/Q samples | Must match file size ÷ 8 |
| `dwell_time_ms` | float | Observation duration | **≥150 ms** (Stare Mode requirement) |
| `timestamp_utc` | string | ISO 8601 timestamp | UTC timezone |
| `normalization` | string | Amplitude scaling | "full_scale" (±1.0) or "raw_adc" |
| `endianness` | string | Byte order | "little" or "big" |

**Optional Fields**:
```json
{
  "target_type": "Quadcopter|Bird|Unknown",
  "rotor_rpm": 5000,
  "range_m": 1200.5,
  "snr_db": 18.3,
  "hardware_source": "Simulation|KrakenSDR|Echodyne|USRP"
}
```

---

## 4. Physics-Driven Requirements

### 4.1 Sampling Rate Mandate: ≥30 kHz

**Requirement**: Sample rate **MUST** be ≥30 kHz for Stare Mode operation.

**Physics Justification**:
```
Blade Tip Velocity (DJI Phantom): V_tip = 100 m/s
X-band Frequency: f_c = 10 GHz
Max Doppler Shift: f_d_max = (2 × V_tip × f_c) / c = 6.67 kHz

Nyquist Requirement: f_s ≥ 2 × f_d_max = 13.34 kHz (minimum)
Harmonic Headroom: f_s ≥ 2 × (3 × f_d_max) ≈ 40 kHz (ideal)
Practical Compromise: f_s = 30 kHz (captures up to 15 kHz Doppler)
```

**Blade Flash Harmonics**:
```
Fundamental: 83 Hz (5000 RPM ÷ 60)
2nd Harmonic: 166 Hz (blade pairs)
3rd Harmonic: 249 Hz
...
10th Harmonic: 830 Hz
```
→ **30 kHz** captures all relevant harmonics with margin.

### 4.2 Dwell Time Mandate: ≥150 ms

**Requirement**: Observation window **MUST** be ≥150 ms for reliable m-D extraction.

**Rationale**:
```
Rotor Period (5000 RPM): T = 60 / 5000 = 12 ms
STFT Window Length: 256 samples @ 30 kHz = 8.5 ms
Minimum Cycles for Stability: ≥10 rotor cycles
Required Dwell: 10 × 12 ms = 120 ms (minimum)
Recommended: 150 ms (12.5 cycles with margin)
```

**STFT Resolution Trade-off**:
- Short dwell (50 ms): Poor frequency resolution, blurred blade flashes
- Long dwell (500 ms): Excessive, wastes bandwidth for hovering targets
- **Sweet spot (150 ms)**: Balances resolution and update rate

---

## 5. Data Normalization Standard

### 5.1 Full-Scale Normalization (Recommended)

**Range**: I and Q components normalized to [-1.0, +1.0]

**Formula**:
```python
def normalize_iq(iq_raw):
    """Normalize raw ADC counts to full-scale ±1.0."""
    max_amplitude = np.max(np.abs(iq_raw))
    iq_normalized = iq_raw / max_amplitude
    return iq_normalized.astype(np.complex64)
```

**Advantages**:
- Prevents overflow in fixed-point processing
- Hardware-agnostic (removes gain/ADC variations)
- Simplifies fusion engine logic

### 5.2 Raw ADC Mode (Legacy Hardware)

If hardware provides unnormalized ADC counts:

**Metadata Flag**:
```json
{
  "normalization": "raw_adc",
  "adc_bits": 16,
  "adc_full_scale": 32767
}
```

**Conversion by Fusion Engine**:
```python
if metadata['normalization'] == 'raw_adc':
    iq_normalized = iq_raw / metadata['adc_full_scale']
```

---

## 6. File Size Expectations

### 6.1 Stare Mode File Sizes

**Standard Capture** (30 kHz, 150 ms):
```
Samples: 30,000 Hz × 0.150 s = 4,500 samples
File Size: 4,500 samples × 8 bytes = 36,000 bytes (35.2 KB)
```

**With Metadata**:
```
Binary: 35.2 KB
JSON:   ~0.5 KB
Total:  ~35.7 KB per capture
```

**Storage Estimate**:
- 1,000 captures = ~36 MB
- 10,000 captures = ~360 MB
- 100,000 captures = ~3.6 GB

**Comparison to RDRD**:
- RDRD (40 kHz, 150 ms, complex128): 96 KB per file
- Our ICD (30 kHz, 150 ms, complex64): 35 KB per file
- **Reduction**: 63% smaller (due to lower sample rate + float32)

---

## 7. Schema Validation

### 7.1 Pre-Ingestion Checks

**Mandatory Validation Pipeline**:
```python
def validate_rf_data(bin_path, json_path):
    """Validate ICD compliance before fusion engine ingestion."""

    # 1. Check file pairing
    assert bin_path.with_suffix('.json') == json_path, "Filename mismatch"

    # 2. Load metadata
    with open(json_path) as f:
        meta = json.load(f)

    # 3. Validate sample rate
    assert meta['sample_rate_hz'] >= 30000, \
        f"Sample rate {meta['sample_rate_hz']} < 30 kHz minimum"

    # 4. Validate dwell time
    assert meta['dwell_time_ms'] >= 150.0, \
        f"Dwell time {meta['dwell_time_ms']} < 150 ms minimum"

    # 5. Load binary data
    iq_data = np.fromfile(bin_path, dtype=np.float32)
    iq_complex = iq_data[0::2] + 1j * iq_data[1::2]

    # 6. Check sample count consistency
    assert len(iq_complex) == meta['num_samples'], \
        "Sample count mismatch between .bin and .json"

    # 7. Check normalization
    if meta['normalization'] == 'full_scale':
        assert np.max(np.abs(iq_complex)) <= 1.0, "Amplitude exceeds ±1.0"

    # 8. Check for invalid samples
    assert not np.any(np.isnan(iq_complex)), "NaN detected"
    assert not np.any(np.isinf(iq_complex)), "Inf detected"

    return iq_complex.astype(np.complex64), meta
```

### 7.2 Error Codes

| **Code** | **Condition** | **Action** |
|----------|---------------|------------|
| `ICD_ERR_001` | Sample rate < 30 kHz | REJECT |
| `ICD_ERR_002` | Dwell time < 150 ms | REJECT |
| `ICD_ERR_003` | File size mismatch | REJECT |
| `ICD_ERR_004` | NaN/Inf detected | REJECT |
| `ICD_ERR_005` | Amplitude > 1.0 (if full_scale) | WARN + clip |
| `ICD_ERR_006` | Missing metadata file | REJECT |

---

## 8. Hardware Integration Examples

### 8.1 From KrakenSDR (int16 native)

```python
def convert_krakensdr_to_icd(raw_int16):
    """Convert KrakenSDR int16 I/Q to ICD-compliant binary."""
    # Deinterleave
    i_raw = raw_int16[0::2].astype(np.float32)
    q_raw = raw_int16[1::2].astype(np.float32)

    # Combine to complex
    iq_complex = i_raw + 1j * q_raw

    # Normalize to ±1.0 (int16 range: -32768 to +32767)
    iq_normalized = iq_complex / 32768.0

    # Convert to complex64
    return iq_normalized.astype(np.complex64)
```

### 8.2 From USRP (GNU Radio complex64 native)

```python
def convert_usrp_to_icd(usrp_complex64):
    """USRP already outputs complex64 - just normalize."""
    max_amp = np.max(np.abs(usrp_complex64))
    return (usrp_complex64 / max_amp).astype(np.complex64)
```

### 8.3 From MATLAB (RDRD dataset)

```python
def convert_rdrd_to_icd(mat_filepath):
    """Convert RDRD .mat file to ICD-compliant .bin + .json."""
    import scipy.io as sio

    # Load MATLAB file
    data = sio.loadmat(mat_filepath)
    iq_raw = data['iq_data'].flatten()
    fs = float(data['sample_rate'][0, 0])
    fc = float(data['center_freq'][0, 0])

    # Normalize
    iq_normalized = (iq_raw / np.max(np.abs(iq_raw))).astype(np.complex64)

    # Resample if needed (RDRD is 40 kHz, we want 30 kHz)
    if fs != 30000:
        from scipy.signal import resample
        num_samples_new = int(len(iq_normalized) * 30000 / fs)
        iq_resampled = resample(iq_normalized, num_samples_new)
    else:
        iq_resampled = iq_normalized

    # Interleave for binary export
    iq_interleaved = np.empty(len(iq_resampled) * 2, dtype=np.float32)
    iq_interleaved[0::2] = iq_resampled.real
    iq_interleaved[1::2] = iq_resampled.imag

    # Write binary
    iq_interleaved.tofile('rdrd_converted.bin')

    # Write metadata
    metadata = {
        "format_version": "1.0",
        "data_format": "binary_complex64",
        "center_frequency_hz": int(fc),
        "sample_rate_hz": 30000,
        "num_samples": len(iq_resampled),
        "dwell_time_ms": len(iq_resampled) / 30.0,  # ms
        "timestamp_utc": "2026-01-10T00:00:00Z",  # Placeholder
        "normalization": "full_scale",
        "endianness": "little",
        "source": "RDRD_converted"
    }

    with open('rdrd_converted.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    return iq_resampled, metadata
```

---

## 9. Acceptance Criteria Verification (VRD-3)

### 9.1 Artifact Created
✅ **Status**: This document (`docs/specs/RF_DATA_STANDARD.md`) exists

### 9.2 Schema Defined
✅ **Binary Structure**: Interleaved float32 I/Q pairs documented
✅ **JSON Metadata**: All mandatory fields specified with constraints

### 9.3 Physics Check
✅ **Sampling Rate**: Explicitly mandates ≥30 kHz (Section 4.1)
✅ **Rationale**: Nyquist requirement for X-band blade-tip Doppler derived from first principles

---

## 10. Summary & Recommendations

### 10.1 Key Takeaways
1. **Format**: Binary complex64 (.bin) with JSON sidecar
2. **Sample Rate**: ≥30 kHz (non-negotiable for Stare Mode)
3. **Dwell Time**: ≥150 ms (captures 12.5 rotor cycles @ 5000 RPM)
4. **Normalization**: ±1.0 full-scale recommended
5. **File Size**: ~35 KB per 150 ms capture

### 10.2 For VRD-4 Implementation
- Update `simulate_radar.py` to export `.bin` format
- Change default sample rate from 20 kHz → 30 kHz
- Change default dwell from 1.0 s → 0.15 s (150 ms)
- Generate JSON metadata companion file
- Add ICD validation function

### 10.3 For VRD-5 Validation
- Convert RDRD .mat files to ICD format using Section 8.3 script
- Verify sample rate conversion (40 kHz → 30 kHz) doesn't degrade signatures
- Ensure normalized comparison (RDRD raw ADC → ±1.0)

---

## 11. Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-10 | Initial ICD release for VRD-3 |

---

**Document Owner**: Veridical Perception - Sensor Team
**Review Cycle**: After VRD-4/VRD-5 completion
**Status**: ✅ **APPROVED FOR IMPLEMENTATION**

---

**END OF ICD**
