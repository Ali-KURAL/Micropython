from modbus_serial_master import Master, Slave, MODE_ASCII
import time

mb_master = Master()
#  port, uart_tx, uart_rx, slaveID=1, baudrate=9600, parity=None, bits=8, stop=1

# MODE 'ASCII' OR 'RTU'
mb_slave = Slave(0, 0, 1, mode=MODE_ASCII)

mb_master.addSlave(mb_slave)

# FORMAT ABCDEFHG
print(mb_master.writeDouble(0, 51.2325))
time.sleep(0.1)
print(mb_master.readDouble(0))

# FORMAT ABCD
print(mb_master.writeFloat(4, 61.35))
time.sleep(0.1)
print(mb_master.readFloat(4))

# FORMAT ABCD
print(mb_master.writeLong(6, 2555623))
time.sleep(0.1)
print(mb_master.readLong(6))

# Unsigned Integer
print(mb_master.writeInteger(9, 22))
time.sleep(0.1)

# slaveID, starting_address, total_size
print(mb_master.readHoldingRegisters(1, 0, 5))
