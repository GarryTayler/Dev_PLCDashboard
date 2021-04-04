from multiprocessing import shared_memory
from app.helper.const import uiSizeAnalog, uiSizeDigital, uiSizeString, uiSizeTime, uiSizeDate, Const_BOOL, Const_WORD,\
    Const_LREAL, Const_WString, Const_String, defaultDecode, Bytes2Int, uiSizeUIWrite, unicodeDecode, Const_UINT
import struct

Const_Digital = "digital"
Const_Analog = "analog"
Const_WsString = "string"
Const_STime = "time"
Const_SDate = "date"
Const_RemoteSize = 56320
Const_Unit = b'"'

WsString_Start = Const_BOOL * uiSizeDigital + uiSizeAnalog * Const_LREAL
STime_Start = WsString_Start + uiSizeString * Const_WString(32)
SDate_Start = STime_Start + Const_String(12) * uiSizeTime

Remote_Step = 56320
Write_Step = 294

VARIABLE_CONST = {
    Const_Digital: {
        'step': Const_BOOL,
        'start': 0,
        'len': uiSizeDigital,
        'decode': defaultDecode,
        'type': 1
    },
    Const_Analog: {
        'step': Const_LREAL,
        'start': Const_BOOL * uiSizeDigital,
        'len': uiSizeAnalog,
        'decode': 'utf8',
        'type': 2
    },
    Const_WsString: {
        'step': Const_WString(32),
        'start': WsString_Start,
        'len': uiSizeString,
        'decode': unicodeDecode,
        'type': 3
    },
    Const_STime: {
        'step': Const_String(12),
        'start': STime_Start,
        'len': uiSizeTime,
        'decode': defaultDecode,
        'type': 4
    },
    Const_SDate: {
        'step': Const_String(10),
        'start': SDate_Start,
        'len': uiSizeDate,
        'decode': defaultDecode,
        'type': 5
    }
}


def parse_utf16(byte_str):
    return_ind = byte_str.find(Const_Unit)
    byte_str = byte_str[return_ind + 1:]
    while byte_str.find(Const_Unit) >= 0:
        ind1 = byte_str.find(Const_Unit)
        return_ind += ind1 + 1
        byte_str = byte_str[ind1 + 1:]

    return return_ind


class SharedMem_LocalVar: # shared memory에서 변수 읽기 / 쓰기
    def __init__(self, local_type='local'):
        #shared memory 읽기부분
        if local_type == "local":
            self._SharedMem = "_SharedMem_LocalVar"
        elif local_type == "remote":
            self._SharedMem = "_SharedMem_RemoteVar"
        #shared_memory 쓰기부분
        self._WriteMem = "_SharedMem_UI_Write"

    def set_buff(self, var_address, var_type, var_val):
        write_shm = shared_memory.SharedMemory(self._WriteMem)  #Attach _SharedMem_UI_Write
        uiCnt = int(struct.unpack('H', bytes(write_shm.buf[0:2]))[0])
        if uiCnt < uiSizeUIWrite:
            exist_flag = False
            var_str = ('"' + var_val + '"').encode(unicodeDecode)
            start_ind = var_str.find(Const_Unit)
            end_ind = start_ind + parse_utf16(var_str[start_ind + 1:])
            var_str = var_str[start_ind + 1:start_ind + end_ind - 1]
            for i in range(uiCnt):
                var_start = Const_UINT + i * Write_Step
                var_end = var_start + Const_String(32)
                byte_arr = bytes(write_shm.buf[var_start:var_end])
                var_add = (byte_arr.replace(b'\x00', b'')).decode(defaultDecode)

                if var_add == var_address:
                    var_start = var_end + Const_WORD
                    for ii in range(Const_WString(128) + 1):
                        ii_ind = var_start + ii
                        write_shm.buf[ii_ind:ii_ind + 1] = b'\x00'

                    write_shm.buf[var_start:var_start + len(var_str)] = var_str

                    exist_flag = True
                    break

            if not exist_flag:
                var_start = Const_UINT + uiCnt * Write_Step
                var_address = var_address.encode()
                write_shm.buf[var_start:var_start + len(var_address)] = var_address

                var_start = var_start + Const_String(32) + Const_WORD
                var_type_val = VARIABLE_CONST[var_type]['type']
                var_type_val = bytes([var_type_val])
                write_shm.buf[var_start - len(var_type_val):var_start] = var_type_val

                write_shm.buf[var_start:var_start + len(var_str)] = var_str

                uiCnt += 1
                write_shm.buf[0:2] = struct.pack('H', uiCnt)
            resp = {'status': True}
        else:
            resp = {'status': False, 'message': '더이상 수정할수 없습니다.'}

        return resp

    def get_buff(self, buf_type='', start=0, end=0, remoteInd=0):
        buffArr = []
        if len(buf_type) == 0:
            return buffArr

        var_type = VARIABLE_CONST[buf_type]
        step = var_type['step']
        var_start = var_type['start'] + start * step + remoteInd * Remote_Step
        shm = shared_memory.SharedMemory(self._SharedMem)
        for i in range(start, end):
            var_end = var_start + step
            decode = var_type['decode']
            byteArr = bytes(shm.buf[var_start:var_end])

            if buf_type == Const_Digital:
                buffArr.append({'key': i - start, 'val': "TRUE" if Bytes2Int(byteArr) == 1 else "FALSE"})
            elif buf_type == Const_Analog:
                sel_value = str(struct.unpack('d', byteArr)[0])
                if '.' in sel_value:
                    sel_val_arr = sel_value.split('.')
                    dot_val = sel_val_arr[1].replace('0', '')
                    sel_value = sel_value if len(dot_val) > 0 else sel_val_arr[0]

                buffArr.append({'key': i - start, 'val': sel_value})
            else:
                if decode == unicodeDecode:
                    ind = byteArr.find(b'\x00\x00')
                    decode = defaultDecode if ind == 0 else decode
                    byteArr = byteArr[:ind + 1] if ind == 0 else byteArr
                elif decode == defaultDecode:
                    ind = byteArr.find(b'\x00')
                    byteArr = byteArr[:ind + 1]

                decode = decode if len(decode) > 0 else defaultDecode
                buffArr.append({'key': i - start, 'val': byteArr.decode(decode)})

            var_start = var_end

        return buffArr
