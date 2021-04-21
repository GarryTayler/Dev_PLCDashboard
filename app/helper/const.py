uiSizeDigital = 2048
uiSizeAnalog = 1024
uiSizeString = 512
uiSizeTime = 512
uiSizeDate = 512
uiSizeUIWrite = 1024

uiSizeEval = 256
uiSizeEvalGrp = 256
uiSizeCtrl = 256
uiSizeCtrlPanel = 256
uiSizeAct = 256
uiSizeActGrp = 256
uiSizeTimePeriod = 24

uiSizeModbus = 32
uiSizeModbusGlobalMapping = 2048
uiSizeModbusMasterChannel = 64
uiSizeModbusMasterChannelMapping = 1024
uiSizeModbusSlaveMem = 1024
uiSizeModbusSlaveMapping = 1024

uiSizeRemoteConn = 64
uiSizeRemoteRWList = 1024

Const_BOOL = Const_BYTE = Const_SINT = Const_USINT = 1
Const_INT = Const_UINT = Const_WORD = 2
Const_DINT = Const_UDINT = Const_DWORD = Const_REAL = 4
Const_LREAL = 8

uiSizeRecipeDef = 16
uiSizeRecipeVars = 128
uiSizeRecipe = 64

uiSizeAlarm = 256

uiSizeUserDefComm = 16
uiSizeUserDefCommFrame = 32
uiSizeUserDefCommSeq = 32
uiSizeUserDefCommSegByteLength = 64
uiSizeUserDefCommSeg = 16
uiSizeUserDefCommTCPConn = 32

uiSizeRemoteDevice = 64

defaultDecode = "1250"
unicodeDecode = "utf16"


def Const_String(n):
    return n + 1


def Const_WString(n):
    return (n + 1) * 2


def Bytes2Int(byteStr):
    return int.from_bytes(byteStr, 'big')


# def parse_wstring(byteArr):
#     ind = byteArr.find(b'\x00\x00')
#     print(ind)
#     decode = defaultDecode if ind == 0 else 'utf16'
#     # byteArr = byteArr[:ind + 1] if ind == 0 else byteArr
#     byteArr = byteArr[:ind + 2] if ind > 0 else byteArr
#     print(byteArr)
#     return byteArr.decode(decode)


def parse_wstring(byteArr):
    ind = byteArr.find(b'\x00\x00')
    decode = defaultDecode if ind == 0 else 'utf16'
    decodeStr = byteArr.decode(decode)
    # print(decodeStr)
    ind = decodeStr.find('\x00')
    # print(ind)
    return decodeStr[:ind] if ind > 0 else decodeStr
