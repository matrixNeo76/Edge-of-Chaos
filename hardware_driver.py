"""
hardware_driver.py
===================
Modulo per l'interfacciamento hardware in tempo reale (in materia).
Simula e gestisce la connessione PyVISA / Serial / TCP con la strumentazione di laboratorio:
  - Keithley DMM (Digital Multimeter) per la lettura delle correnti I(t)
  - PicoScope / Oscilloscopio ad alta velocita' per le tensioni V(t)
  - Array memristivo / Reti percolative 2D/3D
"""

import time
import numpy as np

class KeithleyDMMDriver:
    """Driver per Multimetro Keithley (es. 2000/2400 SourceMeter) via PyVISA."""
    def __init__(self, resource_name="GPIB0::24::INSTR", mock=True):
        self.resource_name = resource_name
        self.mock = mock
        self.connected = False
        
    def connect(self):
        if self.mock:
            self.connected = True
            return "MOCK_KEITHLEY_2400_CONNECTED"
        else:
            # Import reale PyVISA se disponibile nel laboratorio
            import pyvisa
            rm = pyvisa.ResourceManager()
            self.inst = rm.open_resource(self.resource_name)
            self.connected = True
            return self.inst.query("*IDN?")

    def read_current_stream(self, n_samples=100, sample_rate_hz=1000):
        """Legge un flusso continuo di correnti I(t) dal substrato."""
        if not self.connected:
            raise RuntimeError("Dispositivo non connesso. Chiamare connect() prima di leggere.")
            
        if self.mock:
            # Simula flussi di corrente analogici con fluttuazioni 1/f
            dt = 1.0 / sample_rate_hz
            t = np.linspace(0, n_samples * dt, n_samples)
            i_t = 0.001 * (np.sin(2 * np.pi * 5 * t) + np.random.normal(0, 0.1, n_samples))
            return i_t
        else:
            # Comando SCPI Keithley per acquisizione bufferizzata
            self.inst.write(":TRACE:DATA?")
            data_str = self.inst.read()
            return np.array([float(val) for val in data_str.split(',') if val.strip()])


class PicoScopeOscilloscopeDriver:
    """Driver per Oscilloscopio PicoScope ad alta frequenza di campionamento."""
    def __init__(self, channels=("A", "B"), sample_rate_mhz=1.0, mock=True):
        self.channels = channels
        self.sample_rate_mhz = sample_rate_mhz
        self.mock = mock
        self.connected = False

    def connect(self):
        self.connected = True
        return "MOCK_PICOSCOPE_5000_CONNECTED"

    def acquire_waveform(self, time_window_ms=10.0):
        """Acquisisce le forme d'onda di tensione V(t) sui canali A e B."""
        if self.mock:
            n_pts = int(time_window_ms * 1e-3 * self.sample_rate_mhz * 1e6)
            t = np.linspace(0, time_window_ms * 1e-3, n_pts)
            v_a = 1.5 * np.cos(2 * np.pi * 50 * t) + np.random.normal(0, 0.05, n_pts)
            v_b = 0.8 * np.sin(2 * np.pi * 50 * t + np.pi/4) + np.random.normal(0, 0.02, n_pts)
            return {"time": t, "channel_A": v_a, "channel_B": v_b}


class NeuromorphicHardwareInterface:
    """Interfaccia integrata che collega l'hardware reale alla pipeline di valenza."""
    def __init__(self, mock=True):
        self.dmm = KeithleyDMMDriver(mock=mock)
        self.pico = PicoScopeOscilloscopeDriver(mock=mock)

    def initialize_session(self):
        info_dmm = self.dmm.connect()
        info_pico = self.pico.connect()
        return f"Sessione Hardware Inizializzata:\n - DMM: {info_dmm}\n - PicoScope: {info_pico}"

    def get_realtime_frame(self, n_samples=1000):
        """Estrae un frame coordinato di corrente I(t) e tensione V(t)."""
        i_t = self.dmm.read_current_stream(n_samples=n_samples)
        v_data = self.pico.acquire_waveform(time_window_ms=10.0)
        return {
            "current_I": i_t,
            "voltage_V": v_data["channel_A"],
            "time": v_data["time"]
        }


if __name__ == "__main__":
    hw = NeuromorphicHardwareInterface(mock=True)
    print(hw.initialize_session())
    frame = hw.get_realtime_frame(n_samples=500)
    print(f"Acquisiti {len(frame['current_I'])} punti di corrente I(t) e tensione V(t).")
