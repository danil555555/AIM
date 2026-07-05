from stand import PrepareStand

from measurements.runCoefAIM import GetCalibrationInfoAIM
from measurements.runTestAIM import RunTestAIM
from measurements.runCalibrationAIM import RunCalibrationAIM

def print_menu():

    print("")
    print("=============== Тест AIM ===============")
    print("1. Информация о калибровке")
    print("2. Тест платы")
    print("3. Калибровка платы")
    print("4. Выход")
    print("========================================")
    print("")

def main():

    context = PrepareStand() # подготовка платы к работе 

    while True:
        print_menu()

        choice = input("Введите цифру действия: ").strip()

        if choice == "1":
            GetCalibrationInfoAIM(context)

        elif choice == "2":
            RunTestAIM(context)

        elif choice == "3":
            RunCalibrationAIM(context)

        elif choice == "4":
            print("Завершение работы")
            break

        else:
            print("Ошибка, нужно выбрать пункт 1-4")

if __name__ == "__main__":
    main()