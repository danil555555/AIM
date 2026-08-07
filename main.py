# -*- coding: cp1251 -*-
import sys

from colorama import init

from stand import PrepareStand
from measurements.runCoefAIM import GetCalibrationInfoAIM
from measurements.runTestAIM import RunTestAIM
from measurements.runCalibrationAIM import RunCalibrationAIM
from measurements.printInfo import *
from tools.Agilent34401A import Agilent34401A
from tools.TGA1240 import TGA1240
from tools.PowerSource import QJE
import time

init()


def printMainMenu() -> None:
    print("")
    print("Тест AIM".center(60,"="))
    print("1. Тест платы")
    print("2. Калибровка платы")
    print("3. Сменить модуль")
    print("4. Выход")
    print("="*60)
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
            RunTestAIM(context)

        elif choice == "2":
            RunCalibrationAIM(context)

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
        #"Калибровка отсутствует"
        #"Будет выполнена автоматическая калибровка и тестирование"

        calibrateResult = RunCalibrationAIM(context)

        if calibrateResult:

            RunTestAIM(context)

    elif calibrationResult == "FAILED":
        pass

    elif calibrationResult == "OK":
        pass

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

    psu = QJE("COM14")
    psu.Connect()
    psu.OutputOff()

    first_start = True
    old_moduleName = ""

    try:
        while True:
            context = PrepareStand(agilent, generator, psu, first_start, old_moduleName)

            first_start = False

            old_moduleName = context["moduleType"]

            action = processModule(context)

            if action == "CHANGE_MODULE":
                print("Подготовьте следующий модуль")
                psu.OutputOff()
                time.sleep(1)
                psu.SetVoltage(0)
                time.sleep(1)
                psu.SetCurrent(0)
                continue

            if action == "EXIT":
                psu.OutputOff()
                time.sleep(1)
                psu.SetVoltage(0)
                time.sleep(1)
                psu.SetCurrent(0)
                print("Завершение работы")
                powerSource.PowerOff()
                return

    except KeyboardInterrupt:
        print("\nРабота остановлена пользователем")
        psu.OutputOff()
        time.sleep(1)
        psu.SetVoltage(0)
        time.sleep(1)
        psu.SetCurrent(0)

    except Exception as error:
        print(f"\nКритическая ошибка программы: {error}")
        psu.OutputOff()
        time.sleep(1)
        psu.SetVoltage(0)
        time.sleep(1)
        psu.SetCurrent(0)
        raise

    finally:

        print("Завершение работы со стендом")


if __name__ == "__main__":
    main()
