from measurements.calculate import CalcSafeOffsetsGen
from measurements.measure import *

def RunCalibrationAIM(context: object) -> bool:

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

    first_start = True
    old_moduleName = ''
    old_DNP = ''
    IsScanned = '../Resource/IsScanned.mp3'

    np.set_printoptions(formatter={'float': '{: 0.3f}'.format})

    SayFailed = '../Resource/TestIsFailed.mp3'
    SaySuccessful = '../Resource/TestIsSuccessful.mp3'
    TIMEOUT_RESTART = 3
    

    OffsetMax, OffsetMin, Offset, Delta = CalcSafeOffsetsGen(moduleUMin, moduleUMax, moduleInput, Delta)

    #CheckOutputLines(logfile, ctd1620, agilent, moduleType, moduleChannels, fileName)
    LogBlockStart(logfile, "Калибровка платы")
    Print(logfile, "Сброс калибровки платы".center(75, '-'))
    # Reset calibration
    calbGain = np.ones(moduleChannels, dtype=float)
    calbOffset = np.zeros(moduleChannels, dtype=float)
    WriteCalibrate(logfile, ctd1620, fileName, calbGain, calbOffset)

    generator.SetupChannel(1, wform='DC')
    agilent.ConnectChan(9)  # Работаем с 9 каналом для измерений текущего напряжения напрямую с генератора
    agilent.SetMeasurement("VOLT:DC")

    mult_high_volt_1, aim_high_volt_1 = MeasurePointAIM(logfile, ctd1620, agilent, generator, moduleChannels, OffsetMax, Delta, "Измерение 1: верхняя точка калибровки")
    mult_low_volt_2, aim_low_volt_2 = MeasurePointAIM(logfile, ctd1620, agilent, generator, moduleChannels, OffsetMin, Delta, "Измерение 2: нижняя точка калибровки")

    result = CalcCoefCalibration(logfile, ctd1620, fileName, mult_high_volt_1, mult_low_volt_2, aim_high_volt_1, aim_low_volt_2)

    LogBlockEnd(logfile)
    return result
    #in3 = CheckDcMeasureAIM(logfile, ctd1620, agilent, generator, moduleChannels, Offset, Delta, moduleInput)
    #in4 = CheckAcMeasureAIM(logfile, ctd1620, agilent, generator, moduleChannels, Offset, Delta)

    #CheckDcMeasureAuxAim(logfile, agilent, generator, Offset, moduleChannels, in3, moduleType)
    #CheckAcMeasureAuxAim(logfile, agilent, generator, Offset, moduleChannels, in4, moduleType)


