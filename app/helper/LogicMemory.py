from multiprocessing import shared_memory
from app.helper.const import uiSizeEval, uiSizeEvalGrp, uiSizeAct, uiSizeActGrp, uiSizeCtrl, uiSizeCtrlPanel, \
    Const_BOOL, Const_WString, Const_INT, Bytes2Int, parse_wstring

Const_Condition = "condition"
Const_CondGroup = "cond_group"
Const_Action = "action"
Const_ActGroup = "act_group"
Const_Control = "control"
Const_Logic = "logic"

Action_Step = 3 * Const_BOOL + Const_WString(32)
ActGrp_Step = Action_Step - Const_BOOL + Const_INT
Control_Step = Action_Step + Const_BOOL

ActGrp_Start = Const_BOOL * (uiSizeEval + uiSizeEvalGrp) + Action_Step * uiSizeAct
Control_Start = ActGrp_Start + ActGrp_Step * uiSizeActGrp

VARIABLE_CONST = {
    Const_Condition: {
        'step': Const_BOOL,
        'start': 0,
        'len': uiSizeEval
    },
    Const_CondGroup: {
        'step': Const_BOOL,
        'start': Const_BOOL * uiSizeEval,
        'len': uiSizeEvalGrp
    },
    Const_Action: {
        'step': Action_Step,
        'start': Const_BOOL * (uiSizeEval + uiSizeEvalGrp),
        'len': uiSizeAct
    },
    Const_ActGroup: {
        'step': ActGrp_Step,
        'start': ActGrp_Start,
        'len': uiSizeActGrp
    },
    Const_Control: {
        'step': Control_Step,
        'start': Control_Start,
        'len': uiSizeCtrl
    },
    Const_Logic: {
        'step': Const_INT,
        'start': Control_Start + Control_Step * uiSizeCtrl,
        'len': uiSizeCtrlPanel
    }
}


class SharedMem_Logic:
    def __init__(self):
        self._SharedMem = "_SharedMem_Logic"

    def get_buff(self, buf_type='', start=0, end=0):
        buffArr = []
        if len(buf_type) == 0:
            return buffArr

        var_type = VARIABLE_CONST[buf_type]
        step = var_type['step']
        var_start = var_type['start'] + start * step

        shm = shared_memory.SharedMemory(self._SharedMem)
        for i in range(start, end):
            var_end = var_start + step
            if buf_type in [Const_Condition, Const_CondGroup, Const_Logic]:
                buffArr.append({'val': Bytes2Int(bytes(shm.buf[var_start:var_end]))})
            elif buf_type == Const_Action:
                var_end1 = var_start + Const_BOOL
                busyVal = Bytes2Int(bytes(shm.buf[var_start:var_end1])) == 1
                var_start = var_end1
                var_end1 = var_start + Const_BOOL
                doneVal = Bytes2Int(bytes(shm.buf[var_start:var_end1])) == 1
                var_start = var_end1
                var_end1 = var_start + Const_BOOL
                errVal = Bytes2Int(bytes(shm.buf[var_start:var_end1])) == 1

                buffArr.append({'status': parse_wstring(bytes(shm.buf[var_end1:var_end])), 'busy': busyVal,
                                'done': doneVal, 'err': errVal})
            elif buf_type == Const_ActGroup:
                var_end1 = var_start + Const_BOOL
                doneVal = Bytes2Int(bytes(shm.buf[var_start:var_end1])) == 1
                var_start = var_end1
                var_end1 = var_start + Const_BOOL
                busyVal = Bytes2Int(bytes(shm.buf[var_start:var_end1])) == 1

                var_start = var_end1
                var_end1 = var_start + Const_WString(32)
                cntVal = Bytes2Int(bytes(shm.buf[var_end1:var_end]))

                buffArr.append({'status': parse_wstring(bytes(shm.buf[var_start:var_end1])), 'busy': busyVal,
                                'done': doneVal, 'cnt': cntVal})
            elif buf_type == Const_Control:
                var_end1 = var_start + Const_BOOL
                validVal = Bytes2Int(bytes(shm.buf[var_start:var_end1])) == 1
                var_start = var_end1
                var_end1 = var_start + Const_BOOL
                busyVal = Bytes2Int(bytes(shm.buf[var_start:var_end1])) == 1
                var_start = var_end1
                var_end1 = var_start + Const_BOOL
                doneVal = Bytes2Int(bytes(shm.buf[var_start:var_end1])) == 1

                var_start = var_end1
                var_end1 = var_start + Const_WString(32)
                supVal = Bytes2Int(bytes(shm.buf[var_end1:var_end]))

                buffArr.append({'status': parse_wstring(bytes(shm.buf[var_start:var_end1])), 'busy': busyVal,
                                'done': doneVal, 'sup': supVal, 'valid': validVal})

            var_start = var_end

        return buffArr
