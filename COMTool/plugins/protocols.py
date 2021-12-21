default = '''
def decode(data):
    return data

def encode(data):
    return data
'''


maix_mm = '''
import json

version = 1
crc16 = crc.crc16
# cmd enum
CMD_KEY  = 1

class Base:
    def __init__(self, body = b''):
        if body:
            self.decode(body)

    def decode(self, body):
        raise NotImplementedError()

    def encode(self):
        raise NotImplementedError()

class Data_KEY(Base):
    name = "key"
    map = {
        119: "w",
        97: "a",
        100: "s",
        115: "d",
        13: "enter",
        27: "esc"
    }
    def __init__(self, body=b'', num=0, k="", v=1):
        self.map2 = {v : k for k, v in self.map.items()}
        self.k = k
        if self.k and self.k in self.map2:
            self.num = self.map2[self.k]
        else:
            self.num = num
        self.v = v   # 0: release, 1: press, 2: long press
        super().__init__(body=body)

    def decode(self, body):
        self.num = unpack("i", body[:4])[0]
        if self.num in self.map:
            self.k = self.map[self.num]
        self.v = unpack("B", body[4:5])[0]

    def encode(self):
        p = pack("i", self.num)
        p += pack("B", self.v)
        return p

    def __str__(self) -> str:
        ret = {
            "type": self.name,
            "value": self.v,
            "key number": self.num,
            "key name": self.k
        }
        return json.dumps(ret)

def encode(data:bytes):
    cmd = data[0]
    body = data[1:]
    header = b'\\xAA\\xCA\\xAC\\xBB'
    data_len = len(body) + 1
    data_len = pack("I", data_len)
    frame = header + bytes([version]) + data_len + bytes([cmd]) + body
    _crc = crc16(frame)
    _crc = pack("H", _crc)
    frame += _crc
    print(frame)
    return frame

def _decode(raw : bytes):
    # find valid header and body, and check parity sum
    if not raw:
        return None, None, raw
    idx = raw.find(b'\\xAA\\xCA\\xAC\\xBB')
    if idx < 0:
        return None, None, raw
    raw = raw[idx:]
    # check frame length, not enough a frame
    if len(raw) < 12:
        return None, None, raw
    _version = raw[4]
    if _version != version:
        print(f"protocol version is {_version}, but support is {version}")
        return None, None, raw
    # get length
    length = unpack("I", raw[5:9])[0]
    # get cmd type
    cmd = raw[9]
    # check body length, not enough body
    if len(raw) < length + 11:
        return None, None, raw
    # checksum
    crc0 = unpack("H", raw[9 + length : 11 + length])[0]
    _crc = crc16(raw[:9 + length])
    if crc0 != _crc:
        raw = raw[11+length:]
        return None, None, None
    # get body
    body = raw[10:length + 9]
    if cmd == CMD_KEY:
        data = Data_KEY(body=body)
    else:
        data = body
    # remove parsed bytes
    raw = raw[11+length:]
    return cmd, data, raw

def decode(raw:bytes):
    cmd, data, raw = _decode(raw)
    if not cmd:
        return b''
    if type(data) == bytes:
        return bytes([cmd])+data
    return str(data)
'''

defaultProtocols = {
    "default": default,
    "maix-mm": maix_mm
}

