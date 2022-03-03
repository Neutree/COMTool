try:
    import parameters
except ImportError:
    from COMTool import parameters
import os

protocols_dir = os.path.join(parameters.dataPath, "protocols")

default = '''
def decode(data):
    return data

def encode(data):
    return data
'''

defaultProtocols = {
    "default": default,
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


