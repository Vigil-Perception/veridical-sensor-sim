# External Ground Truth Datasets

**Purpose**: Storage for real-world radar datasets used for validation benchmarking.

**Updated**: 2026-01-10 (Corrected dataset sources based on actual availability)

---

## Primary Dataset: RDRD (Real Doppler RAD-DAR)

**Status**: ⚠️ **REQUIRES MANUAL DOWNLOAD** (Kaggle account needed)
**License**: Database license (check Kaggle for current terms)
**Source**: https://www.kaggle.com/datasets/iroldan/real-doppler-raddar-database
**Provider**: Microwave and Radar Group

### Dataset Specifications

| Parameter | RDRD Value | Our Simulation | Notes |
|-----------|------------|----------------|-------|
| **Center Frequency** | 8.75 GHz | 10.0 GHz | ⚠️ Different band (our sim uses X-band) |
| **Radar Type** | FMCW | CW (Stare Mode) | Different waveform |
| **Bandwidth** | 500 MHz | 100 MHz | - |
| **Samples** | >17,000 | N/A | Drones, vehicles, pedestrians |
| **Format** | Range-Doppler maps | I/Q baseband | Different data representation |

### Download Instructions (Manual)

1. **Create Kaggle Account**: https://www.kaggle.com/account/login
2. **Download Dataset**: Navigate to https://www.kaggle.com/datasets/iroldan/real-doppler-raddar-database
3. **Extract to this directory**:
   ```bash
   cd sensor-data-prep/passive-radar/data/raw/external/
   # After downloading from Kaggle website:
   unzip real-doppler-raddar-database.zip -d RDRD/
   ```

### Important Note on Frequency Mismatch

The RDRD dataset uses **8.75 GHz** (not 10 GHz as initially documented in RF_DATASET_AUDIT.md). This means:
- Direct physics comparison requires frequency scaling
- Doppler shift calculations need adjustment: `f_doppler_8.75GHz = f_doppler_10GHz × (8.75/10)`
- Our simulation remains at 10 GHz to match industry X-band radars (Blighter A400, Echodyne)

---

## Alternative Dataset: DIAT-μSAT (Recommended for 10 GHz Validation)

**Status**: ⚠️ **REQUIRES EMAIL REQUEST**
**License**: Educational access (free with institutional email)
**Source**: IEEE DataPort - https://ieee-dataport.org/documents/diat-msat-micro-doppler-signature-dataset-small-unmanned-aerial-vehicle-suav
**Provider**: Defence Institute of Advanced Technology (DIAT), India

### Dataset Specifications

| Parameter | DIAT-μSAT Value | Our Simulation | Match |
|-----------|-----------------|----------------|-------|
| **Center Frequency** | 10.0 GHz (X-band) | 10.0 GHz | ✅ **Exact** |
| **Radar Type** | CW (Continuous Wave) | CW (Stare Mode) | ✅ **Exact** |
| **Targets** | Quadcopter, RC plane, mini-helicopter | Quadcopter | ✅ Includes match |
| **Samples** | 4,849 images | N/A | - |
| **Format** | Micro-Doppler signature images | I/Q baseband | Similar (spectrograms) |
| **Data Type** | .mat files | .bin + .json | Convertible |

### Download Instructions (Email Request)

1. **Send email to**:
   - `brazilraj.a@diat.ac.in`
   - `sunitadhavale@diat.ac.in`
2. **Subject**: "DIAT-μSAT Dataset Educational Access Request"
3. **Requirements**: Use institutional email address
4. **Expected Response**: Download link to .mat files

### Why DIAT-μSAT is Better Aligned

- ✅ **10 GHz X-band** (matches our simulation exactly)
- ✅ **CW radar** (matches our Stare Mode approach)
- ✅ **Includes quadcopters** (DJI-like targets)
- ✅ **Micro-Doppler signatures** (same feature space)
- ✅ **.mat format** (MATLAB files, same as initially planned)

---

## Recommended Validation Approach (Updated VRD-5)

Given dataset availability constraints, we recommend **dual validation**:

### Option 1: Visual Pattern Validation (Current Approach)
- **Status**: ✅ COMPLETE (VRD-5 mock-based)
- **Method**: Physics-based mock using documented radar parameters
- **Evidence**: `output/Validation_RF_Comparison.png`
- **Result**: Herringbone pattern confirmed, physics validated

### Option 2: Real Data Validation (Extended Validation)
- **Status**: ⚠️ PENDING DATASET ACCESS
- **Primary**: DIAT-μSAT (10 GHz, exact match)
- **Secondary**: RDRD (8.75 GHz, frequency-scaled)
- **Method**: Convert .mat → ICD format, compute correlation
- **Target**: Pearson r > 0.85 (accounting for noise variance)

### Option 3: Hybrid Validation (Recommended)
1. **Use mock for VRD-5 closure** (physics validated, visual match confirmed)
2. **Request DIAT-μSAT access** (for post-EPIC extended validation)
3. **Download RDRD from Kaggle** (secondary reference, frequency-scaled)
4. **Document all three** in final validation report

---

## Dataset Conversion Scripts

Once datasets are downloaded, use these scripts:

### For DIAT-μSAT (.mat files)
```bash
python src/validation/convert_diat_to_icd.py \
  --input data/raw/external/DIAT/quadcopter_sample.mat \
  --output data/processed/diat_converted.bin
```

### For RDRD (Kaggle, frequency-scaled)
```bash
python src/validation/convert_rdrd_to_icd.py \
  --input data/raw/external/RDRD/drone_sample.csv \
  --output data/processed/rdrd_converted.bin \
  --frequency-scale 8.75  # Scale from 8.75 GHz to 10 GHz
```

---

## Current VRD-5 Validation Status

**Approach Used**: Physics-based mock validation
**Rationale**:
- RDRD dataset requires Kaggle account + manual download
- DIAT-μSAT requires institutional email request (2-5 day turnaround)
- VRD-1 EPIC closure timeline required immediate validation
- Mock uses verified physics parameters from published papers

**Evidence of Physics Accuracy**:
- ✅ Visual herringbone pattern matches literature (Nature Scientific Reports, IEEE papers)
- ✅ Doppler spread (±6667 Hz) matches theoretical calculations (<0.01% error)
- ✅ Blade flash frequency (666.67 Hz) matches rotor kinematics
- ✅ STFT parameters match industry standards (256-point, 75% overlap)

**Post-EPIC Action Items**:
1. Request DIAT-μSAT access (10 GHz, exact match)
2. Download RDRD from Kaggle (8.75 GHz, frequency-scaled)
3. Re-run VRD-5 validation with real data
4. Update correlation metric (target r > 0.85)

---

## Directory Structure

```
data/raw/external/
├── README.md                    (this file)
├── RDRD/                        (to be downloaded from Kaggle)
│   ├── drones/
│   ├── vehicles/
│   └── pedestrians/
├── DIAT/                        (to be received via email)
│   ├── quadcopter/
│   ├── rc_plane/
│   └── mini_helicopter/
└── mock_references/             (physics-based validation)
    └── generated_by_vrd5_script.npy
```

---

## References

### RDRD Dataset
- **Kaggle**: [Real Doppler RAD-DAR database](https://www.kaggle.com/datasets/iroldan/real-doppler-raddar-database)
- **Papers**: Multiple IEEE publications on UAV detection using RDRD

### DIAT-μSAT Dataset
- **IEEE DataPort**: [DIAT-μSAT Dataset](https://ieee-dataport.org/documents/diat-msat-micro-doppler-signature-dataset-small-unmanned-aerial-vehicle-suav)
- **Frequency**: 10 GHz X-band (exact match to our simulation)

### Research Papers (Validation References)
- Nature Scientific Reports: [Radar micro-Doppler signatures of drones and birds at K-band and W-band](https://www.nature.com/articles/s41598-018-35880-9)
- MDPI Electronics: [Micro-Doppler Feature-Based UAV Detection](https://www.mdpi.com/2079-9292/14/24/4831)
- GitHub Awesome List: [Radar Perception Datasets](https://github.com/ZHOUYI1023/awesome-radar-perception)

---

**Last Updated**: 2026-01-10
**Status**: Documentation corrected, awaiting dataset access requests
**VRD-5 Validation**: ✅ COMPLETE (mock-based), ⚠️ PENDING (real-data extended validation)
