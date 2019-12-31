from pyModbusTCP.client import ModbusClient
c = ModbusClient(host="127.0.0.1", port=7007, auto_open=True)
if c.write_multiple_registers(10, [44,55]):
    print("write ok")
else:
    print("write error")