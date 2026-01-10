#!/usr/bin/env python3
"""
Unit tests for Passive Radar Physics Model

Tests validate the mathematical accuracy of:
- Doppler shift calculations
- RCS modulation patterns
- Signal generation parameters

Author: Vigil Perception
Date: 2026-01-10
Version: 1.0
"""

import sys
import os
import numpy as np
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from simulate_radar import MicroDopplerPhysics, RadarSimulator


class TestMicroDopplerPhysics:
    """Test suite for physics calculations"""

    def setup_method(self):
        """Initialize physics engine for testing"""
        self.physics = MicroDopplerPhysics(carrier_frequency_hz=10e9)

    def test_doppler_shift_stationary_target(self):
        """Test: Stationary target should produce zero Doppler shift"""
        radial_velocity = 0.0  # m/s
        doppler_shift = self.physics.calculate_doppler_shift(radial_velocity)
        assert doppler_shift == 0.0, "Stationary target must have zero Doppler shift"

    def test_doppler_shift_approaching_target(self):
        """Test: Approaching target (V_tip = 100 m/s) should produce +6667 Hz"""
        radial_velocity = 100.0  # m/s (approaching)
        doppler_shift = self.physics.calculate_doppler_shift(radial_velocity)

        # Expected: f_d = (2 * 100 * 10e9) / 3e8 = 6666.67 Hz
        expected_doppler = 6666.67
        tolerance = 1.0  # 1 Hz tolerance

        assert abs(doppler_shift - expected_doppler) < tolerance, \
            f"Doppler shift error: expected {expected_doppler}, got {doppler_shift}"

    def test_doppler_shift_receding_target(self):
        """Test: Receding target should produce negative Doppler shift"""
        radial_velocity = -100.0  # m/s (receding)
        doppler_shift = self.physics.calculate_doppler_shift(radial_velocity)

        expected_doppler = -6666.67
        tolerance = 1.0

        assert abs(doppler_shift - expected_doppler) < tolerance, \
            "Receding target must produce negative Doppler shift"

    def test_blade_rcs_pattern_perpendicular(self):
        """Test: RCS is maximum when blade is perpendicular (θ = 0°)"""
        angle = 0.0  # radians
        rcs = self.physics.blade_rcs_pattern(angle)
        assert rcs == 1.0, "RCS must be 1.0 at θ = 0° (cos²(0) = 1)"

    def test_blade_rcs_pattern_edge_on(self):
        """Test: RCS is minimum when blade is edge-on (θ = 90°)"""
        angle = np.pi / 2  # radians (90°)
        rcs = self.physics.blade_rcs_pattern(angle)
        assert abs(rcs) < 1e-10, "RCS must be ~0 at θ = 90° (cos²(π/2) ≈ 0)"

    def test_radial_velocity_amplitude(self):
        """Test: Radial velocity should oscillate between ±V_tip"""
        rpm = 5000
        blade_radius = 0.191  # m
        time_array = np.linspace(0, 1, 1000)

        radial_vel = self.physics.radial_velocity_time_series(
            time_array, rpm, blade_radius
        )

        # Calculate expected V_tip
        angular_velocity = (rpm / 60.0) * 2 * np.pi  # rad/s
        v_tip_expected = angular_velocity * blade_radius  # ~100 m/s

        v_max = np.max(np.abs(radial_vel))
        tolerance = 1.0  # 1 m/s tolerance

        assert abs(v_max - v_tip_expected) < tolerance, \
            f"Max radial velocity error: expected {v_tip_expected}, got {v_max}"

    def test_radial_velocity_periodicity(self):
        """Test: Radial velocity should be periodic at rotor frequency"""
        rpm = 5000
        rotor_freq = rpm / 60.0  # Hz
        blade_radius = 0.191
        duration = 1.0
        sample_rate = 10000

        time_array = np.linspace(0, duration, int(sample_rate * duration))
        radial_vel = self.physics.radial_velocity_time_series(
            time_array, rpm, blade_radius
        )

        # Perform FFT to find dominant frequency
        fft = np.fft.fft(radial_vel)
        freqs = np.fft.fftfreq(len(time_array), 1/sample_rate)
        peak_idx = np.argmax(np.abs(fft[1:len(fft)//2])) + 1
        peak_freq = abs(freqs[peak_idx])

        tolerance = 1.0  # 1 Hz tolerance
        assert abs(peak_freq - rotor_freq) < tolerance, \
            f"Radial velocity periodicity error: expected {rotor_freq} Hz, got {peak_freq} Hz"


class TestRadarSimulator:
    """Test suite for radar simulator"""

    def setup_method(self):
        """Initialize radar simulator for testing"""
        self.radar = RadarSimulator(
            carrier_freq=10e9,
            sample_rate=20000,
            duration=1.0,
            rotor_rpm=5000,
            num_blades=4,
            blade_radius=0.191
        )

    def test_signal_generation_length(self):
        """Test: Generated signal should have correct number of samples"""
        signal = self.radar.generate_signal()
        expected_samples = int(self.radar.sample_rate * self.radar.duration)

        assert len(signal) == expected_samples, \
            f"Signal length mismatch: expected {expected_samples}, got {len(signal)}"

    def test_signal_is_complex(self):
        """Test: I/Q signal should be complex-valued"""
        signal = self.radar.generate_signal()
        assert np.iscomplexobj(signal), "Signal must be complex (I/Q format)"

    def test_signal_normalization(self):
        """Test: Signal should be normalized (max amplitude ≈ 1)"""
        signal = self.radar.generate_signal()
        max_amplitude = np.max(np.abs(signal))

        # Allow some headroom for noise (SNR = 20 dB)
        assert 0.8 < max_amplitude < 1.5, \
            f"Signal normalization error: max amplitude = {max_amplitude}"

    def test_spectrogram_computation(self):
        """Test: Spectrogram computation should produce expected dimensions"""
        self.radar.generate_signal()
        f, t, Zxx = self.radar.compute_spectrogram()

        assert len(f) > 0, "Frequency bins should be non-empty"
        assert len(t) > 0, "Time bins should be non-empty"
        assert Zxx.shape == (len(f), len(t)), "Spectrogram shape mismatch"

    def test_blade_flash_frequency(self):
        """Test: Blade flash frequency should be visible in spectrogram"""
        self.radar.generate_signal()
        f, t, Zxx = self.radar.compute_spectrogram()

        # Calculate expected blade flash frequency
        expected_flash_freq = (self.radar.rotor_rpm / 60.0) * 2 * self.radar.num_blades

        # Average spectrogram over time to get frequency profile
        power_spectrum = np.mean(np.abs(Zxx) ** 2, axis=1)

        # Find peak in positive frequencies
        positive_freq_idx = f > 0
        positive_freqs = f[positive_freq_idx]
        positive_power = power_spectrum[positive_freq_idx]

        peak_idx = np.argmax(positive_power)
        peak_freq = positive_freqs[peak_idx]

        tolerance = 10.0  # 10 Hz tolerance (broader due to STFT resolution)
        assert abs(peak_freq - expected_flash_freq) < tolerance, \
            f"Blade flash frequency error: expected {expected_flash_freq} Hz, got {peak_freq} Hz"


def run_tests():
    """Run all tests and print results"""
    import traceback

    print("=" * 70)
    print("  PASSIVE RADAR PHYSICS ACCURACY TESTS")
    print("=" * 70)
    print()

    test_classes = [TestMicroDopplerPhysics, TestRadarSimulator]
    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for test_class in test_classes:
        print(f"Running {test_class.__name__}...")
        test_instance = test_class()

        # Get all test methods
        test_methods = [m for m in dir(test_instance) if m.startswith('test_')]

        for method_name in test_methods:
            total_tests += 1
            try:
                # Run setup if exists
                if hasattr(test_instance, 'setup_method'):
                    test_instance.setup_method()

                # Run test
                method = getattr(test_instance, method_name)
                method()

                print(f"  [PASS] {method_name}")
                passed_tests += 1

            except AssertionError as e:
                print(f"  [FAIL] {method_name}: {str(e)}")
                failed_tests.append((test_class.__name__, method_name, str(e)))

            except Exception as e:
                print(f"  [ERROR] {method_name}: EXCEPTION - {str(e)}")
                traceback.print_exc()
                failed_tests.append((test_class.__name__, method_name, str(e)))

        print()

    # Print summary
    print("=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")
    print()

    if failed_tests:
        print("Failed tests:")
        for class_name, method_name, error_msg in failed_tests:
            print(f"  - {class_name}.{method_name}: {error_msg}")
        print()
        return 1
    else:
        print("[SUCCESS] All tests passed!")
        print()
        return 0


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
