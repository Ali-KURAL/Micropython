import modbus
import time
from bh1750 import BH1750

modbus_obj = modbus.Modbus(0,9600,0x01,10,16,17)

register_quantity=10
signed=True
scl = machine.Pin(5)
sda = machine.Pin(4)
i2c = machine.I2C(0,scl = scl,sda = sda)
s = BH1750(i2c)
s.set_mode("CLR")
registers = [1]*11
while True:
    modbus_obj.process(registers)
    time.sleep(0.5)
    lux = int(s.lux() //1)
    registers[0] = lux
    print(lux)
    print(registers)