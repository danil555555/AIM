def CalcSafeOffsetsGen(moduleUMin, moduleUMax, moduleInput, Delta):
    """
    –ассчитывает безопасные напр€жени€:
    OffsetMax Ч верхн€€ точка калибровки
    OffsetMin Ч нижн€€ точка калибровки
    Offset    Ч средн€€ точка дл€ проверки DC/AC
    Delta     Ч допустимое отклонение
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