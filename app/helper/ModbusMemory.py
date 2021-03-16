from multiprocessing import shared_memory
from app.helper.const import Const_BOOL, Const_WString, parse_wstring, Bytes2Int, uiSizeModbusMasterChannel

Const_Step = (uiSizeModbusMasterChannel + 1) * (2 * Const_BOOL + Const_WString(32))


class Modbus_Memory:
    def __init__(self):
        self._Shm = shared_memory.SharedMemory("_SharedMem_Modbus")

    def get_modbus_chl(self, start=0):
        channel_list = []
        var_end = Const_Step * start + 2 * Const_BOOL + Const_WString(32)
        for i in range(uiSizeModbusMasterChannel):
            var_start = var_end
            var_end = var_start + Const_BOOL
            okVal1 = Bytes2Int(bytes(self._Shm.buf[var_start:var_end])) == 1

            var_start = var_end
            var_end = var_start + Const_BOOL
            errVal1 = Bytes2Int(bytes(self._Shm.buf[var_start:var_end])) == 1

            var_start = var_end
            var_end = var_start + Const_WString(32)
            status1 = parse_wstring(bytes(self._Shm.buf[var_start:var_end]))

            channel_list.append({'ok': okVal1, 'err': errVal1, 'status': status1})

        return channel_list

    def get_modbus(self, start=0):
        var_start = Const_Step * start
        var_end = var_start + Const_BOOL
        okVal = Bytes2Int(bytes(self._Shm.buf[var_start:var_end])) == 1

        var_start = var_end
        var_end = var_start + Const_BOOL
        errVal = Bytes2Int(bytes(self._Shm.buf[var_start:var_end])) == 1

        var_start = var_end
        var_end = var_start + Const_WString(32)
        status = parse_wstring(bytes(self._Shm.buf[var_start:var_end]))

        return {'ok': okVal, 'err': errVal, 'status': status}
