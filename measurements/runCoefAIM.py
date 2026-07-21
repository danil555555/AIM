import struct
import numpy as np
from eeprom.eeprom import GetCalibParam

def GetCalibrationInfoAIM(context):

    ctd1620 = context["ctd1620"]
    SlotNumber = context["SlotNumber"]
    moduleName = context["moduleName"]
    logfile = context["logfile"]

    result = GetCalibParam(logfile, ctd1620, SlotNumber, moduleName[0:7])
    return result