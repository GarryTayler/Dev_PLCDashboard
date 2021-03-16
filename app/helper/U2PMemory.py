from multiprocessing import shared_memory
from app.helper.const import Bytes2Int


class U2p_Logic:
    def __init__(self):
        self._SharedMem = "_SharedMem_General_U2P"

    def change_run_mode(self, run_mode=0):
        shm = shared_memory.SharedMemory(self._SharedMem)
        shm.buf[0:1] = bytes([run_mode])
        shm.buf[1:2] = bytes([run_mode])
        shm.close()

    def get_run_mode(self):
        shm = shared_memory.SharedMemory(self._SharedMem)
        return Bytes2Int(bytes(shm.buf[0:1]))
