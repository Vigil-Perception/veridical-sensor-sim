# FLIR ADAS Thermal Dataset

**Dataset**: Teledyne FLIR ADAS Thermal Dataset v2
**Source**: Kaggle
**URL**: https://www.kaggle.com/datasets/samdazel/teledyne-flir-adas-thermal-dataset-v2
**License**: Free for research and development purposes
**Status**: ✅ ACQUIRED (2026-01-11)

---

## Dataset Specifications (VERIFIED)

- **Thermal Images**: 11,886 (10,742 train + 1,144 val)
- **RGB Images**: 11,886 (paired with thermal)
- **Annotations**: 175,040 object bounding boxes (COCO JSON format)
  - 80 object categories (person, car, bike, dog, bird, etc.)
- **Image Format**: 8-bit JPEG (640x512 pixels)
  - Thermal: Grayscale, contrast-enhanced (NOT radiometric)
  - RGB: Color, aligned with thermal frames
- **Conditions**: Day and nighttime scenarios
- **Locations**: United States, England, France

**Important**: FLIR ADAS provides contrast-enhanced 8-bit images, not radiometric temperature data.
Our simulation uses physics-based 14-bit radiometric model for absolute temperature measurements.

---

## Download Instructions

### Method 1: Kaggle CLI (Recommended)

```bash
# Install Kaggle CLI
pip install kaggle

# Configure API credentials
# 1. Go to https://www.kaggle.com/account
# 2. Scroll to "API" section
# 3. Click "Create New API Token"
# 4. This downloads kaggle.json
# 5. Place kaggle.json in:
#    - Linux/Mac: ~/.kaggle/kaggle.json
#    - Windows: %USERPROFILE%\.kaggle\kaggle.json

# Download dataset
cd sensor-data-prep/thermal-lwir/data/raw/thermal_flir
kaggle datasets download -d samdazel/teledyne-flir-adas-thermal-dataset-v2

# Extract
unzip teledyne-flir-adas-thermal-dataset-v2.zip
```

### Method 2: Manual Download

1. Visit https://www.kaggle.com/datasets/samdazel/teledyne-flir-adas-thermal-dataset-v2
2. Click "Download" button (requires Kaggle account)
3. Extract ZIP file to this directory

---

## Expected Directory Structure After Download

```
thermal_flir/
├── README.md (this file)
├── train/
│   ├── thermal_8_bit/
│   │   ├── FLIR_00001.jpeg
│   │   ├── FLIR_00002.jpeg
│   │   └── ...
│   ├── RGB/
│   │   ├── FLIR_00001.jpg
│   │   └── ...
│   └── thermal_annotations.json
├── val/
│   └── (validation set)
└── video/
    └── (video sequences)
```

---

## File Formats

### Thermal Images

- **8-bit Version**: JPEG files in `thermal_8_bit/` folder
  - Lower dynamic range, suitable for visualization
  - Lossy compression (not ideal for radiometric analysis)

- **14-bit Version** (if available in full dataset):
  - TIFF format with radiometric calibration
  - Pixel values map to absolute temperature
  - Preferred for scientific analysis

### RGB Images

- Standard JPEG format
- Aligned with thermal images for sensor fusion research

### Annotations

- COCO JSON format
- Bounding boxes for objects in both thermal and RGB
- Categories: person, car, bicycle, dog, etc.

---

## Usage in VRD-27

This dataset serves as "ground truth" thermal imagery for validating our simulation:

1. **Temperature Statistics**: Analyze real hot spot signatures (vehicle engines, people)
2. **Contrast Levels**: Measure typical Delta T values in various conditions
3. **Fog/Night Performance**: Study thermal performance in degraded weather

### Example Python Code

```python
from PIL import Image
import numpy as np

# Load thermal image
thermal_path = 'train/thermal_8_bit/FLIR_00001.jpeg'
thermal_img = Image.open(thermal_path)
thermal_array = np.array(thermal_img)

# Analyze temperature distribution
print(f"Min pixel value: {thermal_array.min()}")
print(f"Max pixel value: {thermal_array.max()}")
print(f"Mean pixel value: {thermal_array.mean():.2f}")
```

---

## Citation

If using this dataset in publications, please cite:

```
@dataset{flir_adas_2020,
  title={Teledyne FLIR ADAS Thermal Dataset v2},
  author={Teledyne FLIR},
  year={2020},
  publisher={Kaggle},
  url={https://www.kaggle.com/datasets/samdazel/teledyne-flir-adas-thermal-dataset-v2}
}
```

---

## Notes

- **Dataset Size**: ~4-5 GB compressed, ~10 GB extracted
- **Git Ignore**: Thermal images are excluded from git repository (see `.gitignore`)
- **Local Copy**: Each developer must download their own copy
- **License**: Free for research, check Teledyne FLIR terms for commercial use

---

**Last Updated**: 2026-01-11
**JIRA**: VRD-27 (Dataset Acquisition)
