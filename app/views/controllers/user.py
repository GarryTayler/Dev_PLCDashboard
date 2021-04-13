from flask import render_template, Blueprint, session, redirect, request, flash, url_for
from app import models, db, config, main
from functools import wraps
from sqlalchemy.sql.expression import func
from app.helper.common import check_null, datatable_list, datatable_head, get_ethercat
from app.helper.config_helper import Config_Helper
from app.helper.U2PMemory import U2p_Logic
import json, gevent, os

config_helper = Config_Helper()
userbp = Blueprint('userbp', __name__, url_prefix='/user')

varOptions = ['1_PULSE', 'NONE']


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session.get('is_login'):
            return f(*args, **kwargs)
        else:
            return redirect('/user/login')

    return wrap


def auth_check(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        userID = session.get('user_id')
        path_auth = models.Authority.query.filter_by(userid=userID).filter_by(menu=main.get_menu()).first()
        if not path_auth or (path_auth.edit == "1" or path_auth.read == "1"):
            return f(*args, **kwargs)
        else:
            return redirect('/user/home')

    return wrap


def mode_check(mode='stop'):
    def mode_check_dec(f):
        @wraps(f)
        def wrap(*args, **kwargs):
            curModel = models.Settings.query.filter_by(name='mode').first()
            if curModel.value == mode:
                return f(*args, **kwargs)
            else:
                modeStr = '진입' if curModel.value == "run" else "Stop"
                return json.dumps({'status': False, 'message': modeStr + '모드에서는 진행할수 없습니다'})

        return wrap

    return mode_check_dec


@userbp.route('/home')
@login_required
def home():
    return render_template('user/home.html')


@userbp.route('/login')
def login():
    return render_template('user/login.html')


@userbp.route('/dologin', methods=['POST'])
def dologin():
    postData = request.values
    userid = postData.get('userid')
    passwd = postData.get('passwd')

    if check_null(userid) and check_null(passwd):
        sel_user = models.User.query.filter_by(userid=userid).first()
        if sel_user is not None and sel_user.check_password(passwd):
            session['is_login'] = True
            session['user_id'] = sel_user.id
            session['userid'] = sel_user.userid
            session['usertype'] = sel_user.usertype
            session['accept'] = sel_user.accept
            session['setting'] = sel_user.setting
            if sel_user.accept == 0 or sel_user.accept is None:
                return redirect(url_for('userbp.login'))
            elif sel_user.setting == 1:
                return redirect('/')
            else:
                return redirect(url_for('userbp.setting'))
        else:
            flash("로그인 정보가 정확하지 않습니다")
            return redirect(url_for('userbp.login'))
    else:
        flash("로그인 정보가 정확하지 않습니다")
        return redirect(url_for('userbp.login'))


@userbp.route('/logout')
@login_required
def logout():
    session.pop('is_login')
    session.pop('accept')
    session.pop('setting')
    return redirect('/')


@userbp.route('/users')
@login_required
def users():
    return render_template('setting/users.html')


@userbp.route('/register', methods=['POST'])
@login_required
def doregister():
    postData = request.values
    user_id = postData.get('user_id')
    user_type = postData.get('user_type')
    userid = postData.get('userid')
    userPW = postData.get('user_pw')
    if check_null(user_id) and check_null(user_type) and check_null(userid):
        selUser = models.User.query.filter_by(userid=user_id).first()
        if selUser is None or selUser.id == int(userid):
            if int(userid) == 0:
                newUser = models.User(
                    userid=user_id,
                    password=userPW,
                    usertype=user_type
                )

                db.session.add(newUser)
                db.session.commit()
                response = {'status': True}
            else:
                selUser = models.User.query.filter_by(id=userid).first()
                if selUser:
                    pwLen = len(userPW)
                    if pwLen > 0 and selUser.check_password(userPW):
                        selUser.userid = user_id
                        selUser.usertype = user_type
                        selUser.password = postData['conf_pw']
                        db.session.commit()
                        response = {'status': True}
                    elif pwLen == 0:
                        selUser.userid = user_id
                        selUser.usertype = user_type
                        db.session.commit()
                        response = {'status': True}
                    else:
                        response = {'status': False, 'message': '이전암호가 정확하지 않습니다'}
                else:
                    response = {'status': False, 'message': '유저가 존재하지 않습니다'}
        else:
            response = {'message': '이미 사용된 사용자이름입니다', 'status': False}
    else:
        response = {'message': '정보가 정확하지 않습니다', 'status': False}

    return json.dumps(response)


@userbp.route('/authority')
@login_required
def authority():
    selModel = models.User
    menuList = [
        {'id': 'variable', 'name': '변수'},
        {'id': 'condition', 'name': '조건'},
        {'id': 'condition_group', 'name': '조건그룹'},
        {'id': 'action', 'name': '동작'},
        {'id': 'action_group', 'name': '동작그룹'},
        {'id': 'control', 'name': '제어'},
        {'id': 'recipe', 'name': '레시피'},
        {'id': 'collect', 'name': '데이터수집'},
        {'id': 'alarm', 'name': '알람'},
        {'id': 'ethercat', 'name': 'EtherCAT I/O'},
        {'id': 'modbus', 'name': 'Modbus통신'},
        {'id': 'custom', 'name': '사용자정의통신'},
        {'id': 'remote', 'name': '리모트디바이스'}
    ]
    return render_template('setting/authority.html', menu_list=menuList,
                           users=selModel.query.with_entities(selModel.id, selModel.userid).all())


@userbp.route('/remove_user', methods=['POST'])
@login_required
def remove_user():
    postData = request.values
    selIDs = postData.get('selRow')
    if check_null(selIDs):
        selIDs = selIDs.split(",")
        for selid in selIDs:
            models.User.query.filter_by(id=selid).delete()

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@userbp.route('/export_setting')
@login_required
def export_setting():
    return render_template('setting/setting_export.html')


@userbp.route('/import_setting')
@login_required
def import_setting():
    return render_template('setting/setting_import.html')


@userbp.route('/alarms')
@login_required
def alarms():
    return render_template('setting/alarms.html')


@userbp.route('/interval')
@login_required
def interval():
    intervals = models.SettingInterval.query.all()
    int_list = {}
    for intItem in config.INTERVAL_LIST:
        itemVal = ""
        for intItem1 in intervals:
            if intItem1.set_name == intItem:
                itemVal = intItem1.interval
                break

        int_list[intItem] = itemVal
    return render_template('setting/interval.html', intervals=int_list)


def get_group_index(selModel, selid):
    selid = int(selid)
    return str(selModel.query.filter(selModel.id < selid).count() if selid > 0 else -1)


def write_default(section, default_item):
    typeArr = default_item.type.split('-')
    config_helper.set_value(section, config.VARIABLE_MATCH[typeArr[0]] + '.' + typeArr[1] + '.DEFAULT',
                            default_item.defaults)


def write_condition(section_name, condition, ind):
    prefixStr = 'EVAL.' + str(ind) + "."
    config_helper.set_value(section_name, prefixStr + "ENABLE", 'TRUE' if condition.use_flag == 1 else "FALSE")
    config_helper.set_value(section_name, prefixStr + "GROUP_INDEX", get_group_index(models.ConditionGroup, condition.condgroup))
    config_helper.set_value(section_name, prefixStr + "TYPE", condition.type)

    optionArr = json.loads(condition.options) if len(condition.options) > 0 else {}
    if condition.type == config.V_DIGITAL:
        config_helper.set_value(section_name, prefixStr + "VAR", optionArr['digital_variable_sellocstr'])
        config_helper.set_value(section_name, prefixStr + "OPR", optionArr['digital_select'])
        if optionArr['digital_select'] in ['!=', '=']:
            config_helper.set_value(section_name, prefixStr + "VAL", optionArr['digital_condition_sellocstr'])

        if optionArr['digital_option'] in varOptions:
            config_helper.set_value(section_name, prefixStr + "OPTION", optionArr['digital_option'])
        else:
            config_helper.set_value(section_name, prefixStr + "OPTION", optionArr['digital_option_val_sellocstr'] if 'digital_option_val_sellocstr' in optionArr else optionArr['digital_option_val'])
    elif condition.type == config.V_ANALOG:
        config_helper.set_value(section_name, prefixStr + "VAR", optionArr['analog_variable_sellocstr'])
        config_helper.set_value(section_name, prefixStr + "OPR", optionArr['analog_condition'])
        config_helper.set_value(section_name, prefixStr + "VAL", optionArr['analog_value_sellocstr'] if 'analog_value_sellocstr' in optionArr else optionArr['analog_value'])
        if optionArr['condition_option'] in varOptions:
            config_helper.set_value(section_name, prefixStr + "OPTION", optionArr['condition_option'])
        else:
            config_helper.set_value(section_name, prefixStr + "OPTION", optionArr['analog_option_val_sellocstr'] if 'analog_option_val_sellocstr' in optionArr else optionArr['analog_option_val'])
    elif condition.type == config.V_STRING:
        config_helper.set_value(section_name, prefixStr + "VAR", optionArr['string_variable_sellocstr'])
        config_helper.set_value(section_name, prefixStr + "OPR", optionArr['string_condition'])
        config_helper.set_value(section_name, prefixStr + "VAL", optionArr['string_value_sellocstr'] if 'string_value_sellocstr' in optionArr else optionArr['string_value'])
        config_helper.set_value(section_name, prefixStr + "OPTION", optionArr['string_option'])
        if optionArr['string_option'] == "MIN_PEND_TIME":
            config_helper.set_value(section_name, prefixStr + "MIN_PEND_TIME", optionArr[
                'string_option_val_sellocstr'] if 'string_option_val_sellocstr' in optionArr else optionArr[
                'string_option_val'])
    elif condition.type == config.V_SCHEDULE:
        config_helper.set_value(section_name, prefixStr + "SCH_START_DATE", optionArr['schedule_start'])
        termialVal = optionArr['schedule_terminal']
        intervalVal = optionArr['schedule_interval']
        if termialVal == "DATE":
            config_helper.set_value(section_name, prefixStr + "SCH_END_DATE", optionArr['schedule_end'])
        config_helper.set_value(section_name, prefixStr + "SCH_REPEAT_CYCLE", optionArr['schedule_repeat'])
        config_helper.set_value(section_name, prefixStr + "SCH_REPEAT_UNIT", intervalVal)
        config_helper.set_value(section_name, prefixStr + "SCH_END_OPTION", termialVal)
        if intervalVal == "WEEK":
            schedule_days = optionArr['schedule_days'].split(',')
            for i in range(7):
                config_helper.set_value(section_name, prefixStr + "SCH_WEEK_SEL." + str(i), 'TRUE' if str(i) in schedule_days else 'FALSE')
        if termialVal == "EXEC_NUM":
            config_helper.set_value(section_name, prefixStr + "SCH_EXEC_NUM", optionArr['schedule_count'])
    elif condition.type == config.V_PERIOD:
        for i in range(100):
            ii = i + 1
            startKey = "start_period_" + str(ii)
            endKey = "end_period_" + str(ii)
            if startKey in optionArr:
                config_helper.set_value(section_name, prefixStr + "TPD." + str(i) + ".START_TIME",
                                        optionArr[startKey + "_sellocstr"] if startKey + "_sellocstr" in optionArr else
                                        optionArr[startKey])
                config_helper.set_value(section_name, prefixStr + "TPD." + str(i) + ".END_TIME",
                                        optionArr[endKey + "_sellocstr"] if endKey + "_sellocstr" in optionArr else
                                        optionArr[endKey])
            else:
                break
    elif condition.type == config.V_CHANGE:
        config_helper.set_value(section_name, prefixStr + "VAR", optionArr['differ_variable_sellocstr'])
    elif condition.type == config.V_CLOCK:
        config_helper.set_value(section_name, prefixStr + "VAR",
                                optionArr['cycle_value_sellocstr'] if 'cycle_value_sellocstr' in optionArr else
                                optionArr['cycle_value'])
    elif condition.type == config.V_REFER:
        config_helper.set_value(section_name, prefixStr + "OPR", optionArr['refer_cond_select'])
        suffixStr = optionArr['alarm_differ'] + "."
        selModel = models.Condition if suffixStr == "EVAL." else models.ConditionGroup
        config_helper.set_value(section_name, prefixStr + "REF", suffixStr + get_group_index(selModel, optionArr[
            'refer_condition_condid'] if 'refer_condition_condid' in optionArr else optionArr[
            'refer_condition_condgroupid']))
    elif condition.type == config.V_ALARM:
        config_helper.set_value(section_name, prefixStr + "ALARM_INDEX",
                                get_group_index(models.Alarm, optionArr['alarm_select_selid']))


def write_condgroup(section_name, condgroup, ind):
    prefixStr = 'EVAL_GROUP.' + str(ind) + "."
    config_helper.set_value(section_name, prefixStr + "CTRL_INDEX", get_group_index(models.Control, condgroup.controlid))
    config_helper.set_value(section_name, prefixStr + "OPR", condgroup.operator)
    config_helper.set_value(section_name, prefixStr + "INVERT", 'TRUE' if condgroup.reverse == "1" else 'FALSE')


def write_action(section_name, action, ind):
    prefixStr = 'ACTION.' + str(ind) + "."
    config_helper.set_value(section_name, prefixStr + "ENABLE", 'TRUE' if action.use_flag == "1" else 'FALSE')
    config_helper.set_value(section_name, prefixStr + "GROUP_INDEX",
                            get_group_index(models.ActionGroup, action.actgroup))
    config_helper.set_value(section_name, prefixStr + "TYPE", action.type)
    optionArr = json.loads(action.options) if len(action.options) > 0 else {}
    if action.type == config.V_DIGITAL:
        config_helper.set_value(section_name, prefixStr + "VAR", optionArr['digital_variable_sellocstr'])
        config_helper.set_value(section_name, prefixStr + "VAL",
                                optionArr['digital_value_sellocstr'] if 'digital_value_sellocstr' in optionArr else
                                optionArr['digital_value'])
    elif action.type == config.V_ANALOG:
        config_helper.set_value(section_name, prefixStr + "VAR", optionArr['analog_variable_sellocstr'])
        config_helper.set_value(section_name, prefixStr + "VAL",
                                optionArr['analog_value_sellocstr'] if 'analog_value_sellocstr' in optionArr else
                                optionArr['analog_value'])
    elif action.type == config.V_STRING:
        config_helper.set_value(section_name, prefixStr + "VAR", optionArr['string_variable_sellocstr'])
        config_helper.set_value(section_name, prefixStr + "VAL",
                                optionArr['string_value_sellocstr'] if 'string_value_sellocstr' in optionArr else
                                optionArr['string_value'])
    elif action.type == config.V_TIME:
        config_helper.set_value(section_name, prefixStr + "VAR", optionArr['time_variable_sellocstr'])
        config_helper.set_value(section_name, prefixStr + "VAL",
                                optionArr['time_value_sellocstr'] if 'time_value_sellocstr' in optionArr else
                                optionArr['time_value'])
    elif action.type == config.V_DATE:
        config_helper.set_value(section_name, prefixStr + "VAR", optionArr['date_variable_sellocstr'])
        config_helper.set_value(section_name, prefixStr + "VAL",
                                optionArr['date_value_sellocstr'] if 'date_value_sellocstr' in optionArr else
                                optionArr['date_value'])
    elif action.type == config.V_DELAY:
        config_helper.set_value(section_name, prefixStr + "DELAY_TIME", optionArr['delay_value_sellocstr'])
    elif action.type == config.V_UCALC:
        config_helper.set_value(section_name, prefixStr + "IN_EXPR", optionArr['formula_value'])
        config_helper.set_value(section_name, prefixStr + "OUT_VARS", optionArr['formula_variable_sellocstr'])
    elif action.type == config.V_FUNC:
        funcModel = models.ExecFunc
        selFunc = funcModel.query.filter_by(id=optionArr['func_select_selid']).with_entities(funcModel.group, funcModel.name).first()
        config_helper.set_value(section_name, prefixStr + "FUNC_GROUP", selFunc.group)
        config_helper.set_value(section_name, prefixStr + "FUNC", selFunc.name)
        inArr = []
        outArr = []
        for key, val in optionArr.items():
            if 'func_in_val' in key or 'func_out_val' in key:
                keyArr = key.split('_')
                if len(keyArr) == 4:
                    selVal = optionArr[key + "_sellocstr"] if key + "_sellocstr" in optionArr else optionArr[key]
                    if 'func_in_val' in key:
                        inArr.append(selVal)
                    else:
                        outArr.append(selVal)

        config_helper.set_value(section_name, prefixStr + "IN_EXPR", ','.join(inArr))
        config_helper.set_value(section_name, prefixStr + "OUT_VARS", ','.join(outArr))
    elif action.type == config.V_SHELLEXEC:
        config_helper.set_value(section_name, prefixStr + "SHELL_APP", optionArr['shell_application'])
        config_helper.set_value(section_name, prefixStr + "SHELL_CMD", optionArr['shell_param'])
        config_helper.set_value(section_name, prefixStr + "HIDE_START", optionArr['shell_exec'])
        config_helper.set_value(section_name, prefixStr + "EXEC_OPTION", optionArr['shell_duplicate'])
    elif action.type == config.V_CUSTOM:
        config_helper.set_value(section_name, prefixStr + "COMM_INDEX",
                                get_group_index(models.CustomChannel, optionArr['channel_id']))
        config_helper.set_value(section_name, prefixStr + "FRAME_INDEX",
                                get_group_index(models.CustomFrame, optionArr['frame_id']))
        config_helper.set_value(section_name, prefixStr + "FRAME_MODE", optionArr['comm_frame_type'])
    elif action.type == config.V_RECIPE:
        selModel = models.RecipeName
        nameInd = str(selModel.query.filter(selModel.id < optionArr['recipe_id']).filter(selModel.def_id == optionArr['def_id']).count())
        config_helper.set_value(section_name, prefixStr + "RECIPE",
                                get_group_index(models.RecipeDef, optionArr['def_id']) + "." + nameInd)
    elif action.type == config.V_GROUPACT:
        config_helper.set_value(section_name, prefixStr + "ACT_GROUP_INDEX",
                                get_group_index(models.ActionGroup, optionArr['actgroup_id']))
    elif action.type == config.V_CONTROL:
        config_helper.set_value(section_name, prefixStr + "CONTROL_INDEX",
                                get_group_index(models.Control, optionArr['control_id']))

    config_helper.set_value(section_name, prefixStr + "SEQ", str(action.order))


def actgroup_write(section_name, actgroup, ind):
    prefixStr = 'ACTION_GROUP.' + str(ind) + "."
    config_helper.set_value(section_name, prefixStr + "MODE", actgroup.mode)
    config_helper.set_value(section_name, prefixStr + "CTRL_INDEX", get_group_index(models.Control, actgroup.controlid))
    config_helper.set_value(section_name, prefixStr + "EXEC_NUM", actgroup.cnt)


def control_write(section_name, control, ind):
    prefixStr = 'CONTROL.' + str(ind) + "."
    config_helper.set_value(section_name, prefixStr + "ENABLE", 'TRUE' if control.use_flag == '1' else 'FALSE')
    config_helper.set_value(section_name, prefixStr + "PANEL_INDEX", get_group_index(models.Logic, control.logicid))
    config_helper.set_value(section_name, prefixStr + "PRIORITY", control.priority)
    config_helper.set_value(section_name, prefixStr + "APPLY_PANEL_MODE", 'TRUE' if control.mode == '1' else 'FALSE')


def logic_write(section_name, logic, ind):
    prefixStr = 'CONTROL_PANEL.' + str(ind) + "."
    config_helper.set_value(section_name, prefixStr + "ENABLE", 'TRUE' if logic.use_flag == '1' else 'FALSE')
    config_helper.set_value(section_name, prefixStr + "MODE", logic.mode)


def modbus_write(section, modbus, ind):
    prefixStr = str(ind) + "."
    config_helper.set_value(section, prefixStr + "ENABLE", 'TRUE' if modbus.use_flag == '1' else 'FALSE')
    config_helper.set_value(section, prefixStr + "TYPE", modbus.protocol + "_" + modbus.type)

    optionArr = json.loads(modbus.options) if len(modbus.options) > 0 else {}
    if modbus.protocol == "TCP":
        if modbus.type == "MASTER":
            config_helper.set_value(section, prefixStr + "SLAVE_IP", optionArr.get('tcp_master_ip', ''))
            config_helper.set_value(section, prefixStr + "SLAVE_PORT", optionArr.get('tcp_master_port', ''))
            config_helper.set_value(section, prefixStr + "TIME_OUT", optionArr.get('tcp_master_timeout', ''))
            config_helper.set_value(section, prefixStr + "UNIT_ID", optionArr.get('tcp_master_unit', ''))
            config_helper.set_value(section, prefixStr + "DELAY", optionArr.get('tcp_master_delay', ''))
        elif modbus.type == "SLAVE":
            config_helper.set_value(section, prefixStr + "SLAVE_PORT", optionArr.get('tcp_slave_port', ''))
    elif modbus.protocol == "RTU":
        if modbus.type == "MASTER":
            config_helper.set_value(section, prefixStr + "TRANSMISSION", optionArr.get('rtu_master_transmission', ''))
            config_helper.set_value(section, prefixStr + "PORT", optionArr.get('rtu_master_port', ''))
            config_helper.set_value(section, prefixStr + "BAUD_RATE", optionArr.get('rtu_master_bps', ''))
            config_helper.set_value(section, prefixStr + "PARITY_BIT", optionArr.get('rtu_master_parity', ''))
            config_helper.set_value(section, prefixStr + "STOP_BIT", optionArr.get('rtu_master_stop', ''))
            config_helper.set_value(section, prefixStr + "DATA_BIT", optionArr.get('rtu_master_data', ''))
        elif modbus.type == "SLAVE":
            config_helper.set_value(section, prefixStr + "UNIT_ID", optionArr.get('rtu_slave_unit', ''))
            config_helper.set_value(section, prefixStr + "PORT", optionArr.get('rtu_slave_port', ''))
            config_helper.set_value(section, prefixStr + "BAUD_RATE", optionArr.get('rtu_slave_bps', ''))
            config_helper.set_value(section, prefixStr + "PARITY_BIT", optionArr.get('rtu_slave_parity', ''))
            config_helper.set_value(section, prefixStr + "STOP_BIT", optionArr.get('rtu_slave_stop', ''))

    if modbus.type == "MASTER":
        prefixStr = prefixStr + "CHANNEL."
        chl_list = models.ModbusChannel.query.filter_by(modbus_id=modbus.id).all()
        for ind1 in range(len(chl_list)):
            prefixStr1 = prefixStr + str(ind1) + "."
            modbus_chl = chl_list[ind1]
            optionArr = json.loads(modbus_chl.options) if len(modbus_chl.options) > 0 else {}

            if modbus.protocol == "RTU":
                config_helper.set_value(section, prefixStr1 + "UNIT_ID", optionArr.get('channel_unit', ''))
                config_helper.set_value(section, prefixStr1 + "TIME_OUT", optionArr.get('channel_timeout', ''))

            config_helper.set_value(section, prefixStr1 + "FC", optionArr.get('channel_code', ''))

            chlCode = int(optionArr.get('channel_code', '0'))
            if 1 <= chlCode <= 4:
                config_helper.set_value(section, prefixStr1 + "READ_OFFSET", optionArr.get('channel_readoffset', ''))
                config_helper.set_value(section, prefixStr1 + "READ_LEN", optionArr.get('channel_readlen', ''))
            elif 5 <= chlCode <= 16:
                config_helper.set_value(section, prefixStr1 + "WRITE_OFFSET", optionArr.get('channel_writeoffset', ''))
                config_helper.set_value(section, prefixStr1 + "WRITE_LEN", optionArr.get('channel_writelen', ''))
            elif chlCode == 23:
                config_helper.set_value(section, prefixStr1 + "READ_OFFSET", optionArr.get('channel_readoffset', ''))
                config_helper.set_value(section, prefixStr1 + "READ_LEN", optionArr.get('channel_readlen', ''))
                config_helper.set_value(section, prefixStr1 + "WRITE_OFFSET", optionArr.get('channel_writeoffset', ''))
                config_helper.set_value(section, prefixStr1 + "WRITE_LEN", optionArr.get('channel_writelen', ''))


def recipe_write(section, recipe, ind):
    prefixStr = str(ind) + ".VAR."
    prefixStr1 = str(ind) + ".RECIPE."
    varModel = models.RecipeVar
    recipeVars = models.RecipeVar.query.filter_by(def_id=recipe.id).with_entities(varModel.sellocstr, varModel.id).all()
    varArr = {}

    for ind in range(len(recipeVars)):
        recipeVar = recipeVars[ind]
        config_helper.set_value(section, prefixStr + str(ind), recipeVar.sellocstr)

        recipe_val = models.RecipeValue.query.filter_by(def_id=recipe.id).filter_by(var_id=recipeVar.id).all()
        for ind1 in range(len(recipe_val)):
            recipeVal = recipe_val[ind1]
            if len(recipeVal.options) > 5:
                selVal = json.loads(recipeVal.options)['sellocstr']
            else:
                selVal = recipeVal.value
            varArr[prefixStr1 + str(ind) + "." + str(ind1)] = selVal

    for key, val in varArr.items():
        config_helper.set_value(section, key, val)


def local_write(section):
    prefixStr = "LOCAL."
    selServer = models.LocalServer.query.first()
    config_helper.set_value(section, prefixStr + 'ENABLE', 'TRUE' if selServer.use_flag == "1" else "FALSE")
    config_helper.set_value(section, prefixStr + 'IP_ADDR', selServer.ip_addr)
    config_helper.set_value(section, prefixStr + 'PORT', selServer.port_addr)


def remote_write(section, remote, ind):
    prefixStr = "REMOTE." + str(ind) + "."
    config_helper.set_value(section, prefixStr + 'ENABLE', 'TRUE' if remote.use_flag == "1" else "FALSE")
    config_helper.set_value(section, prefixStr + 'NAME', remote.name)
    config_helper.set_value(section, prefixStr + 'IP_ADDR', remote.ip)
    config_helper.set_value(section, prefixStr + 'PORT', remote.port)


def variable_write(section, variable, ind):
    prefixStr = "REMOTE_ITEM." + str(ind)
    typeArr = variable.type.split('-')
    varStr = config.VARIABLE_MATCH[typeArr[0]] + '.' + typeArr[1]
    locStr = "REMOTE." + str(variable.remote - 1) if variable.remote > 0 else "LOCAL.0"
    config_helper.set_value(section, prefixStr, locStr + "." + varStr)


def alarm_write(section, alarm, ind):
    prefixStr = str(ind) + "."
    optionArr = json.loads(alarm.options) if len(alarm.options) > 0 else {}
    config_helper.set_value(section, prefixStr + "TYPE", alarm.type)
    if alarm.type == config.V_DIGITAL:
        config_helper.set_value(section, prefixStr + "OPR", optionArr.get('digital_cond', ''))
        config_helper.set_value(section, prefixStr + "VAR", optionArr.get('digital_variable_sellocstr', ''))
        config_helper.set_value(section, prefixStr + "VAL", optionArr.get('digital_value', ''))
        config_helper.set_value(section, prefixStr + "MIN_PEND_TIME",
                                optionArr['digital_time_sellocstr'] if 'digital_time_sellocstr' in optionArr else
                                optionArr.get('digital_time', ''))
    elif alarm.type == config.V_CHANGE:
        config_helper.set_value(section, prefixStr + "VAR",
                                optionArr['detect_variable_sellocstr'] if 'detect_variable_sellocstr' in optionArr else
                                optionArr.get('detect_variable', ''))
    elif alarm.type == "IN_RANGE":
        config_helper.set_value(section, prefixStr + "OPR_LOWER", optionArr.get('range_lbound', ''))
        config_helper.set_value(section, prefixStr + "OPR_UPPER", optionArr.get('range_ubound', ''))
        config_helper.set_value(section, prefixStr + "VAR", optionArr.get('range_variable_sellocstr', ''))
        config_helper.set_value(section, prefixStr + "VAL_LOWER",
                                optionArr['range_lbound_value_sellocstr'] if 'range_lbound_value_sellocstr' in optionArr
                                else optionArr.get('range_lbound_value', ''))
        config_helper.set_value(section, prefixStr + "VAL_UPPER",
                                optionArr['range_ubound_value_sellocstr'] if 'range_ubound_value_sellocstr' in optionArr
                                else optionArr.get('range_ubound_value', ''))
        config_helper.set_value(section, prefixStr + "HYST",
                                optionArr['range_hysteris_sellocstr'] if 'range_hysteris_sellocstr' in optionArr else
                                optionArr.get('range_hysteris', ''))
        config_helper.set_value(section, prefixStr + "MIN_PEND_TIME",
                                optionArr['range_time_sellocstr'] if 'range_time_sellocstr' in optionArr else
                                optionArr.get('range_time', ''))
    elif alarm.type == "UPPER_LIMIT":
        config_helper.set_value(section, prefixStr + "OPR", optionArr.get('ubound_cond', ''))
        config_helper.set_value(section, prefixStr + "VAR", optionArr.get('ubound_variable_sellocstr', ''))
        config_helper.set_value(section, prefixStr + "VAL",
                                optionArr['ubound_value_sellocstr'] if 'ubound_value_sellocstr' in optionArr else
                                optionArr.get('ubound_value', ''))
        config_helper.set_value(section, prefixStr + "HYST",
                                optionArr['ubound_hysteris_sellocstr'] if 'ubound_hysteris_sellocstr' in optionArr else
                                optionArr.get('ubound_hysteris', ''))
        config_helper.set_value(section, prefixStr + "MIN_PEND_TIME",
                                optionArr['ubound_time_sellocstr'] if 'ubound_time_sellocstr' in optionArr else
                                optionArr.get('ubound_time', ''))
    elif alarm.type == "LOWER_LIMIT":
        config_helper.set_value(section, prefixStr + "OPR", optionArr.get('lbound_cond', ''))
        config_helper.set_value(section, prefixStr + "VAR", optionArr.get('lbound_variable_sellocstr', ''))
        config_helper.set_value(section, prefixStr + "VAL",
                                optionArr['lbound_value_sellocstr'] if 'lbound_value_sellocstr' in optionArr else
                                optionArr.get('lbound_value', ''))
        config_helper.set_value(section, prefixStr + "HYST",
                                optionArr['lbound_hysteris_sellocstr'] if 'lbound_hysteris_sellocstr' in optionArr else
                                optionArr.get('lbound_hysteris', ''))
        config_helper.set_value(section, prefixStr + "MIN_PEND_TIME",
                                optionArr['lbound_time_sellocstr'] if 'lbound_time_sellocstr' in optionArr else
                                optionArr.get('lbound_time', ''))


def interval_write(section):
    selModel = models.SettingInterval
    for intItem in config.INTERVAL_LIST:
        selInt = selModel.query.filter_by(set_name=intItem).with_entities(selModel.interval).first()
        itemVal = selInt.interval if selInt else ""
        config_helper.set_value(section, intItem.upper(), itemVal)


@userbp.route('/change_mode', methods=['POST'])
@login_required
def change_mode():
    postData = request.values
    selMode = postData.get('selMode')
    if check_null(selMode):
        if selMode == "stop":
            # var part
            section_name = 'VAR'
            config_helper.initSection(section_name)
            selModel = models.Variable
            default_var = selModel.query.filter(func.length(selModel.defaults) > 0).all()
            threads = [gevent.spawn(write_default(section_name, default_item)) for default_item in default_var]
            gevent.joinall(threads)

            # condition part
            section_name = 'LOGIC'
            config_helper.initSection(section_name)
            conditions = models.Condition.query.all()
            threads = [gevent.spawn(write_condition(section_name, conditions[ind], ind)) for ind in
                       range(len(conditions))]
            gevent.joinall(threads)

            cond_groups = models.ConditionGroup.query.all()
            threads = [gevent.spawn(write_condgroup(section_name, cond_groups[ind], ind)) for ind in
                       range(len(cond_groups))]
            gevent.joinall(threads)

            actions = models.Action.query.all()
            threads = [gevent.spawn(write_action(section_name, actions[ind], ind)) for ind in range(len(actions))]
            gevent.joinall(threads)

            act_groups = models.ActionGroup.query.all()
            threads = [gevent.spawn(actgroup_write(section_name, act_groups[ind], ind)) for ind in
                       range(len(act_groups))]
            gevent.joinall(threads)

            controls = models.Control.query.all()
            threads = [gevent.spawn(control_write(section_name, controls[ind], ind)) for ind in range(len(controls))]
            gevent.joinall(threads)

            logic = models.Logic.query.all()
            threads = [gevent.spawn(logic_write(section_name, logic[ind], ind)) for ind in range(len(logic))]
            gevent.joinall(threads)

            section_name = "RECIPE_DEF"
            config_helper.initSection(section_name)
            recipe = models.RecipeDef.query.with_entities(models.RecipeDef.id).all()
            threads = [gevent.spawn(recipe_write(section_name, recipe[ind], ind)) for ind in range(len(recipe))]
            gevent.joinall(threads)

            section_name = "ETHERCAT_IO"
            config_helper.initSection(section_name)
            ethercat_use, ethercat_try = get_ethercat()
            config_helper.set_value(section_name, "ENABLE", 'TRUE' if ethercat_use else 'FALSE')
            config_helper.set_value(section_name, "AUTO_RECONFIG", 'TRUE' if ethercat_try else 'FALSE')

            section_name = "MODBUS"
            config_helper.initSection(section_name)
            modbus1 = models.Modbus.query.all()
            threads = [gevent.spawn(modbus_write(section_name, modbus1[ind], ind)) for ind in range(len(modbus1))]
            gevent.joinall(threads)

            section_name = "REMOTE_DEVICE"
            config_helper.initSection(section_name)
            local_write(section_name)

            remotes = models.RemoteClient.query.all()
            threads = [gevent.spawn(remote_write(section_name, remotes[ind], ind)) for ind in range(len(remotes))]
            gevent.joinall(threads)

            variables = models.Variable.query.filter(models.Variable.use_flag=='1', models.Variable.remote > 0).order_by(models.Variable.remote.asc()).all()
            threads = [gevent.spawn(variable_write(section_name, variables[ind], ind)) for ind in range(len(variables))]
            gevent.joinall(threads)

            section_name = "ALARM"
            config_helper.initSection(section_name)
            alarm_list = models.Alarm.query.all()
            threads = [gevent.spawn(alarm_write(section_name, alarm_list[ind], ind)) for ind in range(len(alarm_list))]
            gevent.joinall(threads)

            section_name = "TASK_INTERVAL"
            config_helper.initSection(section_name)
            interval_write(section_name)

        section_name = "GENERAL"
        config_helper.initSection(section_name)
        config_helper.set_value(section_name, "GMT_TIME_ZONE", '9:00')
        config_helper.set_value(section_name, "RUN_MODE", 'TRUE' if selMode == "stop" else 'FALSE')

        #u2p_shm = U2p_Logic()
        #u2p_shm.change_run_mode(1 if selMode == "stop" else 0)

        selSet = models.Settings.query.filter_by(name='mode').first()
        selSet.value = 'run' if selMode == "stop" else 'stop'
        db.session.commit()

        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


def user_item(user, ind):
    return {'id': user.id, 'ind': ind, 'type_str': config.USER_TYPE[user.usertype], 'userid': user.userid,
            'type': user.usertype}


@userbp.route('/user_list', methods=['POST'])
def user_list():
    draw, start, length, columnIndex, columnName, sortOrder = datatable_head(request.values)

    chlModel = models.User
    data_list = chlModel.query
    totalCount = data_list.count()

    # columnIndex = "1"
    # if columnIndex == '2':
    #     orderObj = chlModel.userid.asc() if sortOrder == 'asc' else chlModel.userid.desc()
    # elif columnIndex == '3':
    #     orderObj = chlModel.usertype.asc() if sortOrder == 'asc' else chlModel.usertype.desc()
    # else:
    #     orderObj = chlModel.id.asc() if sortOrder == 'asc' else chlModel.id.desc()

    orderObj = chlModel.id.asc()
    data_list = data_list.order_by(orderObj).offset(start).limit(length).all()
    selList = [user_item(data_list[ind], start + ind + 1) for ind in range(len(data_list))]

    return json.dumps(datatable_list(selList, totalCount, draw))


@userbp.route('/save_authority', methods=['POST'])
def save_authority():
    postData = request.form.to_dict()
    userID = postData.get('userid')
    if check_null(userID):
        postData.pop('userid')
        selModel = models.Authority
        for key, val in postData.items():
            if '-read' in key:
                menu = key.replace('-read', '')
                read = True
            else:
                menu = key.replace('-write', '')
                read = False

            selAuth = selModel.query.filter_by(userid=userID).filter_by(menu=menu).first()
            if selAuth:
                if read:
                    selAuth.read = val
                else:
                    selAuth.edit = val
            else:
                newAuth = selModel(
                    userid=userID,
                    menu=menu,
                    read=val if read else '0',
                    edit=val if not read else '0'
                )
                db.session.add(newAuth)

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@userbp.route('/get_auth', methods=['POST'])
def get_auth():
    postData = request.values
    selUser = postData.get('selUser')
    if check_null(selUser):
        auths = models.Authority.query.filter_by(userid=selUser).all()
        data_list = [{'menu': auth.menu, 'read': auth.read, 'edit': auth.edit} for auth in auths]
        selAuth = models.User.query.filter_by(id=selUser).first()
        response = {'status': True, 'data': data_list, 'type': selAuth.usertype}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@userbp.route('/setting')
def setting():
    userid=session['user_id']
    if userid:
        name = ''
        zone = '22'
        logo = ''
        control_name = models.Settings.query.filter_by(name='control_name').filter_by(userid=userid).first()
        if control_name is not None:
            name=control_name.value
        control_zone = models.Settings.query.filter_by(name='control_zone').filter_by(userid=userid).first()
        if control_zone is not None:
            zone=control_zone.value
        control_logo = models.Settings.query.filter_by(name='control_logo').filter_by(userid=userid).first()
        if control_logo is not None:
            logo=control_logo.value
        timezones = models.Timezone.query.all()
        return render_template('user/setting.html', zone=zone, setting=name, logo=logo, timezones=timezones)
    else :
        return redirect(url_for('userbp.login'))


@userbp.route('/update_setting', methods=['POST'])
def update_setting():
    postData = request.values
    controlName = postData.get('control')
    zone = postData.get('timezone')
    if check_null(controlName):
        userid = session['user_id']
        selName = models.Settings.query.filter_by(name='control_name').filter_by(userid=userid).first()
        if selName:
            selName.value = controlName
        else:
            newName = models.Settings(
                name='control_name',
                value=controlName,
                userid=userid
            )
            db.session.add(newName)

        selZone = models.Settings.query.filter_by(name='control_zone').filter_by(userid=userid).first()

        if selZone:
            selZone.value = zone
        else:
            newZone = models.Settings(
                name='control_zone',
                value=zone,
                userid=userid
            )
            db.session.add(newZone)
        

        if postData.get('bool_file') == "1":
            selLogo = models.Settings.query.filter_by(name='control_logo').filter_by(userid=userid).first()
            if postData.get('new_file') == '1':
                selFile = request.files['file']
                chkPath = config.UPLOAD_FOLDER + "logo/"
                if not os.path.exists(chkPath):
                    os.makedirs(chkPath)

                uploadPath = "logo/" + selFile.filename
                selFile.save(os.path.join(config.UPLOAD_FOLDER, uploadPath))

                if selLogo:
                    selLogo.value = uploadPath
                else:
                    newLogo = models.Settings(
                        name='control_logo',
                        value=uploadPath,
                        userid=userid
                    )
                    db.session.add(newLogo)
            else:
                selLogo.value = ""

        db.session.commit()
        userModel = models.User
        userSet = userModel.query.filter_by(id=userid).first()
        if(userSet) :
            userSet.setting = 1
            session['setting'] = 1
            db.session.commit()
        
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@userbp.route('/save_interval', methods=['POST'])
def save_interval():
    postData = request.values
    selModel = models.SettingInterval
    for key, val in postData.items():
        selInt = selModel.query.filter_by(set_name=key).first()
        if selInt:
            selInt.interval = val
        else:
            newInt = selModel(
                set_id='0',
                set_name=key,
                interval=val
            )

            db.session.add(newInt)

    db.session.commit()
    return json.dumps({'status': True})


@userbp.route('/user_help')
def user_help():
    return render_template('user/help.html')

@userbp.route('/updateaccept', methods=['POST'])
def updateaccept():
    postData = request.values
    userid = postData.get('id')
    userModel = models.User
    userSet = userModel.query.filter_by(id=userid).first()
    if(userSet) :
        userSet.accept = 1
        session['accept'] = 1
        db.session.commit()

    return json.dumps({'status': True})