import numpy as np

#------------------------------------------------------------------------------
def WaitPressEnter(text="Нажмите любую клавишу..."):
    input(text)

#------------------------------------------------------------------------------
def Print(out, data, color = None):
    RED = "\033[91m" # код для вывода красным цветом
    GREEN = "\033[92m" # код для вывода зеленым цветом
    RESET = "\033[0m" # код для сброса цвета консоли обратно в черный

    txt = str(data)
    if(color == "red"):
        print(RED + txt + RESET)
    elif (color == "green"):
        print(GREEN + txt + RESET)
    else:
        print(txt)
    out.write(txt + "\n")



#------------------------------------------------------------------------------
def PercentError(measured, reference):
   """
   Расчет ошибки в процентах относительно одного эталонного значения.

   measured  - массив измеренных значений, например значения платы CTD1620
   reference - эталонное значение, например значение мультиметра Agilent

   Формула:
   percent = |measured - reference| / |reference| * 100
   """
   measured = np.array(measured, dtype=float)

   if abs(reference) < 1e-9:
      return np.zeros(len(measured))

   return abs(measured - reference) / abs(reference) * 100.0

#------------------------------------------------------------------------------
def PercentErrorArray(measured, reference):
   """
   Расчет ошибки в процентах для двух массивов одинаковой длины.

   measured  - массив измеренных значений, например AUX-выходы
   reference - массив эталонных значений, например значения платы CTD1620
   """
   measured = np.array(measured, dtype=float)
   reference = np.array(reference, dtype=float)
   result = np.zeros(len(measured))

   if len(measured) != len(reference):
      print("Error: lists length not equal")
      return result

   for i in range(0, len(measured)):
      if abs(reference[i]) < 1e-9:
         result[i] = 0.0
      else:
         result[i] = abs(measured[i] - reference[i]) / abs(reference[i]) * 100.0

   return result

#------------------------------------------------------------------------------
def PrintMeasureTable(out, title, reference, measured, threshold_mv):
   """
   Печать понятной таблицы для проверки входных измерений.

   reference    - эталон мультиметра, одно число, мВ
   measured     - массив значений платы, мВ
   threshold_mv - допустимая абсолютная ошибка, мВ
   """

   measured = np.array(measured, dtype=float)
   delta = abs(measured - reference)
   percent = PercentError(measured, reference)

   Print(out, title.center(65, '-'))
   Print(out, "Напряжение мультиметра: " + "{0:.3f}".format(reference) + " mV")
   Print(out, "Погрешность: +/-" + "{0:.3f}".format(threshold_mv) + " mV")
   Print(out, "")
   Print(out, "Канал | Напряжение AIM , mV | Ошибка, mV | Ошибка, %")
   Print(out, "---------------------------------------------")

   for i in range(0, len(measured)):
      line = (
         "CH" + str(i + 1).zfill(2) + "    | " +
         "{0:9.3f}".format(measured[i]) + " | " +
         "{0:9.3f}".format(delta[i]) + " | " +
         "{0:8.3f}".format(percent[i]) + " %"
      )
      Print(out, line)

   Print(out, "---------------------------------------------")
   Print(out, "MAX     |           | " +
         "{0:9.3f}".format(max(delta)) + " | " +
         "{0:8.3f}".format(max(percent)) + " %")

   if max(delta) <= threshold_mv:
      Print(out, "Result: SUCCESSFUL")
      Print(out, " ")
      return True
   else:
      Print(out, "Result: FAILED")
      Print(out, " ")
      return False
   
    

#------------------------------------------------------------------------------
def PrintArrayCompareTable(out, title, reference, measured, result, threshold = 0):
   """
   Печать таблицы для сравнения двух массивов.

   reference    - массив эталонных значений, например входные значения платы, мВ
   measured     - массив проверяемых значений, например AUX-выходы, мВ
   threshold_mv - допустимая абсолютная ошибка, мВ
   """

   measured = np.array(measured, dtype=float)

   if np.isscalar(reference):
       reference = np.full(len(measured), float(reference))
   else:
       reference = np.array(reference, dtype = float)

   delta = abs(measured - reference)
   percent = PercentErrorArray(measured, reference)

   header = (f"{'Канал':<6} | "
             f"{'Мультиметр, мВ':>18} | "
             f"{'AIM, мВ':>18} | "
             f"{'Ошибка, мВ':>12} | "
             f"{'Погрешность измерения, %':>20} | "
             f"{'Результат':>10} | "
             )

   Print(out, title.center(75, '-'))
   Print(out, "Погрешность: +/-" + "{0:.3f}".format(threshold) + " мВ")
   Print(out, "")
   Print(out, header)
   #Print(out, "Канал | Мультиметр, мВ | AIM, мВ | Ошибка, мВ | Погрешность измерения, % | Результат ")
   Print(out, "-" * len(header))

   for i in range(0, len(measured)):
      line = (
         f"{'CH' + str(i + 1).zfill(2):<6} | "
         f"{reference[i]:>18.3f} | "
         f"{measured[i]:>18.3f} | "
         f"{delta[i]:>12.3f} | "
         f"{percent[i]:>24.3f} | "
         f"{result[i]:>10} | "
      )
      if(result[i] == "OK"):
         Print(out, line, color = "green")
      else:
         Print(out, line, color = "red")
      

   Print(out, "-" * len(header))
   max_line = (f"{'MAX':<6} | "
               f"{'':>18} | "
               f"{'':>18} | "
               f"{max(delta):>12.3f} | "
               f"{max(percent):>24.3f} | "
               f"{'':>10}"
               )
   Print(out, max_line)
   Print(out, "Результат:")
   if all(r == "OK" for r in result):
      Print(out, "SUCCESSFUL", color = "green")
      Print(out, "")
      return True
   else:
      Print(out, "FAILED", color = "red")
      Print(out, "")
      return False


def PrintChannelMeasureTable(out, title, measured, error, result):
   """
   measured - массив измеренных значений, мВ
   """

   measured = np.array(measured, dtype=float)

   Print(out, title.center(75, '-'))
   header = (
      f"{'Канал':<6} | "
      f"{'Коэфициент':>14} | "
      f"{'Ошибка':>14} | "
      f"{'Результат':>10}"
      )
   Print(out, header)
   Print(out, "-" * len(header))

   for i in range(0, len(measured)):
      line = (
         f"{'CH' + str(i + 1).zfill(2):<6} | "
         f"{measured[i]:>14.3f} | "
         f"{error[i]:>14.3f} | "
         f"{result[i]:>10}"
      )
      if(result[i] == "OK"):
         Print(out, line, color = "green")
      else:
         Print(out, line, color = "red")

   Print(out, "-" * len(line))
   max_line = (f"{'MAX':<6} | "
               f"{'':>14} | "
               f"{max(error):>14.3f} | "
               f"{'':>10}"
               )
   Print(out, max_line)
   Print(out, "-" * len(header))
   Print(out, "Результат:")
   if all(r == "OK" for r in result):
      Print(out, "SUCCESSFUL", color = "green")
      Print(out, "")
      return True
   else:
      Print(out, "FAILED", color = "red")
      Print(out, "")
      return False