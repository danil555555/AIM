
def CheckDcMeasureAIM(out, ctd1620, agilent, generator, moduleChannels, offsetGen, delta, moduleInput):
   Print(out, "Проверка измерения по постоянному току после калибровки".center(75, '-'))
   generator.SetOffset(offsetGen)
   time.sleep(3)
   Print(out, "Параметры генератора: DC - " + f"{offsetGen}" + "V")
   # Measure DC
   Print(out, "VOLT:DC")
   WaitStable(ctd1620, agilent, moduleChannels, delta=delta)
   out3, in3 = Measure(ctd1620, agilent, moduleChannels, average=10)
   if (moduleInput == "IEPE"):
      threshold_dc = 5.0
   else:
      threshold_dc = 1.0

   result_5 = []
   for value in in3:
       if (abs(out3-value) > threshold_dc):
           result_5.append('FAILED')
       else:
           result_5.append('OK')

   PrintArrayCompareTable(out, "", out3, in3, result_5, threshold_dc)
   return in3

def CheckAcMeasureAIM(out, ctd1620, agilent, generator, moduleChannels, offsetGen, delta):
   
   Print(out, "Проверка измерения по переменному току после калибровки".center(75, '-'))
   agilent.SetMeasurement("VOLT:AC") #from agilent py
   generator.SetupChannel(1, freq = 160.0, ampl = 8.0, offset = offsetGen) #from TGA1240 py
   time.sleep(3) #from time
   Print(out, "Параметры генератора: AC - Offset = " + f"{offsetGen}" + "V, " + "Freq = 160 Hz, " + "Ampl = 8 V, ")
   # Measure AC
   Print(out, "VOLT:AC")
   WaitStable(ctd1620, agilent, moduleChannels, delta=delta, param=2) #local def
   out4, in4 = Measure(ctd1620, agilent, moduleChannels, average = 10, param=2) #local def
   #out - multimetr (float), in - pcm1620 (list of float)
   
   result_6 = []
   for value in in4:
       if (abs(out4-value) > 3.0): #в итоге какая граница
           result_6.append('FAILED')
       else:
           result_6.append('OK')


   PrintArrayCompareTable(out, "", out4, in4, result_6, 3.0) #local def
   return in4

def CheckDcMeasureAuxAim(out, agilent, generator, offsetGen, moduleChannels , in3, moduleType):
   
   Print(out, "Проверка AUX выходо по постоянному напряжению".center(75, '-'))
   # Output test with DC
   agilent.SetMeasurement('VOLT:DC')
   generator.SetOffset(offsetGen)
   time.sleep(3)
   Print(out, "Параметры генератора: DC - " + f"{offsetGen}" + "mV")
   print("DC output check:")
   if (moduleType == 'AIM-211'):
     out5 = lineread(out,agilent,moduleChannels,inout=10,offset=6)
   else:
     out5 = lineread(out,agilent,moduleChannels, inout=10)

   result_7 = AuxMeasureResult(in3, out5, 50.0)
   PrintArrayCompareTable(out, "", in3, out5, result_7, 50.0)

def CheckAcMeasureAuxAim(out, agilent, generator, offsetGen, moduleChannels , in4, moduleType):
   
   Print(out, "Проверка AUX выходо по переменному напряжению".center(75, '-'))
   agilent.SetMeasurement("VOLT:AC")
   generator.SetupChannel(1, 160.0, 8.0, offsetGen)
   time.sleep(3)
   Print(out, "Параметры генератора: AC - Offset = " + f"{offsetGen}" + "V, " + "Freq = 160 Hz, " + "Ampl = 8 V, ")
   if (moduleType == 'AIM-211'):
     out6 = lineread(out,agilent,moduleChannels,inout=10,offset=6)
   else:
     out6 = lineread(out,agilent,moduleChannels,inout=10)

   result_8 = AuxMeasureResult(in4,out6, 30.0)
   test6 = PrintArrayCompareTable(out, "", in4, out6, result_8, 30.0)

def CheckOutputLines(out, ctd1620, agilent, moduleType, moduleChannels, fileName):
    ctd1620.Disconnect()

    error_lines = []

    if moduleType == 'AIM-411':
        error_lines = linescan(out, agilent, moduleChannels, 22.4, 23.7)

    elif moduleType == 'AIM-211':
        error_lines = linescan(out, agilent, moduleChannels, 22.4, 23.7, offset=6)

    elif moduleType == 'AIM-412' or moduleType == 'AIM-812':
        error_lines = linescan(out, agilent, moduleChannels, -25.175, -23.475)

    if len(error_lines) > 0:
        Print(out, "Неправильные напряжения на каналах: " + str(error_lines))
        out.close()
        playsound(SayFailed)
        post_report.post_report(fileName + '.log')
        quit()
    else:
        Print(out, "Результат: ")
        Print(out, "SUCCESSFUL", color="green")
        Print(out, "")

    ctd1620.Connect()

def CalcSafeOffsetsGen(moduleUMin, moduleUMax, moduleInput, Delta):
    """
    Рассчитывает безопасные напряжения:
    OffsetMax — верхняя точка калибровки
    OffsetMin — нижняя точка калибровки
    Offset    — средняя точка для проверки DC/AC
    Delta     — допустимое отклонение
    """

    OffsetMax = moduleUMax - 1.0
    if OffsetMax > 10.0:
        OffsetMax = 10.0

    OffsetMin = moduleUMin + 1.0
    if OffsetMin < -10.0:
        OffsetMin = -10.0

    if moduleInput == "IEPE":
        Delta = 1.0

    Offset = (OffsetMin + OffsetMax) / 2.0

    if abs(Offset) < 1.0:
        Offset = 1.0

    return OffsetMax, OffsetMin, Offset, Delta

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