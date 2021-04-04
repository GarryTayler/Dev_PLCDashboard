from app import models, config


class ajaxReturn:
    draw = 0
    iTotalRecords = 0
    iTotalDisplayRecords = 0
    aaData = []


def datatable_head(postData):
    draw = postData.get('draw')
    start = int(postData.get('start'))
    length = int(postData.get('length'))
    columnIndex = postData.get('order[0][column]')
    columnName = postData.get('columns[' + columnIndex + '][data]') if columnIndex and len(columnIndex) > 0 else ''
    sortOrder = postData.get('order[0][dir]')

    return draw, start, length, columnIndex, columnName, sortOrder


def datatable_list(data_list, totalCount, draw):
    response = ajaxReturn()
    response.aaData = data_list
    response.draw = draw
    response.iTotalRecords = totalCount
    response.iTotalDisplayRecords = totalCount
    return response.__dict__


def get_remotes():
    return models.RemoteClient.query.with_entities(models.RemoteClient.id, models.RemoteClient.name, models.RemoteClient.remote_id).all()


def check_null(input_val=None):
    if input_val and len(input_val) > 0:
        return True
    else:
        return False


def get_desc_str(item):
    type1 = item['type']
    returnStr = ""
    if type1 == config.V_DIGITAL:
        opr = 'digital_select'
        if item[opr] in ['ON', 'OFF']:
            returnStr = item['digital_variable'] + " = " + item[opr]
        else:
            returnStr = item['digital_variable'] + " " + item[opr] + " " + item['digital_condition']

        returnStr += ', '
        if item['digital_option'] == 'NONE':
            returnStr += '옵션없음'
        elif item['digital_option'] == '2':
            returnStr += '유지시간: ' + item['digital_option_val']
        else:
            returnStr += '1펄스'
    elif type1 == config.V_ANALOG:
        returnStr = item['analog_variable'] + " " + item['analog_condition'] + " " + item['analog_value']

        returnStr += ', '
        if item['condition_option'] == 'NONE':
            returnStr += '옵션없음'
        elif item['condition_option'] == '2':
            returnStr += '유지시간: ' + item['analog_option_val']
        else:
            returnStr += '1펄스'
    elif type1 == config.V_SCHEDULE:
        returnStr = item['schedule_start'] + " ~ "
        if item['schedule_terminal'] == "DATE":
            returnStr += item['schedule_end']

        returnStr += ", " + item['schedule_repeat'] + config.VARIABLE_DAY[item['schedule_interval']] + "마다 반복, "

        if item['schedule_terminal'] == "NONE":
            returnStr += "종료없음"
        elif item['schedule_terminal'] == "DATE":
            returnStr += "종료일"
        else:
            returnStr += "실행횟수: " + item['schedule_count']

        if item['schedule_interval'] == "WEEK":
            selDays = item['schedule_days'].split(',')
            weekStr = '/'.join([config.VARIABLE_WEEK[day] for day in selDays])
            returnStr += ", " + weekStr if len(weekStr) > 0 else weekStr
    elif type1 == config.V_STRING:
        returnStr = item['string_variable'] + " " + item['string_condition'] + " " + item['string_value']

        returnStr += ', '
        if item['string_option'] == 'NONE':
            returnStr += '옵션없음'
        elif item['string_option'] == '2':
            returnStr += '유지시간: ' + item['string_option_val']
        else:
            returnStr += '1펄스'
    elif type1 == config.V_PERIOD:
        indArr = []
        for key, val in item.items():
            if 'start_period_' in key or 'end_period_' in key:
                splitVal = key.split('_')
                if len(splitVal) == 3 and not splitVal[2] in indArr:
                    indArr.append(splitVal[2])

        returnStr = ""
        for ind in indArr:
            if len(returnStr) == 0:
                returnStr = item['start_period_' + ind] + " ~ " + item['end_period_' + ind]
            else:
                returnStr += ", " + item['start_period_' + ind] + " ~ " + item['end_period_' + ind]

        if item['interval_option'] == "NONE":
            returnStr += ", 옵션없음"
        else:
            returnStr += ", 1펄스"
    elif type1 == config.V_CLOCK:
        returnStr = item['cycle_value']
    elif type1 == config.V_CHANGE:
        returnStr = item['differ_variable']
    elif type1 == config.V_REFER:
        returnStr = item['refer_cond_select'] + " " + item['refer_condition'] + ", "
        if item['differ_option'] == "NONE":
            returnStr += "옵션없음"
        elif item['differ_option'] == "2":
            returnStr += "유지시간 " + item['differ_option_time']
        else:
            returnStr += "1펄스"
    elif type1 == config.V_ALARM:
        returnStr = item['alarm_select'] + ", "
        if item['alarm_option'] == "NONE":
            returnStr += "옵션없음"
        elif item['alarm_option'] == "2":
            returnStr += "유지시간 " + item['differ_option_time']
        else:
            returnStr += "1펄스"

    return returnStr


def get_desc_str1(item):
    type1 = item['type']
    returnStr = ""
    if type1 in [config.V_DIGITAL, config.V_ANALOG, config.V_STRING, config.V_TIME, config.V_DATE]:
        type1 = type1.lower()
        returnStr = item[type1 + '_variable'] + " -> " + item[type1 + '_value']
    elif type1 == config.V_DELAY:
        returnStr = item['delay_value'] + " 지연"
    elif type1 == config.V_UCALC:
        returnStr = item['formula_variable'] + " = " + item['formula_value']
    elif type1 == config.V_FUNC:
        returnStr = item['func_select']
    elif type1 == config.V_RECIPE:
        returnStr = item['recipe_value']
    elif type1 == config.V_SHELLEXEC:
        returnStr = item['shell_application'] + ", " + item['shell_param'] + ", "
        if item['shell_exec'] == "1":
            returnStr += "숨김, "
        returnStr += config.SHELL_DUPLICATE[item['shell_duplicate']]
    elif type1 == config.V_CUSTOM:
        selChl = models.CustomChannel.query.filter_by(id=item['channel_id']).first()
        selFrame = models.CustomFrame.query.filter_by(id=item['frame_id']).first()
        returnStr = selChl.name if selChl else ""
        returnStr = returnStr + ", " + (selFrame.name if selFrame else "")
    elif type1 == config.V_GROUPACT:
        selActGroup = models.ActionGroup.query.filter_by(id=item['actgroup_id']).first()
        returnStr = selActGroup.name if selActGroup else ""
    elif type1 == config.V_CONTROL:
        selControl = models.Control.query.filter_by(id=item['control_id']).first()
        returnStr = selControl.name if selControl else ""

    returnStr += ", 실행순서: " + str(item['order'])
    return returnStr


def get_ethercat():
    selModel = models.Settings
    ethercat_item = selModel.query.filter_by(name='ethercat_use').first()
    ethercat_use = True if ethercat_item and ethercat_item.value == '1' else False
    ethercat_item = selModel.query.filter_by(name='ethercat_try').first()
    ethercat_try = True if ethercat_item and ethercat_item.value == '1' else False
    return ethercat_use, ethercat_try
