import serial, time

class TGA1240:

    Waveforms = [
        'SINE',
        'SQUARE',
        'TRIANG',
        'DC',
        'POSRPM',
        'NEGRPM',
        'COSINE',
        'HAVSIN',
        'HAVCOS',
        'SINC',
        'PULSE',
        'PULSTRN',
        'ARB',
        'SEQ'
    ]

    Channels = [ 1, 2 ]

    Units = ['VPP', 'VRMS', 'DBM']

    Loads = ['50', '600', 'OPEN']

    Filters = [ 'AUTO', 'EL10', 'EL16', 'BESS', 'NONE' ]

    BeepModes = [ 'ON', 'OFF', 'WARN', 'ERROR' ]

    HoldModes = [ 'ON', 'OFF', 'ENAB', 'DISAB' ]

    def __init__(self, port):
        self.port = port
        self.serial = serial.Serial(port, baudrate=9600, timeout=1)
        self.serial.flushInput() # On Python 3 "reset_input_buffer()"

    def scpi_comm(self, command):
        readline=''
        command += '\n'
        self.serial.write(str.encode(command))
        time.sleep(0.01)

        if command[-2] == '?':
            ch=''
            while ch != '\n':
                ch = self.serial.read(1).decode("CP1251")
                if ch == '':
                    break
                if ch != '\r' or ch != '\n':
                    readline += ch

        return readline

    def Reset(self):
        self.scpi_comm('*RST')
        time.sleep(5)

    def Local(self):
        self.scpi_comm('LOCAL')

    def Beep(self):
        self.scpi_comm('BEEP')

    def SetBeepMode(self, mode):
        if mode in self.BeepModes:
            self.scpi_comm('BEEPMODE ' + mode)

    def SetHoldMode(self, mode):
        if mode in self.HoldModes:
            self.scpi_comm('HOLD ' + mode)    

    def SetAmplitude(self, amplitude):
        self.scpi_comm('AMPL ' + str(amplitude))

    def SetOffset(self, offset):
        self.scpi_comm('DCOFFS ' + str(offset))

    def SetFrequency(self, freq):
        self.scpi_comm('WAVFREQ ' + str(freq))

    def SetPeriod(self, period):
        self.scpi_comm('WAVPER ' + str(period))

    def SetFilter(self, filter):
        if filter in self.Filters:
            self.scpi_comm('FILTER ' + filter)

    def SetWaveform(self, waveform):
        return_value = False
        if waveform in self.Waveforms:
            return_value = True
            self.scpi_comm('WAVE ' + waveform)
        return return_value

    def SelectChannel(self, channel):
        if channel in self.Channels:
            self.scpi_comm('SETUPCH ' + str(channel))

    def SetOutput(self, on=True):
        if on == True:
            self.scpi_comm('OUTPUT ON')
        else:
            self.scpi_comm('OUTPUT OFF')

    def SetAmplitudeUnit(self, unit):
        if unit in self.Units:
            self.scpi_comm('AMPUNIT ' + unit)

    def SetLoad(self, load):
        if load in self.Loads:
            self.scpi_comm('ZLOAD ' + load)

    def SetupChannel(self, channel, freq=160.0, ampl=1.0, offset=0.0, wform='SINE', unit='VPP'):
        self.SelectChannel(channel)
        self.SetFrequency(freq)
        self.SetAmplitudeUnit(unit)
        self.SetWaveform(wform)
        self.SetAmplitude(ampl)
        self.SetOffset(offset)
        self.SetOutput(True)
