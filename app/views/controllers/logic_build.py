from flask import render_template, Blueprint, request, redirect
from app.views.controllers.user import login_required
from app import models, db, config
from sqlalchemy import cast, Integer
from app.helper import const, LogicMemory
from app.helper.common import check_null, get_desc_str, get_desc_str1, get_remotes
import json
import string
import random

logic_build = Blueprint('logic_build', __name__, url_prefix='/logic_build')


def condition_page_modal_list(selid):
    condModel = models.Condition
    conditions = condModel.query.filter_by(condgroup=selid).order_by(cast(condModel.ind, Integer)).all()
    return [get_condition_item(condition) for condition in conditions]


def act_page_modal_list(selid):
    actionModel = models.Action
    actions = actionModel.query.filter_by(actgroup=selid).order_by(cast(actionModel.ind, Integer)).all()
    return [get_condition_item(action, False) for action in actions]


@logic_build.route('/control', methods=['POST'])
@login_required
def control():
    postData = request.values
    selid = postData.get('controlID')
    if check_null(selid) and int(selid) > 0:
        selControl = models.Control.query.filter_by(id=selid).first()
        selActGroup = models.ActionGroup.query.filter_by(controlid=selid).first()
        selCondGroup = models.ConditionGroup.query.filter_by(controlid=selid).first()

        cond_page_list = []
        if selCondGroup:
            cond_page_list = condition_page_modal_list(selCondGroup.id)
            selCondGroup = {'id': selCondGroup.id, 'name': selCondGroup.name, 'options': selCondGroup.options}
        else:
            selCondGroup = {'id': 0, 'name': '조건그룹', 'options': ''}

        act_page_list = []
        if selActGroup:
            act_page_list = act_page_modal_list(selActGroup.id)
            selActGroup = {'id': selActGroup.id, 'name': selActGroup.name, 'options': selActGroup.options,
                           'mode': config.ACTION_GROUP_MODE[selActGroup.mode]}
        else:
            selActGroup = {'id': 0, 'name': '동작그룹', 'mode': '', 'options': ''}

        response = {'status': True, 'selControl': {'name': selControl.name, 'options': selControl.options,
                    'useflag': config.USE_FLAG_KR[int(selControl.use_flag)], 'priority': selControl.priority, 'id': selControl.id},
                    'actgroup': selActGroup, 'condgroup': selCondGroup, 'cond_page_list': cond_page_list,
                    'act_page_list': act_page_list}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_build.route('/edit_control', methods=['POST'])
@login_required
def edit_control():
    postData = request.values
    controlName = postData.get('inputName')
    selid = postData.get('controlID')
    if check_null(controlName) and check_null(selid):
        if int(selid) > 0:
            selControl = models.Control.query.filter_by(id=selid).first()
            selControl.name = controlName
            selControl.mode = postData.get('mode')
            selControl.use_flag = postData.get('use_flag')
            selControl.priority = postData.get('inputCnt')
        else:
            newControl = models.Control(
                options="",
                ind="1000",
                logicid="0",
                name=controlName,
                mode=postData.get('mode'),
                use_flag=postData.get('use_flag'),
                priority=postData.get('inputCnt')
            )

            db.session.add(newControl)

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_build.route('/remove_control', methods=['POST'])
@login_required
def remove_control():
    postData = request.values
    selIDS = postData.get('selRow')
    if check_null(selIDS):
        selIDS = selIDS.split(",")
        for selid in selIDS:
            models.Control.query.filter_by(id=selid).delete()

            selActGroup = models.ActionGroup.query.filter_by(controlid=selid).first()
            if selActGroup:
                selActGroup.controlid = '0'
                selActGroup.options = ''

            selCondGroup = models.ConditionGroup.query.filter_by(controlid=selid).first()
            if selCondGroup:
                selCondGroup.controlid = '0'
                selCondGroup.options = ''

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


@logic_build.route('/logic', defaults={'selid': '000'})
@logic_build.route('/logic/<selid>')
@login_required
def logic(selid='000'):
    if selid != '':
        selLogic = models.Logic.query.filter_by(logicid=selid).first()
        if selLogic:
            controlModel = models.Control
            controls = controlModel.query.filter_by(logicid=selid).order_by(cast(controlModel.ind, Integer)).all()

            data_list = []
            for selControl in controls:
                selCondGroup = models.ConditionGroup.query.filter_by(controlid=selControl.id).first()
                selActGroup = models.ActionGroup.query.filter_by(controlid=selControl.id).first()

                if selCondGroup:
                    cond_page_list = condition_page_modal_list(selCondGroup.id)
                    selCondGroup = {'id': selCondGroup.id, 'name': selCondGroup.name, 'options': selCondGroup.options}
                else:
                    cond_page_list = []
                    selCondGroup = {'id': 0, 'name': '조건그룹', 'options': ''}

                if selActGroup:
                    act_page_list = act_page_modal_list(selActGroup.id)
                    selActGroup = {'id': selActGroup.id, 'name': selActGroup.name, 'options': selActGroup.options,
                                   'mode': config.ACTION_GROUP_MODE[selActGroup.mode]}
                else:
                    act_page_list = []
                    selActGroup = {'id': 0, 'name': '동작그룹', 'mode': '', 'options': ''}

                data_list.append({
                    'control': {'name': selControl.name, 'use_flag': config.USE_FLAG_KR[int(selControl.use_flag)],
                                'options': selControl.options, 'priority': selControl.priority, 'id': selControl.id},
                    'condgroup': selCondGroup, 'cond_page_list': cond_page_list,
                    'actgroup': selActGroup, 'act_page_list': act_page_list
                })
            alarms = models.Alarm.query.all()

            logic_mem = LogicMemory.SharedMem_Logic()
            start_val = controlModel.query.filter(controlModel.id < selid).count()
            # validList = logic_mem.get_buff(LogicMemory.Const_Logic, start_val, start_val + 1) validList[0]['val']
            return render_template('logic_build/logic.html', logic=selLogic, controls=data_list,
                                   control_limit=const.uiSizeCtrl, condgroup_limit=const.uiSizeEvalGrp,
                                   actgroup_limit=const.uiSizeActGrp, action_limit=const.uiSizeAct,
                                   condition_limit=const.uiSizeEval, time_limit=const.uiSizeTimePeriod,
                                   alarms=alarms, remotes=get_remotes(), priority="5", selid=selid)
        else:
            return redirect('/')
    else:
        return redirect('/')


@logic_build.route('/edit_logic', methods=['POST'])
@login_required
def edit_logic():
    postData = request.form.to_dict()
    logicName = postData.get('name')
    selid = postData.get('selid')

    print("logicName, selid")
    print(selid)

    if check_null(logicName) and check_null(selid):
        if len(selid) > 1:
            newLogic = models.Logic.query.filter_by(logicid=selid).first()
            newLogic.name = logicName
            newLogic.mode = postData.get('mode')
            newLogic.use_flag = postData.get('use_flag')
        else:
            letters = string.digits
            while True:
                logicid = ''.join(random.choice(letters) for i in range(3))
                checkLogic = models.Logic.query.filter_by(logicid=logicid).first()
                if checkLogic is None:
                    newLogic = models.Logic(
                        options='',
                        name=logicName,
                        mode=postData.get('mode'),
                        use_flag=postData.get('use_flag'),
                        logicid=logicid
                    )
                    db.session.add(newLogic)
                    break
        db.session.commit()
        db.session.refresh(newLogic)
        response = {'status': True, 'selid': newLogic.logicid}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_build.route('/del_control', methods=['POST'])
@login_required
def del_control():
    postData = request.values
    control_id = postData.get('actID')
    if check_null(control_id):
        selControl = models.Control.query.filter_by(id=control_id).first()
        if selControl:
            selControl.logicid = '0'
            selControl.options = ''
            selControl.ind = '1000'
            db.session.commit()
            response = {'status': True}
        else:
            response = {'status': False, 'message': 'Control Not Found'}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


@logic_build.route('/remove_logic', methods=['POST'])
@login_required
def remove_logic():
    postData = request.values
    selIDS = postData.get('selRow')
    if check_null(selIDS):
        selIDS = selIDS.split(",")
        for selid in selIDS:
            models.Logic.query.filter_by(logicid=selid).delete()

            controls = models.Control.query.filter_by(logicid=selid).all()
            for control in controls:
                control.logicid = '0'
                control.options = ''
                control.ind = '1000'

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


def get_condition_item(condition, flag=True):
    returnObj = {
        'id': condition.id,
        'name': condition.name,
        'type': condition.type,
        'use_flag': config.USE_FLAG_KR[int(condition.use_flag)],
        'options': condition.condoptions if flag else condition.actoptions
    }

    settings = json.loads(condition.options)
    for key, val in settings.items():
        returnObj[key] = val

    if not flag:
        returnObj['order'] = condition.order

    returnObj["desc"] = get_desc_str(returnObj) if flag else get_desc_str1(returnObj)
    for key, val in settings.items():
        returnObj.pop(key)

    returnObj['type'] = config.VARIABLE_TYPE[condition.type]
    return returnObj


@logic_build.route('/cond_group', methods=['POST'])
@login_required
def cond_group():
    postData = request.values
    selid = postData.get('condGroupID')
    if check_null(selid) and int(selid) > 0:
        selControl = models.ConditionGroup.query.filter_by(id=selid).first()
        if selControl:
            page_list = condition_page_modal_list(selid)
            response = {'status': True, 'condgroup': {'id': selid, 'name': selControl.name,
                                                      'options': selControl.options}, 'page_list': page_list}
        else:
            response = {'status': False, 'message': 'Not Found'}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_build.route('/edit_cond_group', methods=['POST'])
@login_required
def edit_cond_group():
    postData = request.values
    condGroupName = postData.get('cond_group_name')
    selid = postData.get('cond_group_id')
    if check_null(condGroupName) and check_null('selid'):
        if int(selid) > 0:
            selCondGroup = models.ConditionGroup.query.filter_by(id=selid).first()
            selCondGroup.name = condGroupName
            selCondGroup.operator = postData.get('cond_group_operator')
            selCondGroup.reverse = postData.get('cond_group_reverse')
        else:
            newCondGroup = models.ConditionGroup(
                name=condGroupName,
                controlid=postData.get('control_id'),
                options="",
                operator=postData.get('cond_group_operator'),
                reverse=postData.get('cond_group_reverse')
            )

            db.session.add(newCondGroup)
        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_build.route('/remove_cond_group', methods=['POST'])
@login_required
def remove_cond_group():
    postData = request.values
    selIDS = postData.get('selRow')
    if check_null(selIDS):
        selIDS = selIDS.split(",")
        for selid in selIDS:
            models.ConditionGroup.query.filter_by(id=selid).delete()

            selConditions = models.Condition.query.filter_by(condgroup=selid).all()
            for cond in selConditions:
                cond.condgroup = '0'
                cond.condoptions = ''
                cond.ind = '1000'

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


@logic_build.route('/action_group', methods=['POST'])
@login_required
def action_group():
    postData = request.values
    selid = postData.get('actGroupID')
    if check_null(selid) and int(selid) > 0:
        selActGroup = models.ActionGroup.query.filter_by(id=selid).first()
        if selActGroup:
            page_list = act_page_modal_list(selid)
            response = {'status': True, 'actgroup': {'id': selActGroup.id, 'name': selActGroup.name,
                                                     'options': selActGroup.options,
                                                     'mode': config.ACTION_GROUP_MODE[selActGroup.mode]},
                        'page_list': page_list}
        else:
            response = {'status': False, 'message': "Not Found"}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


@logic_build.route('/edit_action_group', methods=['POST'])
@login_required
def edit_action_group():
    postData = request.form.to_dict()
    actionGroupName = postData.get('inputName')
    selid = postData.get('act_group_id')
    if check_null(actionGroupName) and check_null(selid):
        if int(selid) > 0:
            selActGroup = models.ActionGroup.query.filter_by(id=selid).first()
            selActGroup.name = actionGroupName
            selActGroup.mode = postData.get('inputMode')
            selActGroup.cnt = postData.get('inputCnt')
        else:
            newActionGroup = models.ActionGroup(
                name=actionGroupName,
                controlid=postData.get('control_id'),
                options="",
                mode=postData.get('inputMode'),
                cnt=postData.get('inputCnt')
            )

            db.session.add(newActionGroup)
        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_build.route('/remove_action_group', methods=['POST'])
@login_required
def remove_action_group():
    postData = request.values
    selIDS = postData.get('selRow')
    if check_null(selIDS):
        selIDS = selIDS.split(",")
        for selid in selIDS:
            models.ActionGroup.query.filter_by(id=selid).delete()

            selActions = models.Action.query.filter_by(actgroup=selid).all()
            for act in selActions:
                act.actgroup = '0'
                act.actoptions = ''
                act.ind = '1000'

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


@logic_build.route('/add_cond', methods=['POST'])
@login_required
def add_cond():
    postData = request.form.to_dict()
    cond_group_id = postData.get('condGroupID')
    condition_ids = postData.get('condID')
    beforeID = postData.get('beforeID')
    if check_null(cond_group_id) and check_null(condition_ids) and check_null(beforeID):
        # if int(beforeID) > 0:
        #     befCondition = models.Condition.query.filter_by(id=beforeID).first()
        #     befCondition.condgroup = '0'
        #     befCondition.condoptions = ''
        #     befCondition.ind = '1000'

        for condition_id in condition_ids.split(','):
            selCondition = models.Condition.query.filter_by(id=condition_id).first()
            if selCondition:
                selCondition.condgroup = cond_group_id

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_build.route('/remove_cond', methods=['POST'])
@login_required
def remove_cond():
    postData = request.values
    condition_id = postData.get('actID')
    if check_null(condition_id):
        selCondition = models.Condition.query.filter_by(id=condition_id).first()
        if selCondition:
            selCondition.condgroup = 0
            selCondition.condoptions = ""
            selCondition.ind = '1000'
            db.session.commit()
            response = {'status': True}
        else:
            response = {'status': False, 'message': 'Condition Not Found'}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_build.route('/add_act', methods=['POST'])
@login_required
def add_act():
    postData = request.form.to_dict()
    act_group_id = postData.get('actGroupID')
    action_ids = postData.get('actID')
    beforeID = postData.get('beforeID')
    if check_null(act_group_id) and check_null(action_ids) and check_null(beforeID):
        # if int(beforeID) > 0:
        #     beforeAct = models.Action.query.filter_by(id=beforeID).first()
        #     beforeAct.actgroup = '0'
        #     beforeAct.actoptions = ''
        #     beforeAct.ind = '1000'

        for action_id in action_ids.split(','):
            selCondition = models.Action.query.filter_by(id=action_id).first()
            if selCondition:
                selCondition.actgroup = act_group_id

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_build.route('/remove_action', methods=['POST'])
@login_required
def remove_action():
    postData = request.values
    action_id = postData.get('actID')
    if check_null(action_id):
        selAction = models.Action.query.filter_by(id=action_id).first()
        if selAction:
            selAction.actgroup = 0
            selAction.actoptions = ""
            selAction.ind = '1000'
            db.session.commit()
            response = {'status': True}
        else:
            response = {'status': False, 'message': 'Action Not Found'}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_build.route('/add_actgroup', methods=['POST'])
@login_required
def add_actgroup():
    postData = request.values
    controlID = postData.get('controlID')
    actgroupID = postData.get('actgroupID')
    beforeID = postData.get('beforeID')
    #if check_null(controlID) and check_null(actgroupID):
    #    actgroupModel = models.ActionGroup
    #    if  check_null(beforeID) and int(beforeID) > 0:
    #        beforeActGroup = actgroupModel.query.filter_by(id=beforeID).first()
    #        if beforeActGroup:
    #            beforeActGroup.controlid = '0'
    #            beforeActGroup.options = ''

    #    for selid in actgroupID.split(','):
    #        selActGroup = actgroupModel.query.filter_by(id=selid).first()
    #        if selActGroup:
    #            selActGroup.controlid = controlID

    #    db.session.commit()
    #    response = {'status': True}
    #else:
    #    response = {'status': False, 'message': 'Invalid request'}
    if check_null(controlID) and check_null(actgroupID):
        actgroupModel = models.ActionGroup
        for selid in actgroupID.split(','):
            selActGroup = actgroupModel.query.filter_by(id=selid).first()
            if selActGroup:
                selActGroup.controlid = controlID

        db.session.commit()    
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}
    return json.dumps(response)


@logic_build.route('/add_condgroup', methods=['POST'])
@login_required
def add_condgroup():
    postData = request.values
    controlID = postData.get('controlID')
    condgroupID = postData.get('condgroupID')
    beforeID = postData.get('beforeID')
    #if check_null(controlID) and check_null(condgroupID):
    #    condgroupModel = models.ConditionGroup
    #    if check_null(beforeID) and int(beforeID) > 0:
    #        beforeCondGroup = condgroupModel.query.filter_by(id=beforeID).first()
    #        beforeCondGroup.controlid = '0'
    #        beforeCondGroup.options = ''

    #    for selid in condgroupID.split(','):
    #        selCondGroup = condgroupModel.query.filter_by(id=selid).first()
    #        if selCondGroup:
    #            selCondGroup.controlid = controlID

    #    db.session.commit()
    #    response = {'status': True}
    #else:
    #    response = {'status': False, 'message': 'Invalid request'}
    if check_null(controlID) and check_null(condgroupID):
        condgroupModel = models.ConditionGroup
        for selid in condgroupID.split(','):
            selCondGroup = condgroupModel.query.filter_by(id=selid).first()
            if selCondGroup:
                selCondGroup.controlid = controlID

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}
    return json.dumps(response)


@logic_build.route('/add_control', methods=['POST'])
@login_required
def add_control():
    postData = request.values
    logicID = postData.get('logicID')

    print("logicID==================")
    print(logicID)

    controlID = postData.get('controlID')
    beforeID = postData.get('beforeID')
    if check_null(logicID) and check_null(controlID) and check_null(beforeID) > 0:
        controlModel = models.Control
        if int(beforeID) > 0:
            beforeControl = controlModel.query.filter_by(id=beforeID).first()
            beforeControl.logicid = '0'
            beforeControl.options = ''
            beforeControl.ind = '1000'

        for selid in controlID.split(','):
            selCondGroup = controlModel.query.filter_by(id=selid).first()
            if selCondGroup:
                selCondGroup.logicid = logicID

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_build.route('/save_order', methods=['POST'])
@login_required
def save_order():
    postData = request.form.to_dict()
    selType = postData.get('selType')
    if check_null(selType):
        postData.pop('selType')
        selModel = None
        if selType == "action":
            selModel = models.Action
        elif selType == "condition":
            selModel = models.Condition
        elif selType == "control":
            selModel = models.Control
        elif selType == "monitor":
            selModel = models.MonitorElement

        if selModel:
            for key, val in postData.items():
                selVal = selModel.query.filter_by(id=key).first()
                selVal.ind = val

            db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)
