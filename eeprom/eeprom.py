import struct, sys
import datetime
import os
from measurements.printInfo import *
from measurements import conv_cfg_mem

SlotNumber = 0
TIMEOUT_RESTART = 3

#-----------------------------------------------------------------------------
def findtag(data,ftag):
    offset = 0
    while offset+8 <= len(data):
       tag = struct.unpack('<4sL',data[offset:offset+8])
       if tag[0].decode('ASCII') == ftag:
           return offset
       offset += (8+tag[1]*4)
    return -1 # 
#------------------------------------------------------------------------------
def GetModuleName(data):
    index = findtag(data,'NAME')
    if index < 0:
        return "UNKNOW"
    size = struct.unpack('<L', data[index+4:index+8])[0]
    name = data[index+8:index+8+4*size].decode('CP1251').rstrip('\0') + "."
    index = data.find(b'SERL')
    if index < 0:
        name += "XXXX" 
    else:
        serial = struct.unpack('<L', data[index+8:index+12])[0]
        name += str(serial)
    return name
#------------------------------------------------------------------------------
def GetModuleType(data):
    index = findtag(data,'NAME')
    if index < 0:
        return "UNKNOW"
    size = struct.unpack('<L', data[index+4:index+8])[0]
    name = data[index+8:index+8+4*size].decode('CP1251').rstrip('\0')
    return name

#------------------------------------------------------------------------------
def GetModuleDNP(data):
    index = findtag(data,'DNP:')
    if index < 0:
        return "UNKNOW"
    size = struct.unpack('<L', data[index+4:index+8])[0]
    return data[index+8:index+8+4*size].decode('CP1251').rstrip('\0')

#------------------------------------------------------------------------------
def GetModuleDate(data):
    index = findtag(data,'DATE')
    if index < 0:
        return "UNKNOW"
    size = struct.unpack('<L', data[index+4:index+8])[0]
    return data[index+8:index+8+4*size].decode('CP1251').rstrip('\0')

#------------------------------------------------------------------------------
def GetModuleChannels(data):
    channels = 0
    index = findtag(data,'CHNS')
    if index > 0:
        channels = struct.unpack('<L', data[index+8:index+12])[0]
    return channels

#------------------------------------------------------------------------------
def GetModuleVoltage(data):
    umin = 0
    umax = 0
    index = findtag(data,'UMIN')
    if index > 0:
        umin = struct.unpack('<f', data[index+8:index+12])[0]
    index = findtag(data,'UMAX')
    if index > 0:
        umax = struct.unpack('<f', data[index+8:index+12])[0]
    return umin, umax

#------------------------------------------------------------------------------
def GetModuleInput(data):
    Input = "Not find"
    index = findtag(data,'INPT')
    size = struct.unpack('<L', data[index+4:index+8])[0]
    Input = data[index+8:index+8+4*size].decode('CP1251').rstrip('\0')
    return Input


#------------------------------------------------------------------------------
def packCalibrate(Gain, Offset):
    date = datetime.date.today().strftime("%d.%m.%Y")
    calb = struct.pack('<4s', str.encode('CALB'))
    size_str = len(date)
    size_calb = 1 + size_str//4 + 1 + len(Gain) + len(Offset)
    if (size_str%4):
        size_calb += 1
    calb += struct.pack('<L', size_calb)

    calb += struct.pack('<L', size_str)
    calb += str.encode(date)
    if (size_str%4):
        calb += b' '*(4-size_str%4)

    calb += struct.pack('<L', len(Gain))
    for i in range(0, len(Gain)):
        calb += struct.pack('<f', Gain[i])
        calb += struct.pack('<f', Offset[i])

    return calb

#------------------------------------------------------------------------------
def WriteCalibrate(out, ctd1620, fileName, calbGain, calbOffset):
    calb = packCalibrate(calbGain, calbOffset)
    outfile = open(fileName + '.calb', 'wb')
    outfile.write(calb)
    outfile.close()
    ret = ctd1620.WriteEPROM(0, SlotNumber, 1, calb)
    if ret != True:
        Print(out, "FAILED")
        exit(1)
    Print(out, "SUCCESSFUL")
    Print(out, "")
    ctd1620.Restart(TIMEOUT_RESTART)



#------------------------------------------------------------------------------


#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
def GetFileName(moduleName):
    dirName = "./" + moduleName[0:7]
    if not os.path.exists(dirName):
        os.makedirs(dirName)
    curDate = datetime.date.today().strftime(".%y%m%d")
    return dirName + "/" + moduleName + curDate


#------------------------------------------------------------------------------
def moduleInfoModify(moduleInfo,AIM,dnp_change):
       data = moduleInfo
       # Замена серийного номера
   
       index = findtag(data,'SERL')
       if index >= 0:
           serl_old = data[index:index+12]
           serl_new = struct.pack('<4sll', b'SERL', 1, int(AIM['SN']))
           data = data.replace(serl_old, serl_new, 1)
       index = findtag(data,'DATE')
       if index >= 0:
           date = datetime.date.today().strftime("%d.%m.%Y")
           serl_old = data[index:index+18]
           serl_new = struct.pack('<4sl10s', b'DATE', 3, str.encode(date))
           data = data.replace(serl_old, serl_new)
       # Замена DNP
       if dnp_change:
          dnp_size = len(AIM['DNP'])
          if dnp_size != 10 and dnp_size != 9:
              quit('ERROR !!! Размер DNP не равен 10')
          if(dnp_size == 9):
              AIM['DNP'] += '\0'
          index = findtag(data,'DNP:')
          if index >= 0:
             dnp_old = data[index:index+18]
             dnp_new = struct.pack('<4sl10s', str.encode('DNP:'), 3, str.encode(AIM['DNP']))
             data = data.replace(dnp_old, dnp_new, 1)


       return data
#------------------------------------------------------------------------------



def ReadCalibrate(data):
    """
    Распаковка калибровочных коэффициентов из EEPROM.

    Возвращает:
    date   - дата калибровки
    gains  - массив Gain
    offsets - массив Offset
    """

    if data is None or len(data) < 16:
        print("Калибровочные данные пустые или слишком короткие")
        return None, None, None

    index = findtag(data, 'CALB')

    if index < 0:
        print("Тег CALB не найден")
        return None, None, None

    # Проверяем заголовок CALB
    tag, size_calb = struct.unpack('<4sL', data[index:index+8])

    if tag.decode('ASCII') != 'CALB':
        print("Это не блок CALB")
        return None, None, None

    pos = index + 8

    # Читаем размер строки даты
    date_size = struct.unpack('<L', data[pos:pos+4])[0]
    pos += 4

    # Читаем дату
    date = data[pos:pos+date_size].decode('CP1251')
    pos += date_size

    # Выравнивание до 4 байт
    if date_size % 4:
        pos += 4 - date_size % 4

    # Читаем количество каналов
    channels = struct.unpack('<L', data[pos:pos+4])[0]
    pos += 4

    gains = []
    offsets = []

    for i in range(channels):
        gain = struct.unpack('<f', data[pos:pos+4])[0]
        pos += 4

        offset = struct.unpack('<f', data[pos:pos+4])[0]
        pos += 4

        gains.append(gain)
        offsets.append(offset)

    return date, np.array(gains), np.array(offsets)

def GetCalibParam(ctd1620, SlotNumber, moduleName):
    
    REFERENCE_OFFSETS = {
    "AIM-812": 12100.0,
    "AIM-813": -12100.0,
    "AIM-801": 0.0,
    "AIM-804": 0.0,
    }

    thresholdGain = 0.1
    thresholdOffsetMv = 100

    calbInfo = ctd1620.ReadEPROM(0, SlotNumber, 1)
    calbDate, oldGain, oldOffset = ReadCalibrate(calbInfo)

    #if oldGain is not None and oldOffset is not None:
    if oldGain is not None:
        print("Калибровочные коэффициенты из EEPROM")
        print("Дата калибровки:", calbDate)

        header = (f"{'CH':<6} | "
             f"{'Gain':>9} | "
             f"{'Offset, mV':>12} | "
             f"{'Result':>10} | "
             )
        
        print(header)
        print("-" * len(header))
        result = []
        for i in range(len(oldGain)):

            if moduleName not in REFERENCE_OFFSETS:
                raise ValueError("Неизвестный тип платы: " + str(moduleName))
            else:
                refOffset = REFERENCE_OFFSETS[moduleName]

            gain_result = abs(oldGain[i] - 1) <= thresholdGain
            offset_result = abs(oldOffset[i] - refOffset) <= thresholdOffsetMv

            if gain_result and offset_result:
                result.append("OK")
            else:
                result.append("FAILED")

            line = (
            f"{'CH' + str(i + 1).zfill(2):<6} | "
            f"{oldGain[i]:>9.3f} | "
            f"{oldOffset[i]:>9.3f} | "
            f"{result[i]:>10} | "
            )

            print(line)
            print("-" * len(header))
            
        if all(value == "OK" for value in result):
            print("Результат проверки калибровочных коэффициентов: SUCCESSFUL")
        else:
            print("Результат проверки калибровочных коэффициентов: FAILED")
        return True
    
    else:
        print("Калибровочные коэффициенты не найдены")
        return False 

def PrepareModuleInfo(ctd1620, SlotNumber, AIM, AimQr, first_start, old_moduleName):  
    #есть вопросы
    """
    Читает/обновляет EEPROM платы, получает параметры модуля,
    загружает тестовую конфигурацию при первом запуске.

    Возвращает:
    moduleInfo, moduleType, moduleName, moduleDNP, moduleDate,
    moduleChannels, moduleInput, moduleUMin, moduleUMax,
    first_start, old_moduleName
    """

    # 1. Чтение EEPROM
    moduleInfo = ctd1620.ReadEPROM(0, SlotNumber, 0)

    if len(moduleInfo) <= 2:
        dnp_change = True
        print('Не удалось считать данные из EPROM платы')

        modulefilename = './EEPROM.Config/' + AIM['Name'] + '.bin'
        with open(modulefilename, 'rb') as f:
            moduleInfo = f.read()
    else:
        dnp_change = False
        print("Данные успешно считаны")

    # 2. Проверка соответствия типа платы
    moduleType = GetModuleType(moduleInfo)

    if AIM is not None and moduleType != AIM['Name']:
        dnp_change = True
        print('Тип платы был изменен')

        modulefilename = './EEPROM.Config/' + AIM['Name'] + '.bin'
        with open(modulefilename, 'rb') as f:
            moduleInfo = f.read()

    # 3. Модификация EEPROM-данных
    if len(sys.argv) <= 1:
        moduleInfo = moduleInfoModify(moduleInfo, AIM, dnp_change)

    # 4. Извлечение параметров платы
    moduleType = GetModuleType(moduleInfo)
    moduleName = GetModuleName(moduleInfo)
    moduleDNP = GetModuleDNP(moduleInfo)
    moduleDate = GetModuleDate(moduleInfo)
    moduleChannels = GetModuleChannels(moduleInfo)
    moduleInput = GetModuleInput(moduleInfo)
    moduleUMin, moduleUMax = GetModuleVoltage(moduleInfo)

    # 5. Запись EEPROM обратно в плату
    #if len(sys.argv) <= 1:
        #res = ctd1620.WriteEPROM(0, SlotNumber, 0, moduleInfo)

        #if not res:
            #quit('Не могу записать информацию в плату')

        #ctd1620.HWRestart()

    # 6. Проверка, что серия плат одного типа
    if not first_start and (moduleType != old_moduleName):
       quit('Плата не соответствует первой плате серии')
    else:
       old_moduleName = moduleType
       old_DNP = moduleDNP
       if first_start:
          first_start = False
 
          conffile = './'+moduleType+'/'+moduleType+'.Calibration.xml'
          Ini_conf = conv_cfg_mem.XmlToIni(conffile)
          test = ctd1620.Command('STCF', str.encode(Ini_conf), 4) # Загрузка конфигурации
          if not test:
              quit('Не могу загрузить в цифровую плату тестовую конфигурацию')
          else:
              print('Тестовая конфигуация загружена')
              print("")

          res=ctd1620.FixHardwareConfig()
          if not res:
             quit('Не могу зафиксировать аппаратную конфигурацию')
          else:
             print('Аппаратная конфигурация зафиксирована')
             print("")

    fileName = GetFileName(moduleName)
    logfile = open(fileName + '.log', 'w')
    Print(logfile, "Begin".center(40, '-'))
    Print(logfile, "Module  : " + moduleName[0:7])
    Print(logfile, "Number  : " + moduleName[8:])
    Print(logfile, "Channels: " + str(moduleChannels))
    Print(logfile, "Input   : " + moduleInput)
    Print(logfile, "Voltage : " + "{0:.1f}".format(moduleUMin) + " ... " + "{0:.1f}".format(moduleUMax))
    Print(logfile, "DNP     : " + moduleDNP)
    Print(logfile, "Date    : " + moduleDate)
    Print(logfile, "".center(40, '-'))
    Print(logfile,"")


    return (
        moduleInfo,
        moduleType,
        moduleName,
        moduleDNP,
        moduleDate,
        moduleChannels,
        moduleInput,
        moduleUMin,
        moduleUMax,
        first_start,
        old_moduleName,
        old_DNP,
        fileName,
        logfile
    )