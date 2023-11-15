from struct import pack, unpack

def plot_pack(name:str, x:float, y:float, header= b'\xAA\xCC\xEE\xBB', binary = True):
    name = name.encode()
    if binary:
        f = header
        f+= pack("B", len(name ))
        f+=name
        f += pack("d", x)
        f += pack("d", y)
        f += pack("B", sum(f)%256)
    else:
        f = "${},{},{}".format(name, x, y).encode()
        checksum = sum(f) & 0xFF
        f += b',{:d}\n'.format(checksum)
    return f
