# -*- coding: utf-8 -*-
import socket, struct, time, sys
import datetime
import atexit
import logging
import os
import subprocess
from logging.handlers import RotatingFileHandler


LOG_FILE = os.path.abspath('ctd1620.log')
logger = logging.getLogger('CTD1620')
logger.setLevel(logging.DEBUG)
logger.propagate = False

if not logger.handlers:
    log_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8',
        delay=False,
    )
    log_handler.setFormatter(logging.Formatter(
        '%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    ))
    logger.addHandler(log_handler)


_logConsoleProcess = None


def _stopLogConsole():
    global _logConsoleProcess
    if _logConsoleProcess is not None and _logConsoleProcess.poll() is None:
        try:
            _logConsoleProcess.terminate()
        except OSError:
            pass
    _logConsoleProcess = None


def _startLogConsole():
    global _logConsoleProcess

    if os.name != 'nt':
        return
    if os.environ.get('CTD1620_LOG_CONSOLE', '1') == '0':
        return
    if _logConsoleProcess is not None and _logConsoleProcess.poll() is None:
        return

    escaped_path = LOG_FILE.replace("'", "''")
    powershell_command = (
        "$Host.UI.RawUI.WindowTitle='CTD1620 communication log'; "
        "Write-Host 'CTD1620 log: {}'; "
        "Get-Content -LiteralPath '{}' -Wait"
    ).format(LOG_FILE, escaped_path)

    try:
        _logConsoleProcess = subprocess.Popen(
            [
                'powershell.exe',
                '-NoLogo',
                '-NoProfile',
                '-ExecutionPolicy',
                'Bypass',
                '-Command',
                powershell_command,
            ],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
    except OSError:
        logger.exception('LOG_CONSOLE failed to start')


atexit.register(_stopLogConsole)
_startLogConsole()


def _hexPreview(data, limit=64):
    if not data:
        return '-'
    preview = ' '.join('{:02x}'.format(value) for value in data[:limit])
    if len(data) > limit:
        preview += ' ...'
    return preview


def _commandCaller():
    try:
        frame = sys._getframe(1)
        this_file = os.path.abspath(__file__)
        while frame is not None:
            if os.path.abspath(frame.f_code.co_filename) != this_file:
                break
            frame = frame.f_back
        if frame is None:
            return 'unknown'
        return '{}:{}:{}'.format(
            os.path.basename(frame.f_code.co_filename),
            frame.f_lineno,
            frame.f_code.co_name,
        )
    except (AttributeError, ValueError):
        return 'unknown'


#------------------------------------------------------------------------------
def unpackDateTime(data):
    if len(data) != 8:
        raise IOError('Error data size of DateTime')

    date = struct.unpack('<HBBBBBB', data)
    dt = datetime.datetime(
         year   = date[6] + 2000,
         month  = date[5],
         day    = date[4],
         hour   = date[3],
         minute = date[2],
         second = date[1],
         microsecond = 1000*date[0]
    )
    return dt


#------------------------------------------------------------------------------
def unpackDATA(data, number, format='<f', size=4):
    o = 12
    tag = struct.unpack('<4sll', data[0:o])
    if (tag[0] != b'DATA'):
        raise IOError('Error tag name')
    if (tag[1] > len(data)-12):
        raise IOError('Error tag size')
    if (tag[1] != number*size):
        raise IOError('Error tag size')

    params = []
    end = o + tag[2]
    while o < end:
        params.append(struct.unpack(format, data[o:o+size])[0])
        o += size

    return params


#==============================================================================
class BlockParameters:

#------------------------------------------------------------------------------
    def __init__(self, data=None):
        self.reset()
        if data != None:
            self.unpackBPRM(data)

#------------------------------------------------------------------------------
    def __str__(self):
        return str(self.parameters)

#------------------------------------------------------------------------------
    def reset(self):
        self.vibroParameters = []
        self.vibroStates = []
        self.tachoParameters = []
        self.tachoStates = []
        self.ed = []
        self.modbus = []
        self.datetime = datetime.datetime.today();
        self.timeOfMachine = 0
        self.timeOfModule = 0
        self.temp = int(0)
        self.loadARM = 0  
        self.loadDSP = 0  

#------------------------------------------------------------------------------
    def unpackTimes(self, data):
        if len(data) != 16:
            raise IOError('Error data size of Times')
        self.datetime = unpackDateTime(data[0:8])
        self.timeOfMachine = struct.unpack('<L', data[8:12])[0]
        self.timeOfModule = struct.unpack('<L', data[12:16])[0]

#------------------------------------------------------------------------------
    def unpackLOAD(self, data):
        o = 12
        tag = struct.unpack('<4sll', data[0:o])
        if (tag[0] != b'LOAD'):
            raise IOError('Error tag name')
        if (tag[1] != len(data)-12):
            raise IOError('Error tag size')

        self.temp = struct.unpack('<i', data[o:o+4])[0]
        self.loadARM = struct.unpack('<L', data[o+4:o+8])[0]
        self.loadDSP = struct.unpack('<L', data[o+8:o+12])[0]

#------------------------------------------------------------------------------
    def unpackPRMB(self, data):
        o = 12
        tag = struct.unpack('<4sll', data[0:o])
        if (tag[0] != b'PRMB'):
            raise IOError('Error tag name')
        if (tag[1] != len(data)-12):
            raise IOError('Error tag size')

        Number = struct.unpack('<L', data[o:o+4])[0]

        o += tag[2]
        self.modbus = unpackDATA(data[o:], Number, '<H', 2)

#------------------------------------------------------------------------------
    def unpackPRED(self, data):
        o = 12
        tag = struct.unpack('<4sll', data[0:o])
        if (tag[0] != b'PRED'):
            raise IOError('Error tag name')
        if (tag[1] != len(data)-12):
            raise IOError('Error tag size')

        Number = struct.unpack('<L', data[o:o+4])[0]

        o += tag[2]
        self.ed = unpackDATA(data[o:], Number, '<H', 2)

#------------------------------------------------------------------------------
    def unpackPRTC(self, data):
        o = 12
        tag = struct.unpack('<4sll', data[0:o])
        if (tag[0] != b'PRTC'):
            raise IOError('Error tag name')
        if (tag[1] != len(data)-12):
            raise IOError('Error tag size')

        Channel = struct.unpack('<H', data[o:o+2])[0]
        Number  = struct.unpack('<H', data[o+2:o+4])[0]

        tachoStates = []
        tachoStates.append(struct.unpack('<b', data[o+4:o+5])[0])
        self.tachoStates.append(tachoStates)

        o += tag[2]
        params = unpackDATA(data[o:], Number)
        self.tachoParameters.append(params)

#------------------------------------------------------------------------------
    def unpackPRVC(self, data):
        o = 12
        tag = struct.unpack('<4sll', data[0:o])
        if (tag[0] != b'PRVC'):
            raise IOError('Error tag name')
        if (tag[1] != len(data)-12):
            raise IOError('Error tag size')

        Channel = struct.unpack('<H', data[o:o+2])[0]
        Number  = struct.unpack('<H', data[o+2:o+4])[0]

        s = o + 4
        end = s + Number
        vibroStates = []
        while s < end:
            vibroStates.append(struct.unpack('<b', data[s:s+1])[0])
            s += 1

        o += tag[2]
        vibroStates.append(struct.unpack('<b', data[o-1:o])[0])
        self.vibroStates.append(vibroStates)
    
        params = unpackDATA(data[o:], Number)
        self.vibroParameters.append(params)

#------------------------------------------------------------------------------
    def unpackBPRM(self, data):
        o = 0
        if len(data) < 12:
            raise IOError('Error data size is smoll')

        e = o + 12
        tag = struct.unpack('<4sll', data[o:e])
        o = e
        if (tag[0] != b'BPRM'):
            raise IOError('Error tag name')
        if (tag[1] != len(data)-12):
            raise IOError('Error tag size')

        e = o + tag[2]
        self.unpackTimes(data[o:e])
        o = e

        while o < len(data):
            e = o + 12
            tag = struct.unpack('<4sll', data[o:e])

            e += tag[1]
            if tag[0] == b'PRED':
                self.unpackPRED(data[o:e])
            elif tag[0] == b'PRMB':
                self.unpackPRMB(data[o:e])
            elif tag[0] == b'PRTC':
                self.unpackPRTC(data[o:e])
            elif tag[0] == b'PRVC':
                self.unpackPRVC(data[o:e])
            elif tag[0] == b'LOAD':
                self.unpackLOAD(data[o:e])
            else:
                print("Unknow")
            o = e

#------------------------------------------------------------------------------
    def SetData(self, data):
        self.reset()
        if data != None:
            self.unpackBPRM(data)

#------------------------------------------------------------------------------
    def parameters(self, data, channel, param):
        # Защита: если данных вообще нет (массив пустой), возвращаем его как есть
        if not data:
            return data
            
        if channel < 0:
            if param < 0:
                return data
            else:
                # Фильтрация: берем 'param' по всем каналам, игнорируя слишком короткие каналы
                return [ch[param] for ch in data if len(ch) > param]
        else:
            # Защита: проверяем, существует ли запрашиваемый канал в массиве
            if channel >= len(data):
                return [] # Или можно возвращать None / вызывать ошибку
                
            if param < 0:
                return data[channel]
            else:
                # Защита: проверяем, существует ли параметр внутри этого канала
                if param >= len(data[channel]):
                    return None
                return data[channel][param]

#------------------------------------------------------------------------------
    def VibroParameters(self, channel=-1, param=-1):
        return self.parameters(self.vibroParameters, channel, param)

#------------------------------------------------------------------------------
    def VibroStates(self, channel=-1, param=-1):
        return self.parameters(self.vibroStates, channel, param)

#------------------------------------------------------------------------------
    def TachoParameters(self, channel=-1, param=0):
        return self.parameters(self.tachoParameters, channel, param)

#------------------------------------------------------------------------------
    def TachoStates(self, channel=-1, param=0):
        return self.parameters(self.tachoStates, channel, param)

#------------------------------------------------------------------------------
    def States(self):
        return self.states

#------------------------------------------------------------------------------
    def Ed(self):
        return self.ed

#------------------------------------------------------------------------------
    def Modbus(self):
        return self.modbus

#------------------------------------------------------------------------------
    def DateTime(self):
        return self.datetime

#------------------------------------------------------------------------------
    def Temperature(self):
        return float(self.temp * 0.0625)


#==============================================================================
class Trend:
#------------------------------------------------------------------------------
    def __init__(self, data=None):
        self.blockParams = [] #BlockParameters()
        if data != None:
            self.unpackTRND(data)

#------------------------------------------------------------------------------
    def __str__(self):
        return str(self.parameters)

#------------------------------------------------------------------------------
    def unpackTRND(self, data):
        o = 0
        if len(data) < 12:
            raise IOError('Error data size is smoll: ' + str(data))

        e = o + 12
        tag = struct.unpack('<4sll', data[o:e])
        o = e
        if (tag[0] != b'TRND'):
            raise IOError('Error tag name')
        if (tag[1] != len(data)-12):
            raise IOError('Error tag size')

        e = o + tag[2]
        #self.unpackTrendHeader(data[o:e])
        o = e

        blockParam = BlockParameters()
        self.blockParams = []

        while o < len(data):
            e = o + 12
            tag = struct.unpack('<4sll', data[o:e])

            e += tag[1]
            if tag[0] == b'BPRM':
                blockParam.unpackBPRM(data[o:e])
                self.blockParams.append(blockParam)
            else:
                print("Unknow")
            o = e

#------------------------------------------------------------------------------
    def BlockParams(self, index):
        if index < 0:
            return self.blockParams
        elif index < len(self.blockParams):
            return self.blockParams[index]
        else:
            return []


#==============================================================================
class Inspection:
#------------------------------------------------------------------------------
    def __init__(self, data=None):
        self.waves = {}
        self.tachos = {}
        self.blockParams = BlockParameters()
        self.datetime = datetime.datetime.today();
        if data != None:
            self.unpackINSP(data)

#------------------------------------------------------------------------------
    def __str__(self):
        return str(self.parameters)

#------------------------------------------------------------------------------
    def unpackINSP(self, data):
        o = 0
        if len(data) < 12:
            raise IOError('Error data size is smoll: ' + str(data))

        e = o + 12
        tag = struct.unpack('<4sll', data[o:e])
        o = e
        if (tag[0] != b'INSP'):
            raise IOError('Error tag name')
        if (tag[1] != len(data)-12):
            raise IOError('Error tag size')

        e = o + tag[2]
        #self.unpackInspectionHeader(data[o:e])
        o = e

        while o < len(data):
            e = o + 12
            tag = struct.unpack('<4sll', data[o:e])

            e += tag[1]
            if tag[0] == b'BPRM':
                self.blockParams.unpackBPRM(data[o:e])
            elif tag[0] == b'WAVE':
                self.unpackWAVE(data[o:e])
            elif tag[0] == b'TAXO':
                self.unpackTAXO(data[o:e])
            else:
                print("Unknow")
            o = e

#------------------------------------------------------------------------------
#    def unpackInspectionHeader(self, data):

#------------------------------------------------------------------------------
    def unpackWAVE(self, data):
        o = 12
        tag = struct.unpack('<4sll', data[0:o])
        if (tag[0] != b'WAVE'):
            raise IOError('Error tag name')
        if (tag[1] != len(data)-12):
            raise IOError('Error tag size')

        e = o + tag[2]
        Channel = struct.unpack('<L', data[o:o+4])[0]
        Number  = struct.unpack('<L', data[e-4:e])[0]
        #print("WAVE CH" + str(Channel) + " length " + str(Number))

        self.waves[Channel] = unpackDATA(data[e:], Number)

#------------------------------------------------------------------------------
    def unpackTAXO(self, data):
        o = 12
        tag = struct.unpack('<4sll', data[0:o])
        if (tag[0] != b'TAXO'):
            raise IOError('Error tag name')
        if (tag[1] != len(data)-12):
            raise IOError('Error tag size')

        e = o + tag[2]
        Channel = struct.unpack('<L', data[o:o+4])[0]
        Number  = struct.unpack('<L', data[e-4:e])[0]
        #print("TAXO CH" + str(Channel) + " length " + str(Number))

        self.tachos[Channel] = unpackDATA(data[e:], Number, '<L', 4)

#------------------------------------------------------------------------------
    def GetWave(self, channel):
        if (channel in self.waves):
            return self.waves[channel]
        return 0.0


#==============================================================================
class CTD1620:

    Modes = [1, 2]

    Commands2 = ['GTSS', 'SIZZ', 'RTLS', 'LSSZ', 'LIST', 'LISZ', 'GTFL', 'FLSZ', 'GTIN', 'INSZ', 'EVSZ', 'GTEV', 'GLUI']

#------------------------------------------------------------------------------
    def __init__(self, ip):
        self.ip = ip
        self.port1 = 30001
        self.port2 = 30002
        self.isConnected = False
        self.mode = 1
        logger.info('CREATE ip=%s mode=%s', self.ip, self.mode)

#------------------------------------------------------------------------------
    def SetServerMode(self, mode):
        logger.info(
            'SET_MODE requested=%s connected=%s current=%s',
            mode, self.isConnected, self.mode,
        )
        if self.isConnected:
            logger.warning('SET_MODE rejected: device is connected')
            return False
        if mode in self.Modes:
            self.mode = mode
            logger.info('SET_MODE success mode=%s', self.mode)
            return True
        logger.warning('SET_MODE rejected: invalid mode=%s', mode)
        return False

#------------------------------------------------------------------------------
    def Connect(self):
        started = time.monotonic()
        logger.info(
            'CONNECT start ip=%s port1=%s port2=%s mode=%s',
            self.ip, self.port1, self.port2, self.mode,
        )
        self.sock1 = socket.socket()
        self.sock2 = socket.socket()
        try: 
            self.sock1.settimeout(4.0)
            self.sock2.settimeout(4.0)
            self.sock1.connect((self.ip, self.port1))
            if self.mode == 2:
                self.sock2.connect((self.ip, self.port2))
            self.isConnected = True
            logger.info(
                'CONNECT success ip=%s elapsed=%.3f',
                self.ip, time.monotonic() - started,
            )
            return True
        except Exception:
            self.isConnected = False
            logger.exception(
                'CONNECT failed ip=%s elapsed=%.3f',
                self.ip, time.monotonic() - started,
            )
            return False

#------------------------------------------------------------------------------
    def Disconnect(self):
        logger.info('DISCONNECT start ip=%s connected=%s', self.ip, self.isConnected)
        try:
            self.sock1.close()
            self.sock2.close()
            self.isConnected = False
            logger.info('DISCONNECT success ip=%s', self.ip)
        except Exception:
            self.isConnected = False
            logger.exception('DISCONNECT failed ip=%s', self.ip)
            raise

#------------------------------------------------------------------------------
    def Command(self, command, data=b'', timeout=0.1):
        started = time.monotonic()
        caller = _commandCaller()
        logger.debug(
            'REQUEST command=%s caller=%s connected=%s mode=%s '
            'data_size=%s data_hex=%s timeout=%.3f',
            command, caller, self.isConnected, self.mode,
            len(data), _hexPreview(data), timeout,
        )
        try:
            sock = self.sock1
            socket_number = 1
            if (self.mode == 2) and (command in self.Commands2):
                sock = self.sock2
                socket_number = 2
            size = 4 + len(data)
            transmit = struct.pack('<4sl4s', b'SND>', size, str.encode(command))
            if size > 4:
                transmit += data
            sock.send(transmit)
            time.sleep(timeout)
            ans = sock.recv(8)
            if len(ans) != 8:
                raise IOError('Error header size')
            ans = struct.unpack('<4sl', ans)
            if ans[0] != b'ANS>':
                raise IOError('Error header magic number')
            size = ans[1]
            ansv = b''
            while size > 0:
                tmp = sock.recv(4096)
                size_tmp = len(tmp)
                if size_tmp == 0:
                    raise IOError('Error data size')
                size -= size_tmp
                ansv += tmp

            logger.debug(
                'RESPONSE command=%s caller=%s socket=%s response_size=%s '
                'response_hex=%s elapsed=%.3f',
                command, caller, socket_number, len(ansv),
                _hexPreview(ansv), time.monotonic() - started,
            )
            return ansv
        except Exception:
            logger.exception(
                'COMMAND_ERROR command=%s caller=%s connected=%s '
                'elapsed=%.3f',
                command, caller, self.isConnected,
                time.monotonic() - started,
            )
            raise

#------------------------------------------------------------------------------
    def ReadEPROM(self, slotType, slotNumber, recordNumber):
        data = struct.pack('<lll', slotType, slotNumber, recordNumber)
        return self.Command('GTRC', data)

#------------------------------------------------------------------------------
    def WriteEPROM(self, slotType, slotNumber, recordNumber, data):
        out = struct.pack('<llll', slotType, slotNumber, recordNumber, len(data))
        out += data
        anst = self.Command('BRRC', out, timeout=1)
        if anst == b'OK':
            return True
        return False

#------------------------------------------------------------------------------
    def FixHardwareConfig(self):
        anst = self.Command('FHWC', timeout=1)
        if anst == b'OK':
            return True
        return False

#------------------------------------------------------------------------------
    def SaveInspection(self, maskVibro, maskTacho):
        data = struct.pack('<LL', maskVibro, maskTacho)
        return self.Command('SVIN', data)

#------------------------------------------------------------------------------
    def GetInspection(self, maskVibro, maskTacho):
        data = struct.pack('<LL', maskVibro, maskTacho)
        return self.Command('GTIN', data)

#------------------------------------------------------------------------------
    def GetLastInspection(self):
        return self.Command('GLUI')

#------------------------------------------------------------------------------
    def GetDeviceInfo(self):
        return self.Command('GTIF').decode('utf-8')

#------------------------------------------------------------------------------
    def GetConfig(self):
        return self.Command('GTCF',struct.pack('<llll', 0, 0, 0, 0)).decode('CP1251')

#------------------------------------------------------------------------------
    def GetFile(self, data):
        return self.Command('GTFL', data)

#------------------------------------------------------------------------------
    def GetStateInspection(self):
        ans = self.Command('GSIN', timeout=0.0)
        if len(ans) == 4:
            return struct.unpack('<l', ans)[0]
        return -1
#------------------------------------------------------------------------------
    def GetState(self):
        ans = self.Command('GTST',timeout=8)
        ansv = struct.unpack('<lll',ans)
        return ansv[0],ansv[1],ansv[2]
#------------------------------------------------------------------------------
    def GetLastError(self):
        return self.Command('GTLE', timeout=0.0).decode('utf-8') #.decode('CP1251')

#------------------------------------------------------------------------------
    def ResetLastError(self):
        return self.Command('RSLE').decode('CP1251')

#------------------------------------------------------------------------------
    def Reboot(self):
        return self.Command('REST').decode('CP1251')

#------------------------------------------------------------------------------
    def Restart(self, timeout=0):
        ret = self.Command('SRST').decode('CP1251')
        time.sleep(timeout)
        return ret

#------------------------------------------------------------------------------
    def HWRestart(self, timeout=2):
        ret = self.Command('HWRS').decode('CP1251')
        time.sleep(timeout)
        return ret

#------------------------------------------------------------------------------
    def SetDateTime(self, date=datetime.datetime.now()):
        data = struct.pack('<BBBBBBB', 100+date.year%100, date.month-1, date.day, date.hour, date.minute, date.second, date.weekday())
        return self.Command('SDTI', data).decode('CP1251')

#------------------------------------------------------------------------------
    def GetDateTime(self):
        ans = self.Command('GTTM')
        return unpackDateTime(ans)

#------------------------------------------------------------------------------
    def LockInspection(self):
        return self.Command('LKCN').decode('CP1251')

#------------------------------------------------------------------------------
    def GetLockInspection(self):
        ans = self.Command('GLKC')
        if len(ans) == 8:
            return struct.unpack('<LL', ans)
        return ans

#------------------------------------------------------------------------------
    def UnlockInspection(self):
        return self.Command('CLLC').decode('CP1251')

#------------------------------------------------------------------------------
    def Bash(self, command):
        data = str.encode(command)
        return self.Command('BASH', data).decode('CP1251')

#------------------------------------------------------------------------------
    def GetBlockParameters(self):
        BP = BlockParameters(self.Command('GTBP'))
        return BP

#------------------------------------------------------------------------------
    def SetIP(self, NewIP, NewNetmask=None, NewGateway=None):
        if NewNetmask == None:
           data = struct.pack('<4s',socket.inet_aton(NewIP))
        elif NewGateway == None:
           data = struct.pack('<4s4s', socket.inet_aton(NewIP), socket.inet_aton(NewNetmask))
        else:
           data = struct.pack('<4s4s4s', socket.inet_aton(NewIP), socket.inet_aton(NewNetmask), socket.inet_aton(NewGateway))
        return self.Command('STIP', data).decode('CP1251')

#------------------------------------------------------------------------------
    def SetWorkCountAgregate(self, minute=0):
        data = struct.pack('<L', minute)
        return self.Command('STAG', data).decode('CP1251')

#------------------------------------------------------------------------------
    def SetWorkCountModule(self, minute=0):
        data = struct.pack('<L', minute)
        return self.Command('STMD', data).decode('CP1251')

#------------------------------------------------------------------------------
    def SetRelayState(self, state=0):
        data = struct.pack('<L', state)
        return self.Command('SSRL', data).decode('CP1251')

#------------------------------------------------------------------------------
    def GetRelayState(self):
        ans = self.Command('GSRL')
        if len(ans) == 4:
            data = struct.unpack('<L', ans)
            return data[0]
        return ans

#------------------------------------------------------------------------------
    def GetVersion(self):
        ans = self.Command('GVER') 
        if len(ans) == 16:
            data = struct.unpack('<LLLL', ans)
            return str(data[0]) + '.' + \
                   str(data[1]) + '.' + \
                   str(data[2]) + '.' + \
                   str(data[3])
        return "0.0.0.0"
