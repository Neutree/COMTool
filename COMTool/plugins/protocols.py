try:
    import parameters
except ImportError:
    from COMTool import parameters
import os

protocols_dir = os.path.join(parameters.dataPath, "protocols")

default = '''
def decode(data:bytes) -> bytes:
    return data

def encode(data:bytes) -> bytes:
    return data
'''

add_crc16 = '''

def decode(data:bytes) -> bytes:
    return data

def encode(data:bytes) -> bytes:
    crc_bytes = pack("<H", crc.crc16(data))
    return data + crc_bytes
'''

add_sum = '''
def decode(data:bytes) -> bytes:
    return data

def encode(data:bytes) -> bytes:
    return data + bytes([sum(a) % 256])
'''


defaultProtocols = {
    "default": default,
    "add_crc16": add_crc16,
    "add_sum": add_sum,
}
ignoreList = ["maix-smart"]

for file in os.listdir(protocols_dir):
    name, ext = os.path.splitext(file)
    if name in ignoreList:
        continue
    if ext.endswith(".py"):
        with open(os.path.join(protocols_dir, file)) as f:
            code = f.read()
            defaultProtocols[name] = code


