# -*- coding: cp1251 -*-
import struct
import numpy as np
from eeprom.eeprom import GetCalibParam

def GetCalibrationInfoAIM(context):

    ctd1620 = context["ctd1620"]
    SlotNumber = context["SlotNumber"]
    moduleName = context["moduleName"]
    logfile = context["logfile"]
    ctd1620.Connect()
    result = GetCalibParam(logfile, ctd1620, SlotNumber, moduleName[0:7])
    ctd1620.Disconnect()
    return result