# from pyModbusTCP.client import ModbusClient
# c = ModbusClient(host="127.0.0.1", port=7007, auto_open=True)
# if c.write_multiple_registers(10, [44,55]):
#     print("write ok")
# else:
#     print("write error")
import re,binascii
def str2HexBytes(str):
    if not str:
        return
    arr = re.findall(r'.{2}',str)
    result = []
    for item in arr:
        result.append(int(item,16))
    return bytes(result)

encoded = str2HexBytes('3007')
result = binascii.hexlify(encoded)
print(result)