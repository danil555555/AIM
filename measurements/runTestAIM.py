# -*- coding: cp1251 -*-
from measurements.measure import *
from measurements.calculate import *
from measurements.post_report import *

def RunTestAIM(context):

    logfile = context["logfile"]
    ctd1620 = context["ctd1620"]
    agilent = context["agilent"]
    generator = context["generator"]
    moduleType = context["moduleType"]
    moduleChannels = context["moduleChannels"]
    moduleInput = context["moduleInput"]
    moduleUMin = context["moduleUMin"]
    moduleUMax = context["moduleUMax"]
    fileName = context["fileName"]
    Delta = 0.2
    testIsOk = True
    ctd1620.Connect()

    OffsetMax, OffsetMin, Offset, Delta = CalcSafeOffsetsGen(moduleUMin, moduleUMax, moduleInput, Delta)
    LogBlockStart(logfile, "Тестирование платы")
    CheckOutputLines(logfile, ctd1620, agilent, moduleType, moduleChannels, fileName)

    generator.SetupChannel(1, wform='DC')
    agilent.ConnectChan(9)  # Работаем с 9 каналом для измерений текущего напряжения напрямую с генератора
    agilent.SetMeasurement("VOLT:DC")

    in3, checkDcMeasureResult = CheckDcMeasureAIM(logfile, ctd1620, agilent, generator, moduleChannels, Offset, Delta, moduleInput)
    if checkDcMeasureResult == "FAILED":
        playsound(SaySuccessful)
        return False
   #-----------------------------------------------------
    in4, checkAcMeasureResult = CheckAcMeasureAIM(logfile, ctd1620, agilent, generator, moduleChannels, Offset, Delta)
    if checkAcMeasureResult == "FAILED":
        playsound(SaySuccessful)
        return False
   #Проверка проверка буфферных выходов AIM на DC
   #-----------------------------------------------------

    checkDcMeasureAuxResult = CheckDcMeasureAuxAim(logfile, agilent, generator, Offset, moduleChannels, in3, moduleType)
    if checkDcMeasureAuxResult == "FAILED":
        playsound(SaySuccessful)
        return False
   #Проверка проверка буфферных выходов AIM на AC

    checkAcMeasureAuxResult = CheckAcMeasureAuxAim(logfile, agilent, generator, Offset, moduleChannels, in4, moduleType)
    if checkAcMeasureAuxResult == "FAILED":
        playsound(SaySuccessful)
        return False
    
    LogBlockEnd(logfile)
    #Print(logfile, "End".center(75, '-'))
    #logfile.close()


    ctd1620.Disconnect()
   # Отправка лога и двоичного файла на ftp сервер
    #post_report(fileName+'.log')
    #post_report(fileName+'.calb')

   #Учет результатов проверки
    if(checkDcMeasureResult == "OK" and 
       checkAcMeasureResult == "OK" and 
       checkDcMeasureAuxResult == "OK" and 
       checkAcMeasureAuxResult == "OK"):
        testIsOk = True
    else:
        testIsOk = False

    if testIsOk == True:
        playsound(SaySuccessful)
    else:
        playsound(SayFailed)

    return testIsOk
