from stand import PrepareStand

from measurements.runCoefAIM import GetCalibrationInfoAIM
from measurements.runTestAIM import RunTestAIM
from measurements.runCalibrationAIM import RunCalibrationAIM

from tools.Agilent34401A import *
from tools.TGA1240 import *

def print_menu():

    print("")
    print("=============== Тест AIM ===============")
    print("1. Тест платы")
    print("2. Калибровка платы")
    print("3. Выход")
    print("========================================")
    print("")

def Choise(context):
    print_menu()

    choice = input("Введите цифру действия: ").strip()

    if choice == "1":
        RunTestAIM(context)

    elif choice == "2":
        RunCalibrationAIM(context)

    elif choice == "3":
        print("Завершение работы")

    else:
        print("Ошибка, нужно выбрать пункт 1-4")

def main():

    agilent = Agilent34401A("COM6")
    agilent.SetMeasurement("VOLT:DC")

    generator = TGA1240("COM4")
    generator.SetupChannel(1, wform='DC')

    while True:

        context = PrepareStand(agilent, generator) # подготовка стенда к работе. Возвращает все данные об АИМ 
        
        if not GetCalibrationInfoAIM(context):
            RunCalibrationAIM(context)
            RunTestAIM(context)
        else:
            Choise(context)

        # тут можно сделать инициализацию класса стенда где сразу будет коннект со свсеми приборами и все проверки 
        # для начала нужно проверить все приборы а дальше уже работать так как наверное ошибочно проверять все потом
        # Стандартная инициализация - если нет коэф, сразу запустить RunCalibrationAIM, 
        # 
        # если есть коэф то 
        
  


if __name__ == "__main__":
    main()