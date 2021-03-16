from multiprocessing import shared_memory
from app.helper.const import Const_BOOL, Const_WString, parse_wstring, Bytes2Int, uiSizeRemoteDevice, Const_String

Local_Start = (2 * Const_BOOL + Const_WString(32)) * uiSizeRemoteDevice


class RemoteDevice_Memory:
    def __init__(self):
        self._Shm = shared_memory.SharedMemory("_SharedMem_RemoteDevice")

    def get_remote_clients(self):
        var_end = 0
        client_arr = []
        for i in range(uiSizeRemoteDevice):
            var_start = var_end
            var_end = var_start + Const_BOOL
            conVal = Bytes2Int(bytes(self._Shm.buf[var_start:var_end])) == 1

            var_start = var_end
            var_end = var_start + Const_BOOL
            errVal = Bytes2Int(bytes(self._Shm.buf[var_start:var_end])) == 1

            var_start = var_end
            var_end = var_start + Const_WString(32)
            status = parse_wstring(bytes(self._Shm.buf[var_start:var_end]))

            client_arr.append({'con': conVal, 'err': errVal, 'status': status})

        return client_arr

    def get_local_status(self):
        var_start = Local_Start
        var_end = var_start + Const_BOOL
        okVal = Bytes2Int(bytes(self._Shm.buf[var_start:var_end])) == 1

        var_start = var_end
        var_end = var_start + Const_BOOL
        errVal = Bytes2Int(bytes(self._Shm.buf[var_start:var_end])) == 1

        var_start = var_end
        var_end = var_start + Const_WString(32)
        status = parse_wstring(bytes(self._Shm.buf[var_start:var_end]))

        client_arr = []
        for i in range(uiSizeRemoteDevice):
            var_start = var_end
            var_end = var_start + Const_BOOL
            conVal = Bytes2Int(bytes(self._Shm.buf[var_start:var_end]))

            if conVal == 1:
                var_start = var_end
                var_end = var_start + Const_String(15)
                ipVal = (bytes(self._Shm.buf[var_start:var_end])).decode('utf8')

                var_start = var_end
                var_end = var_start + Const_WString(32)
                curVal = parse_wstring(bytes(self._Shm.buf[var_start:var_end]))

                client_arr.append({'con': conVal, 'ip': ipVal, 'status': curVal})
            else:
                var_end = var_end + Const_String(15) + Const_WString(32)

        return {'ok': okVal, 'err': errVal, 'status': status, 'clients': client_arr}
