from stand import PrepareStand

from measurements.runCoefAIM import GetCalibrationInfoAIM
from measurements.runTestAIM import RunTestAIM
from measurements.runCalibrationAIM import RunCalibrationAIM

from tools.Agilent34401A import *
from tools.TGA1240 import *

from colorama import init

init()

def print_menu():

    print("")
    print("=============== Тест AIM ===============")
    print("1. Тест платы")
    print("2. Калибровка платы")
    print("3. Выход")
    print("========================================")
    print("")

def Choice(context):
    print_menu()

    choice = input("Введите цифру действия: ").strip()

    if choice == "1":
        RunTestAIM(context)

    elif choice == "2":
        RunCalibrationAIM(context)

    elif choice == "3":
        print("Завершение работы")

    else:
        print("Ошибка, нужно выбрать пункт 1-3")

def main():

    agilent = Agilent34401A("COM6")
    agilent.SetMeasurement("VOLT:DC")

    generator = TGA1240("COM4")
    generator.SetupChannel(1, wform='DC')

    first_start = True
    old_moduleName = ""

    while True:

        context = PrepareStand(agilent, generator, first_start, old_moduleName) # подготовка стенда к работе. Возвращает все данные об АИМ 
        
        calibrationResult = GetCalibrationInfoAIM(context)

        if calibrationResult == "NOT_FOUND":
            print("Калибровка отсутствует")
            runCalibrationAimResult = RunCalibrationAIM(context)
            if(runCalibrationAimResult):
                print("Калибровка прошла успешно")
                runTestResult = RunTestAIM(context)
                if(runTestResult):
                    print("Тестрирование прошло успешно")
                    continue
                else:
                    print("Тестирование прошло неуспешно")
                    Choice(context)
            else:
                print("Калибровка прошла неуспешно")
                print("1. Сменить модуль")
                print("2. Выход")
                choice = input("Выберите действие: ").strip()
                if choice == "1":
                    continue
                elif choice == "2":
                    quit("Выход из программы")
                else:
                    quit("Ошибка, нужно выбрать пункт 1-2")

        elif calibrationResult == "FAILED":
            print("Калибровочные коэффициенты неправильные")
            print("1. Калибровать")
            print("2. Выход")
            choice = input("Выберите действие: ").strip()

            if(choice == "1"):
                runCalibrationAimResult = RunCalibrationAIM(context)
                if(runCalibrationAimResult):
                    print("Калибровка прошла успешно")
                    runTestResult = RunTestAIM(context)
                    if(runTestResult):
                        print("Тестрирование прошло успешно")
                        continue
                    else:
                        print("Тестирование прошло неуспешно")
                        continue
            elif(choice == "2"):
                quit("Выход из программы")
            else:
                quit("Ошибка, нужно выбрать пункт 1-2")

        elif calibrationResult == "OK":
            print("Калибровочные коэффициенты исправны")
            Choice(context)

        else:
            print("Ошибка проверки калибровочных коэффициентов")



        # тут можно сделать инициализацию класса стенда где сразу будет коннект со свсеми приборами и все проверки 
        # для начала нужно проверить все приборы а дальше уже работать так как наверное ошибочно проверять все потом
        # Стандартная инициализация - если нет коэф, сразу запустить RunCalibrationAIM, 
        # 
        # если есть коэф то 
if __name__ == "__main__":
    main()