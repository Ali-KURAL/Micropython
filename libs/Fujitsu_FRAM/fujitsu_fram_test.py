import time
import fujitsu_fram

# FRAM(spi_bus,spi_cs,spi_sck,spi_mosi,spi_miso)
fram = fujitsu_fram.FRAM(0,17,18,19,16)

# set 1 to register 0
fram[0] = 1

time.sleep(0.2)


# read register 0
print(fram[0])
