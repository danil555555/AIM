import sys

from colorama import init

from stand import PrepareStand
from measurements.runCoefAIM import GetCalibrationInfoAIM
from measurements.runTestAIM import RunTestAIM
from measurements.runCalibrationAIM import RunCalibrationAIM
from tools.Agilent34401A import Agilent34401A
from tools.TGA1240 import TGA1240


init()


def printMainMenu() -> None:
    print("")
    print("")
    print("Тест AIM".center(75,"="))
    print("1. Тест платы")
    print("2. Калибровка платы")
    print("3. Сменить модуль")
    print("4. Выход")
    print("="*75)
    print("")
    print("")


def moduleMenu(context: dict) -> str:
    """
    Меню работы с установленным модулем.

    Возвращает:
        CHANGE_MODULE — сменить модуль;
        EXIT          — завершить программу.
    """

    while True:
        printMainMenu()

        choice = input("Введите номер действия: ").strip()

        if choice == "1":
            testResult = RunTestAIM(context)

            if testResult:
                print("Тестирование прошло успешно")
            else:
                print("Тестирование прошло неуспешно")

        elif choice == "2":
            calibrateResult = RunCalibrationAIM(context)

            if calibrateResult:
                print("Калибровка прошла успешно")
            else:
                print("Калибровка прошла неуспешно")

        elif choice == "3":
            return "CHANGE_MODULE"

        elif choice == "4":
            return "EXIT"

        else:
            print("Ошибка: необходимо выбрать пункт от 1 до 4")


def processModule(context: dict) -> str:
    """
    Проверяет состояние калибровки и определяет дальнейшую работу.

    Возвращает:
        CHANGE_MODULE — перейти к следующему модулю;
        EXIT          — завершить программу.
    """

    calibrationResult = GetCalibrationInfoAIM(context)

    if calibrationResult == "NOT_FOUND":
        print("Калибровка отсутствует")
        print("Будет выполнена автоматическая калибровка и тестирование")


        calibrateResult = RunCalibrationAIM(context)

        if calibrateResult:
            print("Калибровка прошла успешно")

            testResult = RunTestAIM(context)

            if testResult:
                print("Тестирование прошло успешно")
            else:
                print("Тестирование закончилось с ошибкой")
        else:
            print("Калибровка закончилась с ошибкой")

    elif calibrationResult == "FAILED":
        print("Калибровочные коэффициенты неправильные")


    elif calibrationResult == "OK":
        print("Калибровочные коэффициенты исправны")

    else:
        print(
            "Ошибка проверки калибровочных коэффициентов: "
            f"{calibrationResult!r}"
        )

        return "CHANGE_MODULE"

    return moduleMenu(context)



def main() -> None:

    agilent = Agilent34401A("COM6")
    agilent.SetMeasurement("VOLT:DC")

    generator = TGA1240("COM4")
    generator.SetupChannel(1, wform='DC')

    first_start = True
    old_moduleName = ""

    try:
        while True:
            context = PrepareStand(agilent, generator, first_start, old_moduleName)

            first_start = False

            old_moduleName = context["moduleType"]

            action = processModule(context)

            if action == "CHANGE_MODULE":
                print("Подготовьте следующий модуль")
                continue

            if action == "EXIT":
                print("Завершение работы")
                return

    except KeyboardInterrupt:
        print("\nРабота остановлена пользователем")

    except Exception as error:
        print(f"\nКритическая ошибка программы: {error}")
        raise

    finally:

        print("Завершение работы со стендом")


if __name__ == "__main__":
    main()