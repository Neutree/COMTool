
from datetime import datetime
import binascii
import re

def datetime_format_ms(dt):
    res = dt.strftime("%Y-%m-%d %H:%M:%S.%M")
    return '{}.{:03d}'.format(res, int(round(dt.microsecond/1000)))


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


def can_draw(ucs4cp):
    return 0x2500 <= ucs4cp and ucs4cp <= 0x259F


