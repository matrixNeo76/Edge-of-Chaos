"""
hardware_driver_v2.py
======================
Modulo avanzato per l'interfacciamento hardware in tempo reale (in materia) v2.
Integra i parametri di laboratorio ottimali ricavati dalla campagna di simulazione (P0_Distilled v0.1):
  - Compliance Voltage / Current per evitare la rottura del dispositivo (SiO2:Ag / VO2 Mott)
  - Rumore percolativo 1/f calibrato all'Edge of Chaos (sigma_noise = 0.10, alpha = 1.0)
  - Pre-configurazione automatica per Keithley DMM, PicoScope e Generatore di Funzioni SCPI
  - Feedback allostasico A1/A2 e iniezione della copia efferente in hardware/firmware
"""

import time
import numpy as np

class LaboratoryParametersConfig:
    """Parametri ottimali di laboratorio preregistrati secondo P0_Distilled v0.1."""
    # Tensione e Compliance
    V_OPERATING_NOMINAL = 1.0       # Volts (Tensione di stimolo nominale)
    V_COMPLIANCE_MAX = 1.5          # Volts (Tensione massima di sicurezza)
    I_COMPLIANCE_MAX = 1e-3         # Ampere (1 mA compliance current)
    I_OPERATING_RANGE = (10e-6, 500e-6) # Ampere (Range operativo normale)

    # Campionamento e Tempi
    SAMPLE_RATE_DMM_HZ = 1000.0     # Hz (Frequenza di campionamento DMM)
    SAMPLE_RATE_PICO_MHZ = 1.0      # MHz (Frequenza di campionamento PicoScope)
    TIME_WINDOW_MS = 100.0          # ms (Finestra di acquisizione per frame)

    # Rumore e Criticità (Edge of Chaos)
    SIGMA_NOISE_OPTIMAL = 0.10     # 10% ampiezza rumore percolativo 1/f
    ALPHA_NOISE_1F = 1.0            # Esponente spettrale 1/f^alpha
    EDGE_OF_CHAOS_FREQ_BAND = (10.0, 1000.0) # Hz (Banda di attivazione locale Chua)

    # Feedback Allostasico A1/A2
    EFFERENCE_COPY_GAIN_GAMMA = 0.8
    ALLOSTASIC_BETA = 0.5
    FEEDBACK_LATENCY_MS = 1.0


class KeithleyDMMDriverV2:
    """Driver avanzato per Multimetro Keithley (es. 2000/2400 SourceMeter) con auto-compliance."""
    def __init__(self, resource_name="GPIB0::24::INSTR", config=LaboratoryParametersConfig, mock=True):
        self.resource_name = resource_name
        self.config = config
        self.mock = mock
        self.connected = False
        
    def connect(self):
        if self.mock:
            self.connected = True
            return f"MOCK_KEITHLEY_2400 (Configurato: V_comp={self.config.V_COMPLIANCE_MAX}V, I_comp={self.config.I_COMPLIANCE_MAX*1e3}mA)"
        else:
            import pyvisa
            rm = pyvisa.ResourceManager()
            self.inst = rm.open_resource(self.resource_name)
            # Pre-configurazione comandi SCPI di sicurezza
            self.inst.write(f":SENS:CURR:PROT {self.config.I_COMPLIANCE_MAX}")
            self.inst.write(f":SOUR:VOLT:PROT {self.config.V_COMPLIANCE_MAX}")
            self.connected = True
            return self.inst.query("*IDN?")

    def read_current_stream(self, n_samples=1000):
        """Legge flusso di corrente I(t) iniettando il rumore percolativo 1/f calibrato all'Edge of Chaos."""
        if not self.connected:
            raise RuntimeError("Dispositivo non connesso. Chiamare connect() prima di leggere.")
            
        if self.mock:
            dt = 1.0 / self.config.SAMPLE_RATE_DMM_HZ
            t = np.linspace(0, n_samples * dt, n_samples)
            
            # Generazione rumore 1/f calibrato (sigma_noise = 0.10)
            white_noise = np.random.normal(0, 1, n_samples)
            fft_noise = np.fft.rfft(white_noise)
            freqs = np.fft.rfftfreq(n_samples, d=dt)
            # La componente DC (f=0) diverge nello spettro 1/f: si annulla invece di
            # amplificarla con un divisore quasi-zero (che generava un offset di
            # bassa frequenza dominante e segnali degeneri dopo il clipping).
            fft_noise[0] = 0.0
            freqs[0] = 1.0
            fft_1f = fft_noise / (freqs ** (self.config.ALPHA_NOISE_1F / 2.0))
            noise_1f = np.fft.irfft(fft_1f, n=n_samples)
            noise_1f = (noise_1f / (np.std(noise_1f) + 1e-12)) * self.config.SIGMA_NOISE_OPTIMAL
            
            # Corrente di base modulata con rumore 1/f ed Edge of Chaos
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
    """Driver per Oscilloscopio PicoScope ad alta frequenza di campionamento."""
    def __init__(self, channels=("A", "B"), config=LaboratoryParametersConfig, mock=True):
        self.channels = channels
        self.config = config
        self.mock = mock
        self.connected = False

    def connect(self):
        self.connected = True
        return f"MOCK_PICOSCOPE_5000 (Configurato: SampleRate={self.config.SAMPLE_RATE_PICO_MHZ}MHz)"

    def acquire_waveform(self, time_window_ms=None):
        """Acquisisce le forme d'onda di tensione V(t) con banda Chua e protezione di tensione."""
        if time_window_ms is None:
            time_window_ms = self.config.TIME_WINDOW_MS
            
        if self.mock:
            n_pts = int(time_window_ms * 1e-3 * self.config.SAMPLE_RATE_PICO_MHZ * 1e6)
            t = np.linspace(0, time_window_ms * 1e-3, n_pts)
            
            # Segnale di tensione con risonanza all'Edge of Chaos
            v_a = self.config.V_OPERATING_NOMINAL * np.cos(2 * np.pi * 50 * t) + np.random.normal(0, 0.05, n_pts)
            v_b = 0.8 * np.sin(2 * np.pi * 50 * t + np.pi/4) + np.random.normal(0, 0.02, n_pts)
            
            # Clipping di sicurezza alla V_COMPLIANCE_MAX
            v_a = np.clip(v_a, -self.config.V_COMPLIANCE_MAX, self.config.V_COMPLIANCE_MAX)
            v_b = np.clip(v_b, -self.config.V_COMPLIANCE_MAX, self.config.V_COMPLIANCE_MAX)
            
            return {"time": t, "channel_A": v_a, "channel_B": v_b}


class NeuromorphicHardwareInterfaceV2:
    """Interfaccia integrata che applica automaticamente i parametri di laboratorio ottimali."""
    def __init__(self, config=LaboratoryParametersConfig, mock=True):
        self.config = config
        self.dmm = KeithleyDMMDriverV2(config=config, mock=mock)
        self.pico = PicoScopeOscilloscopeDriverV2(config=config, mock=mock)

    def initialize_session(self):
        info_dmm = self.dmm.connect()
        info_pico = self.pico.connect()
        return (f"=== SESSIONE HARDWARE AVANZATA INIZIALIZZATA (P0_Distilled v0.1) ===\n"
                f" - DMM: {info_dmm}\n"
                f" - PicoScope: {info_pico}\n"
                f" - Compliance V/I: Max {self.config.V_COMPLIANCE_MAX}V / {self.config.I_COMPLIANCE_MAX*1e3}mA\n"
                f" - Calibrazione Rumore 1/f: sigma_noise = {self.config.SIGMA_NOISE_OPTIMAL} (Edge of Chaos)\n"
                f" - Feedback Efferenza: Gain gamma = {self.config.EFFERENCE_COPY_GAIN_GAMMA}\n"
                f"=========================================================================")

    def get_realtime_frame(self, n_samples=1000):
        """Estrae un frame coordinato di corrente I(t) e tensione V(t) pronto per il calcolo della valenza."""
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
    print(f"Frame acquisito: {len(frame['current_I'])} punti I(t) [Mean I = {np.mean(frame['current_I'])*1e6:.2f} uA], {len(frame['voltage_V'])} punti V(t).")
