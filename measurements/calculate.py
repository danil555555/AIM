# -*- coding: cp1251 -*-
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
