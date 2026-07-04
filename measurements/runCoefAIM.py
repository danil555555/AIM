import struct
import numpy as np

REFERENCE_OFFSETS = {
    "AIM-812": 12100.0,
    "AIM-813": -12100.0,
    "AIM-801": 0.0,
    "AIM-804": 0.0,
    }

thresholdGain = 0.1
thresholdOffsetMv = 100

def ReadCalibrate(data):
    """
    Распаковка калибровочных коэффициентов из EEPROM.
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

    calbInfo = ctd1620.ReadEPROM(0, SlotNumber, 1)
    calbDate, oldGain, oldOffset = ReadCalibrate(calbInfo)

    if oldGain is not None and oldOffset is not None:
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
    else:
        print("Калибровочные коэффициенты не найдены")


def GetCalibrationInfoAIM(context):

    ctd1620 = context["ctd1620"]
    SlotNumber = context["SlotNumber"]
    moduleName = context["moduleName"]

    GetCalibParam(ctd1620, SlotNumber, moduleName)