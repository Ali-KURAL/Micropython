from mag_alpha_angle import MagAlpha
import time

magAlpha = MagAlpha(0,cs_pin = 17,sck_pin = 18,mosi_pin = 19,miso_pin = 16)

#Example of register settings (some settings may not be available on every sensor model)
#Set zero setting to 0 (Reg 0 and 1)
magAlpha.writeRegister(0, 0)
magAlpha.writeRegister(1, 0)
#Set Rotation Direction to Clockwise by writting 0 to register 9
magAlpha.writeRegister(9, 0)

#Read raw angle value until the user press on Ctr+C (Keyboard interrupt) to exit the program
while True:
    angle = magAlpha.readAngleInDegree(True)
    time.sleep(0.1)
