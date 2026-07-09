from measure import *
from calculate import *

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

    OffsetMax, OffsetMin, Offset, Delta = CalcSafeOffsetsGen(moduleUMin, moduleUMax, moduleInput, Delta)

    CheckOutputLines(logfile, ctd1620, agilent, moduleType, moduleChannels, fileName)

    generator.SetupChannel(1, wform='DC')
    agilent.ConnectChan(9)  # Работаем с 9 каналом для измерений текущего напряжения напрямую с генератора
    agilent.SetMeasurement("VOLT:DC")

    in3 = CheckDcMeasureAIM(logfile, ctd1620, agilent, generator, moduleChannels, Offset, Delta, moduleInput)

   #-----------------------------------------------------
    in4 = CheckAcMeasureAIM(logfile, ctd1620, agilent, generator, moduleChannels, Offset, Delta)

   #Проверка проверка буфферных выходов AIM на DC
   #-----------------------------------------------------

    CheckDcMeasureAuxAim(logfile, agilent, generator, Offset, moduleChannels, in3, moduleType)

   #Проверка проверка буфферных выходов AIM на AC

    CheckAcMeasureAuxAim(logfile, agilent, generator, Offset, moduleChannels, in4, moduleType)

    Print(logfile, "End".center(75, '-'))
    logfile.close()

    ctd1620.Disconnect()

   # Отправка лога и двоичного файла на ftp сервер
    post_report.post_report(fileName+'.log')
    post_report.post_report(fileName+'.calb')

   #Учет результатов проверки

    if testIsOk == True:
        playsound(SaySuccessful)
    else:
        playsound(SayFailed)