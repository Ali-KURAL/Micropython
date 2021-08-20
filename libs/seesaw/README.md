# Raspberry Pi Pico Seesaw Soil Sensor with Micropython Library

## About
This is a micropython library for Seesaw Soil Moisture Sensor

## Setup


I2C pins as shown in the table below:
 
| Raspberry Pi Pico    | Pin | BME280 |
| ---                  | --- | ---    |
| GP16                 | 21     | SDA      |
| GP17                 | 22     | SCL      |
| GND                  | 38,23,28...       | GND      |
| 3.3V(OUT)            | 36     | VIN      |


![alt text](https://github.com/Ali-KURAL/Micropython/blob/main/libs/seesaw/afsoilsensor.png)






## Code 
The calculations are presented as close to the examples in the datasheet as possible
Code automatically finds the i2c address when you give the i2c device in micropython.





If you want to use specific address for i2c you can use i2c_address label.
```python
ss = seesaw.Seesaw(i2c=i2c,i2c_address = 0x77)
```

