from tools.CTD1620 import *
from tools.Agilent34401A import *
from tools.TGA1240 import *
from scanQR.scan_markers import ScanDataMatrix
from eeprom.eeprom import *

SlotNumber = 0

def PrepareStand():

    print("Подготовка стенда")

    agilent = Agilent34401A("COM6")
    agilent.SetMeasurement("VOLT:DC")

    generator = TGA1240("COM4")
    generator.SetupChannel(1, wform='DC')

    ctd1620 = CTD1620("10.0.0.2")

    SlotNumber = 0

    print("Распознавание наклейки AIM-XXX.\n m - ручной ввод \n ESC - выйти")
    AIM = ScanDataMatrix('AIM')
    WaitPressEnter("1. Вставьте плату, подключите AUX\n2. Нажмите Enter")
    print("===========Connect===========")
    ctd1620.Connect()
    print("==========Read info==========")
    # Чтение информации из памяти платы
    (
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
    ) = PrepareModuleInfo(ctd1620, SlotNumber, AIM, first_start, old_moduleName)

    context = {
        "AIM": AIM,
        "moduleInfo": moduleInfo,
        "moduleType": moduleType,
        "moduleName": moduleName,
        "moduleDNP": moduleDNP,
        "moduleDate": moduleDate,
        "moduleChannels": moduleChannels,
        "moduleInput": moduleInput,
        "moduleUMin": moduleUMin,
        "moduleUMax": moduleUMax,
        "SlotNumber": SlotNumber,
        "ctd1620": ctd1620,
        "agilent": agilent,
        "generator": generator,
        "logfile": logfile,
        "fileName": fileName,
        "old_DNP": old_DNP,
    }

    return context


