
from datetime import datetime
import binascii
import re

def datetime_format_ms(dt):
    res = dt.strftime("%Y-%m-%d %H:%M:%S")
    return '{}.{:03d}'.format(res, int(round(dt.microsecond/1000)))

def hexlify(bs, sed=b' '):
    tmp = b'%02X' + sed.encode()
    return b''.join([tmp % b for b in bs])

def bytes_to_hex_str(strB : bytes) -> str:
    strHex = binascii.b2a_hex(strB).upper()
    return re.sub(r"(?<=\w)(?=(?:\w\w)+$)", " ", strHex.decode())+" "

def hex_str_to_bytes(hexString : str) -> bytes:
    dataList = hexString.split(" ")
    j = 0
    for i in dataList:
        if len(i) > 2:
            return -1
        elif len(i) == 1:
            dataList[j] = "0" + i
        j += 1
    data = "".join(dataList)
    try:
        data = bytes.fromhex(data)
    except Exception:
        return -1
    return data

def str_to_bytes(data:str, escape=False, encoding="utf-8"):
    if not escape:
        return data.encodeing(encoding)
    final = b""
    p = 0
    escapes = {
        "a": (b'\a', 2),
        "b": (b'\b', 2),
        "f": (b'\f', 2),
        "n": (b'\n', 2),
        "r": (b'\r', 2),
        "t": (b'\t', 2),
        "v": (b'\v', 2),
        "\\": (b'\\', 2),
        "\'": (b"'", 2),
        '\"': (b'"', 2),
    }
    octstr = ["0", "1", "2", "3", "4", "5", "6", "7"]
    while 1:
        idx = data[p:].find("\\")
        if idx < 0:
            final += data[p:].encode(encoding, "ignore")
            break
        final += data[p : p + idx].encode(encoding, "ignore")
        p += idx
        e = data[p+1]
        if e in escapes:
            r = escapes[e][0]
            p += escapes[e][1]
        elif e == "x": # \x01
            try:
                r = bytes([int(data[p+2 : p+4], base=16)])
                p += 4
            except Exception:
                msg = "Escape is on, but escape error:" + data[p : p+4]
                raise Exception(msg)
        elif e in octstr and len(data) > (p+2) and data[p+2] in octstr: # \dd or \ddd e.g. \001
            try:
                twoOct = False
                if len(data) > (p+3) and data[p+3] in octstr: # \ddd
                    try:
                        r = bytes([int(data[p+1 : p+4], base=8)])
                        p += 4
                    except Exception:
                        twoOct = True
                else:
                    twoOct = True
                if twoOct:
                    r = bytes([int(data[p+1 : p+3], base=8)])
                    p += 3
            except Exception as e:
                msg = "Escape is on, but escape error:" + data[p : p+4]
                raise Exception(msg)
        else:
            r = data[p: p+2].encode(encoding, "ignore")
            p += 2
        final += r
    return final


def can_draw(ucs4cp):
    return 0x2500 <= ucs4cp and ucs4cp <= 0x259F


