# -*- coding: cp1251 -*-
import numpy as np
import time
import math
import serial
from tools.Agilent34401A import AgilentReadError
from measurements.post_report import *
from measurements.printInfo import *
from playsound import playsound

from eeprom.eeprom import *

IsScanned = r'./Resource/IsScanned.mp3'
SayFailed = r'./Resource/TestIsFailed.mp3'
SaySuccessful = r'./Resource/TestIsSuccessful.mp3'

def read_mult(agilent, attempts=3, delay=0.2):
    for attempt in range(1, attempts + 1):
        value = agilent.Read()

        if value is not None:
            return value

        print(
            f"Повтор чтения мультиметра: "
            f"{attempt}/{attempts}"
        )

        if attempt < attempts:
            time.sleep(delay)

    print(
        "Предупреждение: не удалось получить "
        "показание мультиметра"
    )

    return None

def Measure(ctd1620, agilent, channels, average=1, delta=0.1, param=0):
    #ctd1620-для чтения V,agilent - для чтения V,channels - для списка ctd1620
    avrVoltage = 0.0
    avrParams = np.zeros(channels) #напряжение на pcm1620 
    tmpVoltageOld = avrVoltage
    tmpParamsOld = avrParams

    agilent.Read()

    if (average == 1):
        BP = ctd1620.GetBlockParameters()
        avrVoltage = 1000.0 * read_mult(agilent) #чтение показаний мультиметра
        if avrVoltage is None:
            print("Нет данных мультиметра. Измерение остановлено. Перезагрузите мультиметр.")
            return None, None
        avrParams = np.array(BP.VibroParameters(param=param)[0:channels])
        #avrParams - получаем из цифровой платы pcm1620
        return (avrVoltage, avrParams) #(out, in)

    i = 0
    ret = 1
    while True: #цикл измерений
        i += 1
        if i > 50:
            print("Ошибка усреднения значения.")
            return None, None
        BP = ctd1620.GetBlockParameters()
        mult_value = read_mult(agilent)
        if mult_value is None:
            print("Нет данных мультиметра. Измерение остановлено.")
            return None, None
        avrVoltage += 1000.0 * float(mult_value)
        params = BP.VibroParameters(param=param)[0:channels]
        avrParams += params
        koef = 1.0 / float(i)
        tmpVoltage = koef * avrVoltage
        tmpParams  = koef * avrParams
        dVoltage = abs(tmpVoltage - tmpVoltageOld)  #изменение out
        dParams  = abs(tmpParams - tmpParamsOld) #изменение in
        ret = max(dVoltage, max(dParams)) #максимальное изменение in или out
        print(f"\rУсреднение измерений " + str(i) + ": " + f"{ret:.3f}    ", end = '', flush=True)
        time.sleep(1)
        #print("\r" + " " * 75 + "\r", end='', flush = True )
        #txt = "Average " + str(i) + " (" + "{0:.3f}".format(ret) + ")"
        #print(txt.ljust(24,' '), end='\r')
        if (ret < delta) and (i >= average): #условие выхода из цикла
            print('')
            # Добавить логирование погрешности 
            break
        tmpVoltageOld = tmpVoltage
        tmpParamsOld  = tmpParams.copy()
        # реализовать выход из цикла 

    return (tmpVoltage, tmpParams) #(out, in)
    #out - мультиметр (float), in - блок с платами ctd1620 (array)

def WaitStable(ctd1620, agilent, channels, delta=0.2, param=0):
    #функция ожидания, пока измерения не станут стабильными
    out1, in1 = Measure(ctd1620, agilent, channels) #первое измерение
    ret = 1
    i = 0
    while True:
        i += 1 # out2,in2 - Новые измерения, уже с параметром
        if i > 50:
            print("Ошибка ожидания")
            return
        out2, in2 = Measure(ctd1620, agilent, channels, param=param)
        #out1 = 0.9*out1 + 0.1*out2
        #in1  = 0.9*in1  + 0.1*in2
        dout = abs(out2 - out1) 
        din  = abs(in2 - in1)
        ret = max(dout, max(din))
        print(f"\rCтабилизация измерений " + str(i) + ": " + f"{ret:.3f}   ", end='\r', flush=True)
        #Print(logfile, "Стабилизация измерений")
        if ret < delta: #максимальная погрешность в пределах допуска?
            print('')
            return
        out1 = out2
        in1  = in2.copy()



def linescan(out,ag,n,lowthr,highthr,offset=0): # Сканирование напряжений линий
   #ag-мультиметр, n-это кол-во каналов,
   Print(out, "Проверка напряжений выходных линий питания".center(40, '-'))
   Print(out, "")
   Print(out,f"Допустимый диапазон: {lowthr:.3f} ... {highthr:.3f}")
   Print(out, "")
   ag.SetMeasurement('VOLT:DC')
   vals = np.zeros(n) #zeros создает массив из n элементов, заполненный нулями
   res = []
   list_results = []
   np.set_printoptions(formatter={'float': '{: 0.3f}'.format})
   for x in range(0,n):
     ag.ConnectChan(offset+x+1) #настройка мультиметра на канал
     ag.SetContinue(False) #отключение продолжения (?)
     time.sleep(2)
     val=ag.Read()#чтение показаний мультиметра
     #Цикл проходит по всем каналам: если напряжение не входит в заданный диапазон, то
     #номер неисправного канала заносится в список res; если все каналы исправны - список пуст
     while isinstance(val,float) and not math.isfinite(val): # Пока inf повторять попытки чтения
        #повторять пока (с плавающей токой) и (бесконечное) 
        val = ag.Read()
     val = float(val)
     vals[x] = val
     if val>=lowthr and val<=highthr:
           pass
           list_results.append("OK")
     else:
           res.append(x+1) #append - добавление элемента в конец списка
           list_results.append("FAILED")
   Print(out, "Таблица напряжений".center(75, '-'))
   Print(out, "Канал | Напряжение, В | Результат")
   Print(out, "---------------------------------")
   for i in range(0, len(vals)):
      line = (
         "CH" + str(i + 1).zfill(2) + "  | " +
         "{0:12.3f}".format(vals[i]) + "  | " +
         list_results[i]
      )
      if(list_results[i] == "OK"):
         Print(out, line, color="green")
      else:
         Print(out, line, color="red")

   return res #список с номерами неисправных каналов





def lineread(file,ag,n,inout=0,offset=0, attempts=5):
   values = np.zeros(n) 
   np.set_printoptions(formatter={'float': '{: 0.3f}'.format})
   for y in range(0,n):
     
     ag.ConnectChan(offset+inout+y+1)
     time.sleep(2)

     ag.SetContinue(False) 
     time.sleep(2)

     #ag.Read()   
     for attempt in range(1, attempts+1):
         value = ag.Read()
         if value is None:
             print(f"Измерить канал {y+1} не удалось, попытка {attempt}/{attempts}")
             time.sleep(0.4)
             continue
         value = float(value)
         print(f"\rИзмерение " + str(y+1) + ": " + f"{value}   ", end='\r', flush=True)
         values[y] = 1000.0 * value
         break
     else:
        return None
   print("Измерения выполнены успешно     ")
   return values


#------------------------------------------------------------------------------
def MeasureResult(multimetr, tool, threshold):
    result = []
    for value in tool:
        if(abs(value - multimetr) > threshold):
            result.append("FAILED")
        else:
            result.append("OK")
    return result
#------------------------------------------------------------------------------
def AuxMeasureResult(measure : list, measure_aux : list, threshold):
    result =[]
    for i in range(len(measure)):
        if(abs(measure[i] - measure_aux[i]) > threshold):
            result.append("FAILED")
        else:
            result.append("OK")
    return result


def Deltacalc(list1,list2):
   deltalist = np.zeros(len(list1))
   if len(list1) != len(list2):
     print("Error: lists length not equal") 
     return deltalist
   for k in range(0,len(list1)):
     deltalist[k]=abs(list1[k]-list2[k])

   return deltalist


#------------------------------------------------------------------------------
def CheckThreshold(out,values, threshold): #проверка прохождения порога
    ret = True
    text = "SUCCESSFUL "
    deltaMax = max(values) #выбор самого большого отклонения; values - это массив
    if (deltaMax > threshold):
        text = "FAILED "
        ret = False
    Print(out, text + "{0:.3f}".format(deltaMax))
    return ret

#------------------------------------------------------------------------------
def CheckGain(out, gains, threshold):
    
    gainDelta = max( abs(max(gains) - 1.0), abs(min(gains) - 1.0))
    if (gainDelta >= threshold):
        Print(out, "Gain FAILED " + "{0:.3f}".format(gainDelta))
        return False
    return True

def MeasurePointAIM(out, ctd1620, agilent, generator, moduleChannels, offsetGen, delta, title):

    Print(out, title.center(75, '-'))
    generator.SetOffset(offsetGen)
    Print(out, "Параметры генератора: DC - " + f"{offsetGen}" + "V")
    time.sleep(2)
    WaitStable(ctd1620, agilent, moduleChannels, delta=delta)
    mult, AIMVolt = Measure(ctd1620, agilent, moduleChannels, average=10, delta=delta / 2.0)
    result = MeasureResult(mult, AIMVolt, delta)
    #PrintArrayCompareTable(out, "", mult, AIMVolt, result, threshold=delta / 2)
    Print(out, f"Напряжение на мультиметре {mult}, mV")
    Print(out,"")
    header = (
            f"{'Канал':<6} | "
            f"{'Напряжение AIM':>18}" 
        )
    Print(out, header)
    for i in range(0, len(AIMVolt)):
        line = (
            f"{'CH' + str(i+1).zfill(2):<6} | "
            f"{AIMVolt[i]:>18.3f}"
        )
        Print(out, line)

    return mult, AIMVolt

def CalcCoefCalibration(out, ctd1620, fileName, mult1, mult2, AIMVolt1, AIMVolt2):

   Print(out, "Расчёт калибровочных коэффициентов".center(75, '-'))
   calbGain = abs((mult2 - mult1) / (AIMVolt2 - AIMVolt1))
   calbOffset = ((AIMVolt1 + AIMVolt2) - (mult1 + mult2) / calbGain) / 2.0
   result_3 = []
   error_gain = []
   for value in calbGain:
      if (abs(1-value) > 0.1):
         result_3.append('FAILED')
         error_gain.append(value-1)
      else:
         result_3.append('OK')
         error_gain.append(value-1)

   PrintChannelMeasureTable(out, "Gain", calbGain, error_gain, result_3)
   
   result_4 = []
   for i in range(len(calbOffset)):
      result_4.append("OK")

   PrintChannelMeasureTable(out, "OffsetAim", calbOffset, 0.0, result_4)

   testIsOk = CheckGain(out, calbGain, 0.1)


   #-----------------------------------------------------
   #запись калибровочного коэффициента в плату
   Print(out, "Write".center(75, '-'))
   WriteCalibrate(out, ctd1620, fileName, calbGain, calbOffset)

   if testIsOk != True:
       playsound(SayFailed)

   return testIsOk

def CheckDcMeasureAIM(out, ctd1620, agilent, generator, moduleChannels, offsetGen, delta, moduleInput):
   Print(out, "Проверка измерения по постоянному току после калибровки".center(75, '-'))
   generator.SetOffset(offsetGen)
   time.sleep(3)
   Print(out, "VOLT:DC")
   Print(out, "Параметры генератора: Offset = " + f"{offsetGen}" + "V")
   # Measure DC

   WaitStable(ctd1620, agilent, moduleChannels, delta=delta)
   out3, in3 = Measure(ctd1620, agilent, moduleChannels, average=10)
   if (abs(abs(out3) - abs(offsetGen)) < 1):
      print(f"Ошибка измерения, мультиметр должен измерить {offsetGen}")
   
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

   if all(r == "OK" for r in result_5):
       result = "OK"
   else:
       result = "FAILED"

   return in3, result

def CheckAcMeasureAIM(out, ctd1620, agilent, generator, moduleChannels, offsetGen, delta):
   
   Print(out, "Проверка измерения по переменному току после калибровки".center(75, '-'))
   agilent.SetMeasurement("VOLT:AC") #from agilent py
   generator.SetupChannel(1, freq = 160.0, ampl = 8.0, offset = offsetGen) #from TGA1240 py
   time.sleep(3) #from time
   Print(out, "VOLT:AC")
   Print(out, "Параметры генератора: Offset = " + f"{offsetGen}" + "V, " + "Freq = 160 Hz, " + "Ampl = 8 V, ")
   # Measure AC
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

   if all(r == "OK" for r in result_6):
       result = "OK"
   else:
       result = "FAILED"
   return in4, result

def CheckDcMeasureAuxAim(out, agilent, generator, offsetGen, moduleChannels , in3, moduleType):
   
   Print(out, "Проверка AUX выходо по постоянному напряжению".center(75, '-'))
   # Output test with DC
   agilent.SetMeasurement('VOLT:DC')
   generator.SetOffset(offsetGen)
   time.sleep(3)
   Print(out, "Параметры генератора: DC - " + f"{offsetGen}" + "mV")
   if (moduleType == 'AIM-211'):
     out5 = lineread(out,agilent,moduleChannels,inout=10,offset=6)
   else:
     out5 = lineread(out,agilent,moduleChannels, inout=10)
   if out5 is None:
       Print(out, "Ошибка, мультиметр не передал данные")
       return "FAILED"
   result_7 = AuxMeasureResult(in3, out5, 50.0)
   PrintArrayCompareTable(out, "", in3, out5, result_7, 50.0)

   if all(r == "OK" for r in result_7):
       result = "OK"
   else:
       result = "FAILED"

   return result

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
   PrintArrayCompareTable(out, "", in4, out6, result_8, 30.0)

   if all(r == "OK" for r in result_8):
       result = "OK"
   else:
       result = "FAILED"

   return result

def CheckOutputLines(out, ctd1620, agilent, moduleType, moduleChannels, fileName):
    ctd1620.Disconnect()

    if (moduleType.split("-")[1][1] == "1"):

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

    else:
        Print(out, "Выходных линий питания нет на данной плате")
    time.sleep(2)
    ctd1620.Connect()
    time.sleep(2)

