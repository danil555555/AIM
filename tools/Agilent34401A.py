import serial, time, math

class Agilent34401A:

    MeasurementFunctions = [
        'VOLT:DC',
        'VOLT:DC:RATIO',
        'VOLT:AC',
        'CURR:DC',
        'CURR:AC',
        'RES',
        'FRESISTANCE',
        'FREQUENCY',
        'PERIOD',
        'CONTINUITY',
        'DIODE'
    ]

#------------------------------------------------------------------------------
    def __init__(self, port):
        self.port = port
        self.serial = serial.Serial(port,
                                    baudrate=9600,
                                    parity=serial.PARITY_NONE, 
                                    stopbits=serial.STOPBITS_ONE,
#                                    xonxoff=True,
                                    timeout=2
        )
        self.serial.flushInput() # On Python 3 "reset_input_buffer()"
        self.Remote()
        self.ClearStatus()

#------------------------------------------------------------------------------
    def scpi_comm(self, command):
        readline=''
        command += '\n'
        self.serial.write(str.encode(command))

        if command[-2] == '?':
            time.sleep(0.01)
            ch=''
            while ch != '\n': 
                ch = self.serial.read(1).decode("ASCII")
                if ch == '':
                    break
                if ch != '\r' or ch != '\n':
                    readline += ch

        return readline

#------------------------------------------------------------------------------
    def Remote(self):
        self.scpi_comm("SYST:REM")

#------------------------------------------------------------------------------          
    def ClearStatus(self):
        self.scpi_comm("*CLS")

#------------------------------------------------------------------------------
    def SetMeasurementFunction(self, function):
        return_value = False
        if function in self.MeasurementFunctions:
            return_value = True
            function_string = "FUNCTION " + "\"" + function + "\""
            self.scpi_comm(function_string)
            time.sleep(1)
        return(return_value)

#------------------------------------------------------------------------------
    def SetAutoRange(self, function, state=True):
        return_value = False
        if function in self.MeasurementFunctions:
            return_value = True
            auto_range_string = function + ":RANG:AUTO "
            if state == True:
                auto_range_string += "ON"
            else:
                auto_range_string += "OFF"
            self.scpi_comm(auto_range_string)
            time.sleep(1)
        return(return_value)

#------------------------------------------------------------------------------
    def SetAverageState(self, function, state=True):
        return_value = False
        if function in self.MeasurementFunctions:
            return_value = True
            auto_range_string = function + ":AVER:STAT "
            if state == True:
                auto_range_string += "ON"
            else:
                auto_range_string += "OFF"
            self.scpi_comm(auto_range_string)
            time.sleep(1)
        return(return_value)

#------------------------------------------------------------------------------
    def SetNPLC(self, function, value):
        return_value = False
        if function in self.MeasurementFunctions:
            return_value = True
            command = function + ":NPLC " + str(value)
            self.scpi_comm(command)
            time.sleep(1)
        return(return_value)

#------------------------------------------------------------------------------
    def SetContinue(self, state=False):
        command = "INIT:CONT "
        if state == True:
            command += "ON"
        else:
            command += "OFF"
        self.scpi_comm(command)

#------------------------------------------------------------------------------
    def Read(self):
        readline = self.scpi_comm("READ?")
        if len(readline) < 16:
            return math.inf
        return readline.split(',')[0][0:15]

#------------------------------------------------------------------------------
    def SetMeasurement(self, mode):
        self.SetMeasurementFunction(mode)
        self.SetAutoRange(mode)
        self.SetAverageState(mode, False)
        self.SetNPLC(mode, 10)
        self.SetContinue(False)
#------------------------------------------------------------------------------
    def ConnectChan(self,n): # Connect channel to DMM
        self.scpi_comm('ROUT:CLOS (@1'+ ('%.2d' % n) +')')
#------------------------------------------------------------------------------
    def DisconnectAll(self): # Disconnect all channels 
        self.scpi_comm('ROUT:OPEN:ALL')
#------------------------------------------------------------------------------
    def Scan(self):
       self.serial.write(str.encode("SENS:FUNC 'VOLT:DC'\n")) # measuring DC VOLTS
       self.serial.write(str.encode("SENS:VOLT:DC:RANG:AUTO ON\n")) # auto range
       self.serial.write(str.encode("TRAC:CLE\n")) # Clear buffer.
       self.serial.write(str.encode("INIT:CONT OFF\n")) # Disable continuous initiation.
       self.serial.write(str.encode("TRIG:SOUR IMM\n")) # Select the immediate control source.
       self.serial.write(str.encode("TRIG:COUN 1\n")) # Set to perform one scan.
       #ser.write(str.encode("TRIG:DEL 1\n")) # Set to perform delay in secs.
       self.serial.write(str.encode("SAMP:COUN 10\n")) # Set to scan 10 channels.
       self.serial.write(str.encode("ROUT:SCAN (@101:110)\n")) # Set scan list channels; 101 through 110.
       self.serial.write(str.encode("ROUT:SCAN:TSO IMM\n")) # Start scan when enabled and triggered.
       self.serial.write(str.encode("ROUT:SCAN:LSEL INT\n")) # Enable scan
       self.serial.write(str.encode("READ?\n")) # Trigger scan and request the readings
       time.sleep(8)
       self.serial.flushInput() # On Python 3 "reset_input_buffer()"


       self.serial.write(str.encode("TRAC:DATA?\n"))
       
       res = []
       readline=''   
       time.sleep(0.1)
       ch=''
       while ch != '\n': 
          ch = self.serial.read(1).decode("ASCII")
          if ch == '':
            break
          readline += ch
       if readline == '':
           self.serial.write(str.encode("*RST\n")) # Disable scan
           return res

          
       readline = readline.split(';') 
       readline = readline[0].split(',')      
       for s in readline:
          if s.rfind('VDC') == len(s)-3:
             inp = s[0:15]
             fl_input = float(inp)
             res.append(fl_input)
       self.serial.write(str.encode("*RST\n")) # Disable scan
       return res  
    

