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
CMD_OK             = 0x00
CMD_ERROR          = 0xFF
CMD_KEY            = 0x01
CMD_APP_LIST       = 0x02
CMD_CUR_APP_INFO   = 0x03
CMD_APP_INFO       = 0x04
CMD_START_APP      = 0x05
CMD_EXIT_APP       = 0x06
CMD_APP_CMD        = 0x08

CMD_RESPONSE_MASK  = 0x80

class Base:
    name = ""
    def __init__(self, request=True, body = b''):
        self.request = request
        if body:
            self.decode(body)

    def decode(self, body):
        raise NotImplementedError()

    def encode(self):
        raise NotImplementedError()

class Data_OK(Base):
    name = ""
    def __init__(self, request=False, body = b''):
        super().__init__(request, body=body)

    def decode(self, body):
        pass

    def encode(self):
        return b''

class Data_ERROR(Base):
    name = ""
    def __init__(self, request=False, body = b'', msg = ''):
        self.msg = msg
        super().__init__(request, body=body)

    def decode(self, body):
        self.msg = body.decode("utf-8")

    def encode(self):
        return self.msg.encode("utf-8")

class Data_KEY(Base):
    '''
        simulate keyboard input, only have request format:
        |   name  | cmd(1B)     | key(4B) | value(1B) |
        | ------- | ----------- | ------------- | --------- |
        | example | 0x01(fixed) | 0x00000026(LE)    | 0x01(/0x00/0x02) |
        e.g. [0x01, 0x26, 0x00, 0x00, 0x00, 0x01]
        cmd: fixed 0x01
        key: little edian 4 bytes data, value can be:
            38: "up"
            40: "down"
            37: "left"
            39: "right"
            108: "enter"
            27: "esc"
            0x01010101: "ok"
            0x02020202: "ret"
            0x03030303: "pre"
            0x04040404: "next"
        value: key value, can be 0x01(pressed),0x02(long pressed), 0x00(released)
    '''
    name = "key"
    map = {
        38: "up",
        40: "down",
        37: "left",
        39: "right",
        108: "enter",
        27: "esc",
        0x01010101: "ok",
        0x02020202: "ret",
        0x03030303: "pre",
        0x04040404: "next",
    }
    def __init__(self, request = True, body=b'', num=0, k="", v=1):
        self.map2 = {v : k for k, v in self.map.items()}
        self.k = k
        if self.k and self.k in self.map2:
            self.num = self.map2[self.k]
        else:
            self.num = num
        self.v = v   # 0: release, 1: press, 2: long press
        super().__init__(request, body=body)

    def decode(self, body):
        '''
            @body 4 bytes(int32 type) key, little edian, e.g. b'\x73\x00\x00\x00', 1 byte(uint8 type) value: b'\x01'
        '''
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
        return json.dumps(ret, ensure_ascii=False)

class Data_APP_List(Base):
    '''
        get app list command,
            request format:
                |   name  | cmd(1B) | 
                | ------- | ------- |
                | example | 0x02    |
            response format:
                |   name  | cmd(1B) | number(1B) | app 0 info(id_len(1B),id,name_len(1B),name,brief_len(1B),brief| ... | app n info |
                | ------- | ------- | ---------- | ---------- | ----- |  ------ |
                | example | 0x82    |    0x05    | [4, 'face', 4, 'face', 11, 'face detect'] | ... | ... |
    '''
    name = "app list"
    def __init__(self, request = True,  body=b'', apps = []):
        self.apps = apps
        super().__init__(request, body=body)

    def decode(self, body):
        if self.request:
            return
        self.apps = []
        self.num = unpack("B", body[0:1])[0]
        p = 1
        idx = 0
        while 1:
            id_len = unpack("B", body[p:p+1])[0]
            p += 1
            id = body[p : p + id_len]
            p += id_len
            name_len = unpack("B", body[p:p+1])[0]
            p += 1
            name = body[p : p + name_len]
            p += name_len
            brief_len = unpack("B", body[p:p+1])[0]
            p += 1
            brief = body[p : p + brief_len]
            p += brief_len
            app = {
                "idx": idx,
                "id": id.decode("utf-8"),
                "name": name.decode("utf-8"),
                "brief": brief.decode("utf-8")
            }
            self.apps.append(app)
            idx += 1
            if p >= len(body):
                break

    def encode(self):
        if self.request:
            return b''
        frame = pack("B", len(self.apps))
        for app in self.apps:
            # id
            id = app["id"].encode("utf-8")
            frame += pack("B", len(id))
            frame += id
            # name
            name = app["name"].encode("utf-8")
            frame += pack("B", len(name))
            frame += name
            # brief
            brief = app["brief"].encode("utf-8")
            frame += pack("B", len(brief))
            frame += brief
        return frame

    def __str__(self) -> str:
        if self.request:
            ret = {
                "type": self.name,
                "request": self.request,
            }
        else:
            ret = {
                "type": self.name,
                "request": self.request,
                "app num": self.num,
                "apps": self.apps
            }
        return json.dumps(ret, ensure_ascii=False)

class Data_CUR_APP_Info(Base):
    '''
        get current app info command,
            request format:
                |   name  | cmd(1B) | 
                | ------- | ------- |
                | example | 0x03    |
            response format:
                |   name  | cmd(1B) |  idx(1B)                 | app 0 info(id_len(1B),id,name_len(1B),name,brief_len(1B),brief|
                | ------- | ------- | ------------------------ | ---------- |
                | example | 0x83    |    0x02(0xFF means home) | [4, 'face', 4, 'face', 11, 'face detect'] |
    '''
    name = "cur app info"
    def __init__(self, request = True,  body=b'', app_id = "", apps = []):
        self.apps = apps
        self.app_id = app_id
        super().__init__(request, body=body)

    def decode(self, body):
        if self.request:
            return
        self.idx = unpack("B", body[0:1])[0]
        p = 1
        id_len = unpack("B", body[p:p+1])[0]
        p += 1
        id = body[p : p + id_len]
        p += id_len
        name_len = unpack("B", body[p:p+1])[0]
        p += 1
        name = body[p : p + name_len]
        p += name_len
        brief_len = unpack("B", body[p:p+1])[0]
        p += 1
        brief = body[p : p + brief_len]
        p += brief_len
        self.app = {
            "idx": self.idx,
            "id": id.decode("utf-8"),
            "name": name.decode("utf-8"),
            "brief": brief.decode("utf-8")
        }

    def encode(self):
        if self.request:
            return b''
        idx = -1
        if self.app_id == "home":
            idx = 0xff
            app = {
                "id": "home",
                "name": "home",
                "brief": "home"
            }
        else:
            for i, app in enumerate(self.apps):
                print(self.app_id, app["id"])
                if self.app_id == app["id"]:
                    idx = i
                    break
            if idx < 0:
                return b''
            app = self.apps[idx]
        frame = pack("B", idx)
        # id
        id = app["id"].encode("utf-8")
        frame += pack("B", len(id))
        frame += id
        # name
        name = app["name"].encode("utf-8")
        frame += pack("B", len(name))
        frame += name
        # brief
        brief = app["brief"].encode("utf-8")
        frame += pack("B", len(brief))
        frame += brief
        return frame

    def __str__(self) -> str:
        if self.request:
            ret = {
                "type": self.name,
                "request": self.request,
            }
        else:
            ret = {
                "type": self.name,
                "request": self.request,
                "app": self.app
            }
        return json.dumps(ret, ensure_ascii=False)

class Data_APP_Info(Base):
    '''
        get app info command,
            request format:
                |   name  | cmd(1B) |  idx(1B)                           | app_id(nB) |  
                | ------- | ------- | ---------------------------------- | ------ | 
                | example | 0x04    | 0x02(set to 0xFF means not set)    | 'face'(if idx set, this can be empty) | 
            response format:
                |   name  | cmd(1B) | idx(1B) | app 0 info(id_len(1B),id,name_len(1B),name,brief_len(1B),brief|
                | ------- | ------- | ------- | ---------------- |
                | example | 0x84    |  0x02   | [4, 'face', 4, 'face', 11, 'face detect'] |
    '''
    name = "app info"
    def __init__(self, request = True,  body=b'', idx = 0xff, app_id = "", apps = []):
        self.apps = apps
        self.app_id = app_id
        self.idx = idx
        super().__init__(request, body=body)
        if not request:
            idx = -1
            if self.app_id == "home":
                idx = 0xff
                self.app = {
                    "id": "home",
                    "name": "home",
                    "brief": "home"
                }
            else:
                if self.idx != 0xFF:
                    idx = self.idx
                elif not self.app_id:
                    raise ValueError("idx or app_id should be provided")
                else:
                    for i, app in enumerate(self.apps):
                        if self.app_id == app["id"]:
                            idx = i
                            break
                self.app = self.apps[idx]
            self.idx = idx

    def decode(self, body):
        if self.request:
            self.idx = unpack("B", body[0:1])[0]
            self.app_id = body[1:].decode("utf-8")
            return
        self.idx = unpack("B", body[0:1])[0]
        p = 1
        id_len = unpack("B", body[p:p+1])[0]
        p += 1
        id = body[p : p + id_len]
        p += id_len
        name_len = unpack("B", body[p:p+1])[0]
        p += 1
        name = body[p : p + name_len]
        p += name_len
        brief_len = unpack("B", body[p:p+1])[0]
        p += 1
        brief = body[p : p + brief_len]
        p += brief_len
        self.app = {
            "idx": self.idx,
            "id": id.decode("utf-8"),
            "name": name.decode("utf-8"),
            "brief": brief.decode("utf-8")
        }

    def encode(self):
        if self.request:
            return b''
        frame = pack("B", self.idx)
        # id
        id = self.app["id"].encode("utf-8")
        frame += pack("B", len(id))
        frame += id
        # name
        name = self.app["name"].encode("utf-8")
        frame += pack("B", len(name))
        frame += name
        # brief
        brief = self.app["brief"].encode("utf-8")
        frame += pack("B", len(brief))
        frame += brief
        return frame

    def __str__(self) -> str:
        if self.request:
            ret = {
                "type": self.name,
                "request": self.request,
                "idx": self.idx,
                "app_id": self.app_id
            }
        else:
            ret = {
                "type": self.name,
                "request": self.request,
                "idx": self.idx,
                "app": self.apps
            }
        return json.dumps(ret, ensure_ascii=False)

class Data_START_APP(Base):
    '''
        start app command, only have request
            request format:
                |   name  | cmd(1B) |  idx(1B)                           | app_id(nB) |  
                | ------- | ------- | ---------------------------------- | ------ | 
                | example | 0x05    | 0x02(set to 0xFF means not set)    | 'face'(if idx set, this can be empty) | 
    '''
    name = "start app"
    def __init__(self, request = True,  body=b''):
        if not request:
            raise ValueError()
        super().__init__(request, body=body)

    def decode(self, body):
        self.idx = unpack("B", body[0:1])[0]
        self.app_id = body[1:].decode("utf-8")

    def encode(self):
        return b''

    def __str__(self) -> str:
        ret = {
            "type": self.name,
            "request": self.request,
            "idx": self.idx,
            "app_id": self.app_id
        }
        return json.dumps(ret, ensure_ascii=False)

class Data_EXIT_APP(Base):
    '''
        exit app command, only have request
            request format:
                |   name  | cmd(1B) |
                | ------- | ------- |
                | example | 0x06    |
    '''
    name = "exit app"
    def __init__(self, request = True,  body=b'',):
        if not request:
            raise ValueError()
        super().__init__(request, body=body)

    def decode(self, body):
        pass

    def encode(self):
        return b''

    def __str__(self) -> str:
        ret = {
            "type": self.name,
            "request": self.request
        }
        return json.dumps(ret, ensure_ascii=False)




cmd_class = {
    CMD_KEY: Data_KEY,
    CMD_APP_LIST: Data_APP_List,
    CMD_CUR_APP_INFO: Data_CUR_APP_Info,
    CMD_APP_INFO: Data_APP_Info,
    CMD_START_APP: Data_START_APP,
    CMD_EXIT_APP: Data_EXIT_APP,
}


def encode(data:bytes):
    cmd = data[0]
    body = data[1:]
    header = b'\xAA\xCA\xAC\xBB'
    data_len = len(body) + 1
    data_len = pack("I", data_len)
    frame = header + bytes([version]) + data_len + bytes([cmd]) + body
    _crc = crc16(frame)
    _crc = pack("H", _crc)
    frame += _crc
    print(frame)
    return frame


def _decode(raw : bytes):
    '''
        @raw protocol | header(4B) | version(1B) | data len(4B)(cmd + body)  | cmd(1B) | body(nB)     | CRC16_IBM(2B)(all previous) |
             decimal  | 3148663466 | 1           | 5                         | 1       | ...          | 1271                        |
               hex    | 0xBBACCAAA | 0x01        | 0x00000005                | 0x01    | 0x01000073   | 0x04F7                      |
             little edian when convert bytes to integer
             bytes: b'\xAA\xCA\xAC\xBB\x01\x06\x00\x00\x00\x01\x73\x00\x00\x00\x01\xf7\x04'
        @return (cmd, data, raw) 
                cmd 
                data 
                raw Data remaining after parsing
    '''
    # find valid header and body, and check parity sum
    if not raw:
        return None, None, raw
    idx = raw.find(b'\xAA\xCA\xAC\xBB')
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
    request = False if raw[9] & CMD_RESPONSE_MASK != 0 else True
    cmd = raw[9] & (~CMD_RESPONSE_MASK)
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
    try:
        if cmd in cmd_class:
            data = cmd_class[cmd](request, body=body)
        else:
            data = body
    except Exception as e:
        print("-- [ERROR] decode error" + str(e))
        raw = raw[11+length:]
        return None, None, raw
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

