from serial import Serial
import time

class QJE:

    def __init__(self, port):
        self.port = port
        self.serial = None

    def Connect(self):
        self.serial = Serial(self.port, 9600, timeout=1)
        time.sleep(1)

        print(f"QJ3003P подключен: {self.port}")

    def Disconnect(self):

        if self.serial and self.serial.is_open:
            self.serial.close()

        print("QJ3003P отключен")

    def Write(self, command):
        self.serial.write(command.encode())
        print(f"Отправлено: {command}")

    def SetVoltage(self, voltage):
        self.Write(f"VSET1:{voltage:.2f}")

    def SetCurrent(self, current):
        self.Write(f"ISET1:{current:.3f}")
    
    def PowerOn(self):
        self.Write("OUTPUT1")
        print("Питание включено")

    def PowerOff(self):
        self.Write("OUTPUT0")
        print("Питание отключено")