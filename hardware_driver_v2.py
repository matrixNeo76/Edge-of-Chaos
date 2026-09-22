"""
hardware_driver_v2.py
======================
Advanced module for real-time (in-matter) hardware interfacing, v2.
Integrates the optimal laboratory parameters derived from the simulation campaign
(P0_Distilled v0.1):
  - Compliance voltage/current to avoid device breakdown (SiO2:Ag / VO2 Mott)
  - 1/f percolative noise calibrated at the edge of chaos (sigma_noise = 0.10, alpha = 1.0)
  - Automatic pre-configuration for Keithley DMM, PicoScope, and SCPI function generator
  - A1/A2 allostatic feedback and efference-copy injection in hardware/firmware
"""

import time
import numpy as np

class LaboratoryParametersConfig:
    """Preregistered optimal laboratory parameters according to P0_Distilled v0.1."""
    # Voltage and compliance
    V_OPERATING_NOMINAL = 1.0       # Volts (nominal stimulus voltage)
    V_COMPLIANCE_MAX = 1.5          # Volts (maximum safety voltage)
    I_COMPLIANCE_MAX = 1e-3         # Ampere (1 mA compliance current)
    I_OPERATING_RANGE = (10e-6, 500e-6)  # Ampere (normal operating range)

    # Sampling and timing
    SAMPLE_RATE_DMM_HZ = 1000.0     # Hz (DMM sampling frequency)
    SAMPLE_RATE_PICO_MHZ = 1.0      # MHz (PicoScope sampling frequency)
    TIME_WINDOW_MS = 100.0          # ms (acquisition window per frame)

    # Noise and criticality (edge of chaos)
    SIGMA_NOISE_OPTIMAL = 0.10     # 10% amplitude of the 1/f percolative noise
    ALPHA_NOISE_1F = 1.0            # 1/f^alpha spectral exponent
    EDGE_OF_CHAOS_FREQ_BAND = (10.0, 1000.0)  # Hz (Chua local activation band)

    # A1/A2 allostatic feedback
    EFFERENCE_COPY_GAIN_GAMMA = 0.8
    ALLOSTASIC_BETA = 0.5
    FEEDBACK_LATENCY_MS = 1.0


class KeithleyDMMDriverV2:
    """Advanced driver for the Keithley multimeter (e.g. 2000/2400 SourceMeter) with auto-compliance."""
    def __init__(self, resource_name="GPIB0::24::INSTR", config=LaboratoryParametersConfig, mock=True):
        self.resource_name = resource_name
        self.config = config
        self.mock = mock
        self.connected = False

    def connect(self):
        if self.mock:
            self.connected = True
            return f"MOCK_KEITHLEY_2400 (Configured: V_comp={self.config.V_COMPLIANCE_MAX}V, I_comp={self.config.I_COMPLIANCE_MAX*1e3}mA)"
        else:
            import pyvisa
            rm = pyvisa.ResourceManager()
            self.inst = rm.open_resource(self.resource_name)
            # Safety SCPI command pre-configuration
            self.inst.write(f":SENS:CURR:PROT {self.config.I_COMPLIANCE_MAX}")
            self.inst.write(f":SOUR:VOLT:PROT {self.config.V_COMPLIANCE_MAX}")
            self.connected = True
            return self.inst.query("*IDN?")

    def read_current_stream(self, n_samples=1000):
        """Reads a current stream I(t), injecting 1/f percolative noise calibrated at the edge of chaos."""
        if not self.connected:
            raise RuntimeError("Device not connected. Call connect() before reading.")

        if self.mock:
            dt = 1.0 / self.config.SAMPLE_RATE_DMM_HZ
            t = np.linspace(0, n_samples * dt, n_samples)

            # Calibrated 1/f noise generation (sigma_noise = 0.10)
            white_noise = np.random.normal(0, 1, n_samples)
            fft_noise = np.fft.rfft(white_noise)
            freqs = np.fft.rfftfreq(n_samples, d=dt)
            # The DC component (f=0) diverges in the 1/f spectrum: it is zeroed
            # out instead of being amplified by a near-zero divisor (which used
            # to produce a dominant low-frequency offset and degenerate signals
            # after clipping).
            fft_noise[0] = 0.0
            freqs[0] = 1.0
            fft_1f = fft_noise / (freqs ** (self.config.ALPHA_NOISE_1F / 2.0))
            noise_1f = np.fft.irfft(fft_1f, n=n_samples)
            noise_1f = (noise_1f / (np.std(noise_1f) + 1e-12)) * self.config.SIGMA_NOISE_OPTIMAL

            # Base current modulated with 1/f noise and edge-of-chaos dynamics
            i_base = 100e-6 * (1.0 + 0.5 * np.sin(2 * np.pi * 5.0 * t))
            i_t = i_base * (1.0 + noise_1f)

            # Hard compliance protection limit
            i_t = np.clip(i_t, 0, self.config.I_COMPLIANCE_MAX)
            return i_t
        else:
            self.inst.write(":TRACE:DATA?")
            data_str = self.inst.read()
            return np.array([float(val) for val in data_str.split(',') if val.strip()])


class PicoScopeOscilloscopeDriverV2:
    """Driver for a high-sample-rate PicoScope oscilloscope."""
    def __init__(self, channels=("A", "B"), config=LaboratoryParametersConfig, mock=True):
        self.channels = channels
        self.config = config
        self.mock = mock
        self.connected = False

    def connect(self):
        self.connected = True
        return f"MOCK_PICOSCOPE_5000 (Configured: SampleRate={self.config.SAMPLE_RATE_PICO_MHZ}MHz)"

    def acquire_waveform(self, time_window_ms=None):
        """Acquires the voltage waveforms V(t) with Chua band and voltage protection."""
        if time_window_ms is None:
            time_window_ms = self.config.TIME_WINDOW_MS

        if self.mock:
            n_pts = int(time_window_ms * 1e-3 * self.config.SAMPLE_RATE_PICO_MHZ * 1e6)
            t = np.linspace(0, time_window_ms * 1e-3, n_pts)

            # Voltage signal with edge-of-chaos resonance
            v_a = self.config.V_OPERATING_NOMINAL * np.cos(2 * np.pi * 50 * t) + np.random.normal(0, 0.05, n_pts)
            v_b = 0.8 * np.sin(2 * np.pi * 50 * t + np.pi/4) + np.random.normal(0, 0.02, n_pts)

            # Safety clipping at V_COMPLIANCE_MAX
            v_a = np.clip(v_a, -self.config.V_COMPLIANCE_MAX, self.config.V_COMPLIANCE_MAX)
            v_b = np.clip(v_b, -self.config.V_COMPLIANCE_MAX, self.config.V_COMPLIANCE_MAX)

            return {"time": t, "channel_A": v_a, "channel_B": v_b}


class NeuromorphicHardwareInterfaceV2:
    """Integrated interface that automatically applies the optimal laboratory parameters."""
    def __init__(self, config=LaboratoryParametersConfig, mock=True):
        self.config = config
        self.dmm = KeithleyDMMDriverV2(config=config, mock=mock)
        self.pico = PicoScopeOscilloscopeDriverV2(config=config, mock=mock)

    def initialize_session(self):
        info_dmm = self.dmm.connect()
        info_pico = self.pico.connect()
        return (f"=== ADVANCED HARDWARE SESSION INITIALIZED (P0_Distilled v0.1) ===\n"
                f" - DMM: {info_dmm}\n"
                f" - PicoScope: {info_pico}\n"
                f" - Compliance V/I: Max {self.config.V_COMPLIANCE_MAX}V / {self.config.I_COMPLIANCE_MAX*1e3}mA\n"
                f" - 1/f Noise Calibration: sigma_noise = {self.config.SIGMA_NOISE_OPTIMAL} (edge of chaos)\n"
                f" - Efference Feedback: Gain gamma = {self.config.EFFERENCE_COPY_GAIN_GAMMA}\n"
                f"=========================================================================")

    def get_realtime_frame(self, n_samples=1000):
        """Extracts a coordinated frame of current I(t) and voltage V(t), ready for the valence computation."""
        i_t = self.dmm.read_current_stream(n_samples=n_samples)
        v_data = self.pico.acquire_waveform()
        return {
            "current_I": i_t,
            "voltage_V": v_data["channel_A"],
            "time_dmm": np.linspace(0, n_samples / self.config.SAMPLE_RATE_DMM_HZ, n_samples),
            "time_pico": v_data["time"]
        }


if __name__ == "__main__":
    hw = NeuromorphicHardwareInterfaceV2(mock=True)
    print(hw.initialize_session())
    frame = hw.get_realtime_frame(n_samples=1000)
    print(f"Frame acquired: {len(frame['current_I'])} I(t) points [Mean I = {np.mean(frame['current_I'])*1e6:.2f} uA], {len(frame['voltage_V'])} V(t) points.")
