from tools.CTD1620 import *
from tools.PowerSource import *
from scanQR.scan_markers import ScanDataMatrix
from eeprom.eeprom import *
from measurements.printInfo import *

SlotNumber = 0

def PrepareStand(agilent, generator, powerSource, first_start, old_moduleName):

    SlotNumber = 0
    print("")
    print("")
    print("Чтение данных с наклейки".center(40, '='))
    print("Распознавание наклейки AIM-XXX.\n m - ручной ввод \n ESC - выйти")
    AIM = ScanDataMatrix('AIM')
    print("".center(40, '='))
    print()
    print("Подключение платы AIM-XXX".center(40, '='))
    WaitPressEnter("1. Вставьте плату, подключите AUX\n2. Нажмите Enter")
    powerSource.SetVoltage(24.00)
    powerSource.SetCurrent(1.500)
    powerSource.PowerOn()
    #print("Подключение к CTD-1620")
    ctd1620 = CTD1620("10.0.0.2")
    ctd1620.Connect()
    #print("Подключение к CTD-1620 выполнено успешно")
    print("".center(40,"="))
    print("")
    print("")
    

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
 # Если инфо есть проверить соотвесиве с Qr, если не согласуется дать варианты действия - перезаписать или прекратить 
 # если инфа есть ее можно оставить, или имя серийник dnp
# если нет инфы идем штатно  


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


