# Raspberry Pi Pico Modbus Library for RS485

## About
This is a micropython library for modbus slave.

## Setup


UART pins as shown in the table below:
 
| Raspberry Pi Pico    | Pin | RS485 |
| ---                  | --- | ---    |
| GP16                 | 21     | TX      |
| GP17                 | 22     | RX      |
| GND                  | 38,23,28...       | GND      |
| 5V(OUT)            | 40     | VBUS      |


![alt text](https://github.com/Ali-KURAL/Micropython/blob/main/libs/modbus_slave_rs485/rs485_pin.png)






## Test Code 


```python
import modbus
import time


modbus_obj = modbus.Modbus(0,9600,0x01,10,16,17)

register_quantity=10
signed=True

registers = [1]*10
while True:    
    modbus_obj.process(registers)
    registers[1] += 1
    time.sleep(0.5)
```

