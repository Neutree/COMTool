from struct import pack, unpack

def plot_pack(name:str, x:float, y:float, header= b'\xAA\xCC\xEE\xBB'):
    name = name.encode()
    f = header
    f+= pack("B", len(name ))
    f+=name
    f += pack("d", x)
    f += pack("d", y)
    f += pack("B", sum(f)%256)
    return f
