import json, os
from flask import render_template, Blueprint, request
from app.views.controllers.user import login_required, mode_check, auth_check
from app import config, models, db
from app.helper import const, LocalVar, LogicMemory
from sqlalchemy import or_
from app.helper.common import check_null, get_desc_str, datatable_list, get_desc_str1, get_remotes, \
    datatable_head

# Create a dashboard blueprint
logic_setting = Blueprint('logic_setting', __name__, url_prefix='/logic_setting')


@logic_setting.route('/variable')
@login_required
@auth_check
def variable():
    return render_template('logic_setting/variable.html', remotes=get_remotes())


@logic_setting.route('/condition')
@login_required
def condition():
    return render_template('logic_setting/condition.html', remotes=get_remotes(),
                           condition_limit=const.uiSizeEval, time_limit=const.uiSizeTimePeriod)


@logic_setting.route('/control_list', methods=['POST'])
def control_list():
    postData = request.values
    draw, start, length, columnIndex, columnName, sortOrder = datatable_head(postData)

    controlModel = models.Control
    controls = controlModel.query.outerjoin(models.Logic, models.Logic.logicid == controlModel.logicid) \
        .with_entities(controlModel.id, controlModel.name, controlModel.use_flag, controlModel.priority,
                       controlModel.mode) \
        .add_columns(models.Logic.name.label('logic_name'))

    beforeID = postData.get('beforeID')
    if check_null(beforeID):
        controls = controls.filter(or_(controlModel.logicid == '0', controlModel.id == beforeID))

    totalCount = controls.count()

    # if columnName == "useflag":
    #     sortObj = controlModel.use_flag.asc() if sortOrder == "asc" else controlModel.use_flag.desc()
    # elif columnName == "name":
    #     sortObj = controlModel.name.asc() if sortOrder == "asc" else controlModel.name.desc()
    # elif columnName == "priority":
    #     sortObj = controlModel.type.asc() if sortOrder == "asc" else controlModel.type.desc()
    # elif columnName == "mode1":
    #     sortObj = controlModel.mode.asc() if sortOrder == "asc" else controlModel.mode.desc()
    # else:
    #     sortObj = controlModel.id.asc() if sortOrder == "asc" else controlModel.id.desc()

    sortObj = controlModel.id.asc()
    controls = controls.order_by(sortObj).offset(start).limit(length).all()
    # validList = get_logic_mem(LogicMemory.Const_Control, start, length, const.uiSizeCtrl) validList[ind]
    data_list = [{"id": control[0], "name": control[1], "use_flag": control[2], "priority": control[3],
                  "mode": control[4], "logic_name": control[5], "ind": start + ind + 1, "shm": "TRUE",
                  'useflag': config.USE_FLAG_KR[int(control[2])], 'mode1': config.USE_FLAG[int(control[4])]}
                 for ind, control in enumerate(controls)]

    return json.dumps(datatable_list(data_list, totalCount, draw))


@logic_setting.route('/recipe_list', methods=['POST'])
def recipe_list():
    draw, start, length, columnIndex, columnName, sortOrder = datatable_head(request.values)

    defModel = models.RecipeDef
    def_list = defModel.query
    totalCount = def_list.count()

    # if columnName == "name":
    #     sortObj = defModel.name.asc() if sortOrder == "asc" else defModel.name.desc()
    # else:
    #     sortObj = defModel.id.asc() if sortOrder == "asc" else defModel.id.desc()

    sortObj = defModel.id.asc()
    def_list = def_list.order_by(sortObj).offset(start).limit(length).all()
    selList = [{'id': def_list[ind].id, 'ind': start + ind + 1, 'name': def_list[ind].name} for ind in range(len(def_list))]

    return json.dumps(datatable_list(selList, totalCount, draw))


def get_logic_mem(buf_type='', start=0, length=1, limit=0):
    end = start + length
    end = end if limit > 0 and end < limit else limit
    logic_mem = LogicMemory.SharedMem_Logic()
    return logic_mem.get_buff(buf_type, start, end)


def get_valid(buf_type, start, length, limit):
    validList = get_logic_mem(buf_type, start, length, limit)
    return ["TRUE" if valid['val'] == 1 else "FALSE" for valid in validList]


@logic_setting.route('/condition_list', methods=['POST'])
def condition_list():
    postData = request.values
    draw, start, length, columnIndex, columnName, sortOrder = datatable_head(postData)

    data_list = []
    condModel = models.Condition
    conditions = condModel.query.outerjoin(models.ConditionGroup, models.ConditionGroup.id == condModel.condgroup) \
        .with_entities(condModel.id, condModel.name, condModel.type, condModel.use_flag, condModel.options,
                       condModel.condgroup) \
        .add_columns(models.ConditionGroup.name.label('condgroup_name'))

    beforeID = postData.get('beforeID')
    if check_null(beforeID):
        conditions = conditions.filter(or_(condModel.condgroup == '0', condModel.id == beforeID))

    totalCount = conditions.count()

    # if columnName == "use_flag":
    #     sortObj = condModel.use_flag.asc() if sortOrder == "asc" else condModel.use_flag.desc()
    # elif columnName == "name":
    #     sortObj = condModel.name.asc() if sortOrder == "asc" else condModel.name.desc()
    # elif columnName == "type":
    #     sortObj = condModel.type.asc() if sortOrder == "asc" else condModel.type.desc()
    # else:
    #     sortObj = condModel.id.asc() if sortOrder == "asc" else condModel.id.desc()

    sortObj = condModel.id.asc()
    conditions = conditions.order_by(sortObj).offset(start).limit(length).all()
    # validList = get_valid(LogicMemory.Const_Condition, start, length, const.uiSizeEval)
    for ind, condition in enumerate(conditions):
        result = {
            "id": condition[0],
            "name": condition[1],
            "type": condition[2],
            "use_flag": config.USE_FLAG_KR[int(condition[3])],
            "options": condition[4],
            "condgroup": condition[5],
            "condgroup_name": condition[6],
            "ind": start + ind + 1,
            # "valid": validList[ind],
            "valid": "TRUE"
        }

        settings = json.loads(result["options"])
        result.pop("options")
        for key, val in settings.items():
            result[key] = val

        result["desc"] = get_desc_str(result)
        result["type"] = config.VARIABLE_TYPE[result["type"]]
        for key, val in settings.items():
            result.pop(key)
        
        data_list.append(result)

    return json.dumps(datatable_list(data_list, totalCount, draw))


@logic_setting.route('/action_list', methods=['POST'])
def action_list():
    postData = request.values
    draw, start, length, columnIndex, columnName, sortOrder = datatable_head(postData)

    data_list = []
    actionModel = models.Action
    actions = actionModel.query.outerjoin(models.ActionGroup, models.ActionGroup.id == actionModel.actgroup) \
        .with_entities(actionModel.id, actionModel.name, actionModel.type, actionModel.use_flag, actionModel.options,
                       actionModel.order, actionModel.actgroup) \
        .add_columns(models.ActionGroup.name.label('actgroup_name'))

    beforeID = postData.get('beforeID')
    if check_null(beforeID):
        actions = actions.filter(or_(actionModel.actgroup == '0', actionModel.id == beforeID))

    totalCount = actions.count()

    # if columnName == "use_flag":
    #     sortObj = actionModel.use_flag.asc() if sortOrder == "asc" else actionModel.use_flag.desc()
    # elif columnName == "name":
    #     sortObj = actionModel.name.asc() if sortOrder == "asc" else actionModel.name.desc()
    # elif columnName == "type":
    #     sortObj = actionModel.type.asc() if sortOrder == "asc" else actionModel.type.desc()
    # elif columnName == "order":
    #     sortObj = actionModel.order.asc() if sortOrder == "asc" else actionModel.order.desc()
    # else:
    #     sortObj = actionModel.id.asc() if sortOrder == "asc" else actionModel.id.desc()

    sortObj = actionModel.id.asc()
    actions = actions.order_by(sortObj).offset(start).limit(length).all()
    # validList = get_logic_mem(LogicMemory.Const_Action, start, length, const.uiSizeAct)
    for ind, action in enumerate(actions):
        result = {
            "id": action[0],
            "name": action[1],
            "type": action[2],
            "use_flag": config.USE_FLAG_KR[int(action[3])],
            "options": action[4],
            "order": action[5],
            "actgroup": action[6],
            "actgroup_name": action[7],
            "ind": start + ind + 1,
            # "shm": validList[ind]
            "shm": {'status': '', 'busy': False, 'done': False, 'err': False}
        }

        settings = json.loads(result["options"])
        result.pop("options")
        for key, val in settings.items():
            result[key] = val

        result["desc"] = get_desc_str1(result)
        result["type"] = config.VARIABLE_TYPE[action[2]]
        for key, val in settings.items():
            result.pop(key)

        data_list.append(result)

    return json.dumps(datatable_list(data_list, totalCount, draw))


@logic_setting.route('/add_condition', methods=['POST'])
@login_required
def add_condition():
    postData = request.form.to_dict()
    selid = postData.get("selid")
    conditionName = postData.get("condition_name")
    conditionType = postData.get("condition_type")
    if check_null(selid) and check_null(conditionName) and check_null(conditionType):
        postData.pop("selid")
        postData.pop("condition_name")
        postData.pop("condition_type")
        useFlag = postData.get("use_flag")
        postData.pop("use_flag")

        selid = int(selid)
        if selid > 0:
            selCondition = models.Condition.query.filter_by(id=selid).first()
            if selCondition:
                selCondition.name = conditionName
                selCondition.type = conditionType
                selCondition.use_flag = useFlag
                selCondition.options = json.dumps(postData)

                db.session.commit()
                response = {"status": True}
            else:
                response = {"status": False, "message": "No "}
        else:
            newCondition = models.Condition(
                name=conditionName,
                type=conditionType,
                use_flag=useFlag,
                condgroup="0",
                options=json.dumps(postData),
                condoptions="",
                ind="1000"
            )

            db.session.add(newCondition)
            db.session.commit()
            response = {"status": True}
    else:
        response = {"status": False, "message": "Invalid Condition Data"}

    return json.dumps(response)


@logic_setting.route('remove_condition', methods=['POST'])
@login_required
def remove_condition():
    postData = request.values
    selIDS = postData.get('selRow')
    if check_null(selIDS):
        selIDS = selIDS.split(",")
        for selid in selIDS:
            models.Condition.query.filter_by(id=selid).delete()

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


@logic_setting.route('/edit_condition', methods=['POST'])
@login_required
def edit_condition():
    postData = request.values
    selID = postData.get('selid')
    if check_null(selID):
        selCondition = models.Condition.query.filter_by(id=selID).first()
        selData = {
            'type': selCondition.type,
            'name': selCondition.name,
            'use_flag': selCondition.use_flag,
            'options': selCondition.options
        }
        response = {'status': True, 'data': selData}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_setting.route('/condition_group')
@login_required
def condgroup():
    alarms = models.Alarm.query.all()
    return render_template('logic_setting/condition_group.html', condgroup_limit=const.uiSizeEvalGrp,
                           condition_limit=const.uiSizeEval, time_limit=const.uiSizeTimePeriod,
                           alarms=alarms, remotes=get_remotes())


@logic_setting.route('/condgroup_list', methods=['POST'])
@login_required
def condgroup_list():
    postData = request.values
    draw, start, length, columnIndex, columnName, sortOrder = datatable_head(postData)

    condgroupModel = models.ConditionGroup
    condgroups = condgroupModel.query.outerjoin(models.Control, condgroupModel.controlid == models.Control.id) \
        .with_entities(condgroupModel.id, condgroupModel.name, condgroupModel.controlid, condgroupModel.operator,
                       condgroupModel.reverse) \
        .add_columns(models.Control.name.label('control_name'))

    beforeID = postData.get('beforeID')
    if check_null(beforeID):
        condgroups = condgroups.filter(or_(condgroupModel.controlid == '0', condgroupModel.id == beforeID))
    #else:
    #    condgroups = condgroups.filter(condgroupModel.controlid == '0')

    totalCount = condgroups.count()

    # if columnName == "name":
    #     sortObj = condgroupModel.name.asc() if sortOrder == "asc" else condgroupModel.name.desc()
    # elif columnName == "operator":
    #     sortObj = condgroupModel.operator.asc() if sortOrder == "asc" else condgroupModel.operator.desc()
    # elif columnName == "reverse":
    #     sortObj = condgroupModel.reverse.asc() if sortOrder == "asc" else condgroupModel.reverse.desc()
    # else:
    #     sortObj = condgroupModel.id.asc() if sortOrder == "asc" else condgroupModel.id.desc()

    sortObj = condgroupModel.id.asc()
    condgroups = condgroups.order_by(sortObj).offset(start).limit(length).all()
    # validList = get_valid(LogicMemory.Const_CondGroup, start, length, const.uiSizeEvalGrp)
    data_list = [{"id": condgroup[0], "name": condgroup[1], "controlid": condgroup[2], "operator": condgroup[3],
                  "reverse": config.USE_FLAG[int(condgroup[4])], "control_name": condgroup[5], "ind": start + ind + 1,
                  "valid": "TRUE"} for ind, condgroup in enumerate(condgroups)]

    return json.dumps(datatable_list(data_list, totalCount, draw))

@logic_setting.route('/condgroup_list_setting', methods=['POST'])
@login_required
def condgroup_list_setting():
    postData = request.values
    draw, start, length, columnIndex, columnName, sortOrder = datatable_head(postData)

    condgroupModel = models.ConditionGroup
    condgroups = condgroupModel.query.outerjoin(models.Control, condgroupModel.controlid == models.Control.id) \
        .with_entities(condgroupModel.id, condgroupModel.name, condgroupModel.controlid, condgroupModel.operator,
                       condgroupModel.reverse) \
        .add_columns(models.Control.name.label('control_name'))

    #beforeID = postData.get('beforeID')
    #if check_null(beforeID):
    #    condgroups = condgroups.filter(or_(condgroupModel.controlid == '0', condgroupModel.id == beforeID))
    #else :
    #    condgroups = condgroups.filter(condgroupModel.controlid == '0')
    condgroups = condgroups.filter(condgroupModel.controlid == '0')
    totalCount = condgroups.count()

    sortObj = condgroupModel.id.asc()
    condgroups = condgroups.order_by(sortObj).offset(start).limit(length).all()
    data_list = [{"id": condgroup[0], "name": condgroup[1], "controlid": condgroup[2], "operator": condgroup[3],
                  "reverse": config.USE_FLAG[int(condgroup[4])], "control_name": condgroup[5], "ind": start + ind + 1,
                  "valid": "TRUE"} for ind, condgroup in enumerate(condgroups)]

    return json.dumps(datatable_list(data_list, totalCount, draw))

@logic_setting.route('/actgroup_list', methods=['POST'])
@login_required
def actgroup_list():
    postData = request.values
    draw, start, length, columnIndex, columnName, sortOrder = datatable_head(postData)

    actgroupModel = models.ActionGroup
    actGroups = actgroupModel.query.outerjoin(models.Control, actgroupModel.controlid == models.Control.id) \
        .with_entities(actgroupModel.id, actgroupModel.name, actgroupModel.controlid, actgroupModel.mode,
                       actgroupModel.cnt) \
        .add_columns(models.Control.name.label('control_name'))

    beforeID = postData.get('beforeID')
    if check_null(beforeID):
        actGroups = actGroups.filter(or_(actgroupModel.controlid == '0', actgroupModel.id == beforeID))

    totalCount = actGroups.count()

    # if columnName == "name":
    #     sortObj = actgroupModel.name.asc() if sortOrder == "asc" else actgroupModel.name.desc()
    # elif columnName == "mode":
    #     sortObj = actgroupModel.mode.asc() if sortOrder == "asc" else actgroupModel.mode.desc()
    # elif columnName == "cnt":
    #     sortObj = actgroupModel.cnt.asc() if sortOrder == "asc" else actgroupModel.cnt.desc()
    # else:
    #     sortObj = actgroupModel.id.asc() if sortOrder == "asc" else actgroupModel.id.desc()

    sortObj = actgroupModel.id.asc()
    actGroups = actGroups.order_by(sortObj).offset(start).limit(length).all()
    # validList = get_logic_mem(LogicMemory.Const_ActGroup, start, length, const.uiSizeActGrp) validList[ind]
    data_list = [{"id": condgroup[0], "name": condgroup[1], "mode": config.ACTION_GROUP_MODE[condgroup[3]],
                  "cnt": condgroup[4], "control_name": condgroup[5], "ind": start + ind + 1, "mode1": condgroup[3],
                  "run": "TRUE"} for ind, condgroup in enumerate(actGroups)]

    return json.dumps(datatable_list(data_list, totalCount, draw))

@logic_setting.route('/actgroup_list_setting', methods=['POST'])
@login_required
def actgroup_list_setting():
    postData = request.values
    draw, start, length, columnIndex, columnName, sortOrder = datatable_head(postData)

    actgroupModel = models.ActionGroup
    actGroups = actgroupModel.query.outerjoin(models.Control, actgroupModel.controlid == models.Control.id) \
        .with_entities(actgroupModel.id, actgroupModel.name, actgroupModel.controlid, actgroupModel.mode,
                       actgroupModel.cnt) \
        .add_columns(models.Control.name.label('control_name'))

    #beforeID = postData.get('beforeID')
    #if check_null(beforeID):
    #    actGroups = actGroups.filter(or_(actgroupModel.controlid == '0', actgroupModel.id == beforeID))
    #else:
    #    actGroups = actGroups.filter(actgroupModel.controlid == '0')
    actGroups = actGroups.filter(actgroupModel.controlid == '0')

    totalCount = actGroups.count()

    # if columnName == "name":
    #     sortObj = actgroupModel.name.asc() if sortOrder == "asc" else actgroupModel.name.desc()
    # elif columnName == "mode":
    #     sortObj = actgroupModel.mode.asc() if sortOrder == "asc" else actgroupModel.mode.desc()
    # elif columnName == "cnt":
    #     sortObj = actgroupModel.cnt.asc() if sortOrder == "asc" else actgroupModel.cnt.desc()
    # else:
    #     sortObj = actgroupModel.id.asc() if sortOrder == "asc" else actgroupModel.id.desc()

    sortObj = actgroupModel.id.asc()
    actGroups = actGroups.order_by(sortObj).offset(start).limit(length).all()
    # validList = get_logic_mem(LogicMemory.Const_ActGroup, start, length, const.uiSizeActGrp) validList[ind]
    data_list = [{"id": condgroup[0], "name": condgroup[1], "mode": config.ACTION_GROUP_MODE[condgroup[3]],
                  "cnt": condgroup[4], "control_name": condgroup[5], "ind": start + ind + 1, "mode1": condgroup[3],
                  "run": "TRUE"} for ind, condgroup in enumerate(actGroups)]

    return json.dumps(datatable_list(data_list, totalCount, draw))


@logic_setting.route('/action')
@login_required
def action():
    return render_template('logic_setting/action.html', remotes=get_remotes(), action_limit=const.uiSizeCtrl,
                           channel_limit=const.uiSizeUserDefComm, frame_limit=const.uiSizeUserDefCommFrame,
                           defLimit=const.uiSizeRecipeDef, recipeLimit=const.uiSizeRecipe,
                           recipeVarLimit=const.uiSizeRecipeVars)


@logic_setting.route('/remove_action', methods=['POST'])
@login_required
def remove_action():
    selIDS = request.values.get('selRow')
    if check_null(selIDS):
        selIDS = selIDS.split(",")
        for selid in selIDS:
            models.Action.query.filter_by(id=selid).delete()

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)

@logic_setting.route('/remove_action_in_action_group', methods=['POST'])
@login_required
def remove_action_in_action_group():
    postData = request.values
    action_ids = postData.get('selRow')
    if check_null(action_ids):
        action_ids = action_ids.split(",")
        for action_id in action_ids:
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

@logic_setting.route('/update_action', methods=['POST'])
@login_required
def update_action():
    postData = request.form.to_dict()
    selid = postData.get('selid')
    action_name = postData.get('action_name')
    action_order = postData.get('action_order')
    action_type = postData.get('action_type')

    if check_null(action_name) and check_null(action_order) and check_null(selid) and check_null(action_type):
        postData.pop('action_name', None)
        postData.pop('action_order', None)
        postData.pop('action_type', None)
        use_flag = postData.get('use_flag')
        postData.pop('use_flag', None)
        selid = int(selid)
        if selid > 0:
            selAction = models.Action.query.filter_by(id=selid).first()
            if selAction:
                selAction.name = action_name
                selAction.order = action_order
                selAction.use_flag = use_flag
                selAction.type = action_type
                selAction.options = json.dumps(postData)

                db.session.commit()
                response = {'status': True}
            else:
                response = {'message': 'Action not found', 'status': False}
        else:
            newAction = models.Action(
                name=action_name,
                order=action_order,
                use_flag=use_flag,
                type=action_type,
                actgroup="0",
                actoptions="",
                ind="1000",
                options=json.dumps(postData)
            )

            db.session.add(newAction)
            db.session.commit()
            response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_setting.route('/edit_action', methods=['POST'])
@login_required
def edit_action():
    postData = request.values
    selID = postData.get('selid')
    if check_null(selID):
        selCondition = models.Action.query.filter_by(id=selID).first()
        selData = {
            'type': selCondition.type,
            'name': selCondition.name,
            'order': selCondition.order,
            'use_flag': int(selCondition.use_flag),
            'options': selCondition.options
        }
        if selCondition.type == 'FUNCTION' and len(selCondition.options) > 0:
            optionArr = json.loads(selCondition.options)
            funcID = optionArr['func_select_selid']
            in_list, out_list = in_out_list(funcID)
            selData['in_list'] = in_list
            selData['out_list'] = out_list

        response = {'status': True, 'data': selData}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_setting.route('/action_group')
@login_required
def action_group():
    return render_template('logic_setting/action_group.html', actgroup_limit=const.uiSizeActGrp,
                           action_limit=const.uiSizeCtrl, channel_limit=const.uiSizeUserDefComm,
                           frame_limit=const.uiSizeUserDefCommFrame, defLimit=const.uiSizeRecipeDef,
                           recipeLimit=const.uiSizeRecipe, recipeVarLimit=const.uiSizeRecipeVars)


@logic_setting.route('/control')
@login_required
def control():
    alarms = models.Alarm.query.all()
    return render_template('logic_setting/control.html', control_limit=const.uiSizeCtrl,
                           condgroup_limit=const.uiSizeEvalGrp, actgroup_limit=const.uiSizeActGrp,
                           action_limit=const.uiSizeAct, condition_limit=const.uiSizeEval,
                           time_limit=const.uiSizeTimePeriod, alarms=alarms, remotes=get_remotes())


@logic_setting.route('/recipe')
@login_required
def recipe_panel():
    return render_template('logic_setting/recipe.html', defLimit=const.uiSizeRecipeDef, remotes=get_remotes(),
                           recipeLimit=const.uiSizeRecipe, recipeVarLimit=const.uiSizeRecipeVars)


@logic_setting.route('/new_def', methods=['POST'])
@login_required
def new_def():
    postData = request.values
    inputName = postData.get('inputName')
    defID = postData.get('recipeDefID')
    if check_null(inputName) and check_null(defID):
        if int(defID) > 0:
            selDef = models.RecipeDef.query.filter_by(id=defID).first()
            selDef.name = inputName
        else:
            newDef = models.RecipeDef(
                name=inputName
            )
            db.session.add(newDef)

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_setting.route('/recipe_variable', methods=['POST'])
@login_required
def recipe_variable():
    postData = request.values
    recipeDefID = postData.get('recipeDefID')
    inputVal = postData.get('inputVal')
    if check_null(recipeDefID) and check_null(inputVal):
        newVar = models.RecipeVar(
            def_id=recipeDefID,
            name=inputVal,
            sellocstr=postData.get('sellocstr'),
            selid=postData.get('selid'),
            type=postData.get('seltype'),
            order=0,
            ind=0
        )

        db.session.add(newVar)
        db.session.commit()

        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_setting.route('/update_variable', methods=['POST'])
@login_required
def update_variable():
    postData = request.form.to_dict()
    trVal = postData.get('trVal')
    remote = postData.get('remote')

    print (trVal, remote)

    if check_null(trVal) and check_null(remote):
        selVariable = models.Variable.query.filter_by(type=trVal).filter_by(remote=remote).first()
        if selVariable:
            if 'inputName' in postData:
                selVariable.name = postData.get('inputName')
            elif 'inputUnit' in postData:
                selVariable.unit = postData.get('inputUnit')
            elif 'inputDefault' in postData:
                selVariable.defaults = postData.get('inputDefault')
        else:
            newVariable = models.Variable(
                ind='',
                type=trVal,
                use_flag='0',
                remote=remote,
                name=postData.get('inputName') if 'inputName' in postData else '',
                unit=postData.get('inputUnit') if 'inputUnit' in postData else '',
                defaults=postData.get('inputDefault') if 'inputDefault' in postData else ''
            )
            db.session.add(newVariable)

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invaid request'}

    return json.dumps(response)


@logic_setting.route('/variable_list', methods=['POST'])
@login_required
def variable_list():
    postData = request.values
    draw, start, length, columnIndex, columnName, sortOrder = datatable_head(postData)
    # searchValue = postData.get('search[value]')

    remoteID = postData.get('variable_id')
    variable_type = postData.get('variable_type')
    variable1 = postData.get('variable').split('-')
    variableStr = "LOCAL." if variable1[0] == "local" else "REMOTE." + variable1[1] + "."
    
    totalCount = 0
    variable_type1 = config.VARIABLE_MATCH[variable_type]
    variableStr += variable_type1 + "."
    if variable_type1 == "DG":
        totalCount = const.uiSizeDigital
    elif variable_type1 == "AN":
        totalCount = const.uiSizeAnalog
    elif variable_type1 == "ST":
        totalCount = const.uiSizeString
    elif variable_type1 == "DT":
        totalCount = const.uiSizeDate
    elif variable_type1 == "TM":
        totalCount = const.uiSizeTime

    if start > totalCount:
        start = 0

    selList = []
    sortOrder = "asc"
    step = 1 if sortOrder == "asc" else -1
    end = start + length if sortOrder == "asc" else totalCount - start - length
    start = start if sortOrder == "asc" else totalCount - start - 1

    if end >= totalCount:
        end = totalCount
    elif end < 0:
        end = 0

    if remoteID != '0':
        data_list_count = models.Variable.query.filter_by(remote=remoteID).filter_by(use_flag="1").filter(models.Variable.type.ilike('%'+variable_type+'%')).all()
        totalCount = len(data_list_count)
    
    orderObj = models.Variable.addr_id.asc()
    data_list = models.Variable.query.filter_by(remote=remoteID).filter_by(use_flag="1").filter(models.Variable.type.ilike('%'+variable_type+'%')).order_by(orderObj).offset(start).limit(length).all()
    
    if remoteID != '0':
        for i in range(len(data_list)):
            itemStr = variable_type + "-" + str(i)

            nameEnd =  str(data_list[i].addr_id) if data_list[i].addr_id is not None else str(i)
            itemName = data_list[i].name if data_list[i] and len(data_list[i].name) > 0 else config.VARIABLE_TYPE[variable_type.upper()] +nameEnd

            itemUnit = data_list[i].unit if data_list[i] else ''
            itemChk = data_list[i].use_flag if data_list[i] else '0'
            itemDefault = data_list[i].defaults if data_list[i] else ''
            
            adressEnd = str(data_list[i].addr_id) if data_list[i].addr_id is not None  else str(i)
            selList.append({'id': i, 'address': variableStr +adressEnd , 'name': itemName, 'chk': itemChk, 'unit': itemUnit, 'default': itemDefault, 'addr_id': data_list[i].addr_id, 'remote_id': remoteID})
    else:
        for i in range(start, end, step):
            itemStr = variable_type + "-" + str(i)
            selVar = models.Variable.query.filter_by(remote=remoteID).filter_by(type=itemStr).first()

            itemName = selVar.name if selVar and len(selVar.name) > 0 else config.VARIABLE_TYPE[
                                                                            variable_type.upper()] + str(i)
            itemUnit = selVar.unit if selVar else ''
            itemChk = selVar.use_flag if selVar else '0'
            itemDefault = selVar.defaults if selVar else ''
            selList.append({'id': i, 'address': variableStr + str(i), 'name': itemName, 'chk': itemChk, 'unit': itemUnit,
                            'default': itemDefault, 'remote_id': remoteID, 'addr_id': str(i)})
    
    
    return json.dumps(datatable_list(selList, totalCount, draw))


@logic_setting.route('/remote_list', methods=['POST'])
@login_required
def remote_list():
    postData = request.values
    draw, start, length, columnIndex, columnName, sortOrder = datatable_head(postData)
    # searchValue = postData.get('search[value]')

    remoteID = postData.get('variable_id')
    variable_type = postData.get('variable_type')
    variable1 = postData.get('variable').split('-')
    variableStr = "LOCAL." if variable1[0] == "local" else "REMOTE." + variable1[1] + "."
    
    totalCount = 0
    variable_type1 = config.VARIABLE_MATCH[variable_type]
    variableStr += variable_type1 + "."
    if variable_type1 == "DG":
        totalCount = const.uiSizeDigital
    elif variable_type1 == "AN":
        totalCount = const.uiSizeAnalog
    elif variable_type1 == "ST":
        totalCount = const.uiSizeString
    elif variable_type1 == "DT":
        totalCount = const.uiSizeDate
    elif variable_type1 == "TM":
        totalCount = const.uiSizeTime

    if start > totalCount:
        start = 0

    selList = []
    sortOrder = "asc"
    step = 1 if sortOrder == "asc" else -1
    end = start + length if sortOrder == "asc" else totalCount - start - length
    start = start if sortOrder == "asc" else totalCount - start - 1

    if end >= totalCount:
        end = totalCount
    elif end < 0:
        end = 0
    
    for i in range(start, end, step):
        itemStr = variable_type + "-" + str(i)
        selVar = models.Variable.query.filter_by(remote=remoteID).filter_by(type=itemStr).first()

        itemName = selVar.name if selVar and len(selVar.name) > 0 else config.VARIABLE_TYPE[
                                                                           variable_type.upper()] + str(i)
        itemUnit = selVar.unit if selVar else ''
        itemChk = selVar.use_flag if selVar else '0'
        itemDefault = selVar.defaults if selVar else ''
        selList.append({'id': i, 'address': variableStr + str(i), 'name': itemName, 'chk': itemChk, 'unit': itemUnit,
                        'default': itemDefault})

    
    return json.dumps(datatable_list(selList, totalCount, draw))


@logic_setting.route('/remove_recipe', methods=['POST'])
@login_required
def remove_recipe():
    postData = request.values 
    selIDs = postData.get('selRow')
    if check_null(selIDs):
        selType = postData.get('selType')
        selIDs = selIDs.split(',')
        if selType and len(selType) > 0:
            recipeDefID = postData.get('recipeDefID')
            if selType == "var":
                selModel = models.RecipeVar
                for selID in selIDs:
                    models.RecipeValue.query.filter(models.RecipeValue.def_id == recipeDefID) \
                        .filter(models.RecipeValue.var_id == selID).delete()
            else:
                selModel = models.RecipeName
                for selID in selIDs:
                    models.RecipeValue.query.filter(models.RecipeValue.def_id == recipeDefID) \
                        .filter(models.RecipeValue.name_id == selID).delete()
        else:
            selModel = models.RecipeDef
            for selID in selIDs:
                models.RecipeVar.query.filter_by(def_id=selID).delete()
                models.RecipeName.query.filter_by(def_id=selID).delete()
                models.RecipeValue.query.filter_by(def_id=selID).delete()

        for selID in selIDs:
            selModel.query.filter_by(id=selID).delete()

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_setting.route('/func_list', methods=['POST'])
@login_required
def func_list():
    postData = request.values
    draw, start, length, columnIndex, columnName, sortOrder = datatable_head(postData)

    funcModel = models.ExecFunc
    totalCount = funcModel.query.count()
    data_list = funcModel.query.with_entities(funcModel.id, funcModel.group, funcModel.name, funcModel.desc)

    # if columnIndex == '1':
    #     orderObj = funcModel.group.asc() if sortOrder == 'asc' else funcModel.group.desc()
    # elif columnIndex == '2':
    #     orderObj = funcModel.name.asc() if sortOrder == 'asc' else funcModel.name.desc()
    # else:
    #     orderObj = funcModel.desc.asc() if sortOrder == 'asc' else funcModel.desc.desc()

    orderObj = funcModel.desc.asc()
    data_list = data_list.order_by(orderObj).offset(start).limit(length).all()
    selList = [{'id': data.id, 'group': data.group, 'name': data.name, 'desc': data.desc} for data in data_list]

    return json.dumps(datatable_list(selList, totalCount, draw))


def in_out_list(funcID):
    selFunc = models.ExecFunc.query.with_entities(models.ExecFunc.name).filter_by(id=funcID).first()
    funcOut = models.FuncOutput.query.filter_by(func_name=selFunc.name).all()
    funcIn = models.FuncInput.query.filter_by(func_name=selFunc.name).all()

    in_list = [{'id': item.id, 'name': item.input_desc, 'type': item.data_type, 'control': item.control,
                'combo': item.combo_member, 'min': item.min_value, 'max': item.max_value, 'len': item.string_max_len,
                'default': item.default_value} for item in funcIn]
    out_list = [{'id': item.id, 'name': item.output_desc, 'type': item.var_type} for item in funcOut]

    return in_list, out_list


@logic_setting.route('/func_inout', methods=['POST'])
@login_required
def func_inout():
    postData = request.values
    selID = postData.get('selid')
    if check_null(selID):
        in_list, out_list = in_out_list(selID)
        response = {'status': True, 'out_list': out_list, 'in_list': in_list}
    else:
        response = {'status': False, 'message': 'Invaid request'}

    return json.dumps(response)


@logic_setting.route('/recipe_detail', methods=['POST'])
@login_required
def recipe_detail():
    recipeDefID = request.values.get('recipeDefID')
    if check_null(recipeDefID):
        varList = models.RecipeVar.query.filter_by(def_id=recipeDefID).all()
        var_list = [{'id': var.id, 'name': var.name, 'type': var.selid} for var in varList]

        recipeNames = models.RecipeName.query.filter_by(def_id=recipeDefID).all()
        name_list = [{'id': var.id, 'name': var.name} for var in recipeNames]

        recipeValues = models.RecipeValue.query.filter_by(def_id=recipeDefID).all()
        value_list = [
            {'id': var.id, 'var_id': var.var_id, 'value': var.value, 'options': var.options, 'name_id': var.name_id} for
            var in recipeValues]

        response = {'status': True, 'var_list': var_list, 'name_list': name_list, 'value_list': value_list}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_setting.route('/recipe_name', methods=['POST'])
@login_required
def recipe_name():
    postData = request.values
    selID = postData.get('selid')
    inputName = postData.get('inputName')
    recipeDefID = postData.get('recipeDefID')
    if check_null(inputName) and check_null(selID) and check_null(recipeDefID):
        if int(selID) > 0:
            selName = models.RecipeName.query.filter_by(id=selID).first()
            selName.name = inputName
        else:
            newName = models.RecipeName(
                name=inputName,
                def_id=recipeDefID
            )

            db.session.add(newName)

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_setting.route('/recipe_val', methods=['POST'])
@login_required
def recipe_val():
    postData = request.form.to_dict()
    recipeDefID = postData.get('recipeDefID')
    varID = postData.get('var_id')
    nameID = postData.get('name_id')
    if check_null(recipeDefID) and check_null(varID) and check_null(nameID):
        selVal = models.RecipeValue.query.filter(models.RecipeValue.def_id == recipeDefID) \
            .filter(models.RecipeValue.var_id == varID).filter(models.RecipeValue.name_id == nameID).first()
        postData.pop('var_id')
        postData.pop('name_id')
        postData.pop('recipeDefID')
        inputName = postData.get('inputName')
        postData.pop('inputName')
        if selVal:
            selVal.value = inputName
            selVal.options = json.dumps(postData)
        else:
            newVal = models.RecipeValue(
                def_id=recipeDefID,
                var_id=varID,
                name_id=nameID,
                options=json.dumps(postData),
                value=inputName,
                ind=0
            )
            db.session.add(newVal)

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_setting.route('/logic_option', methods=['POST'])
@login_required
def logic_option():
    postData = request.form.to_dict()
    selID = postData.get('selID')
    selType = postData.get('selType')
    if check_null(selID) and check_null(selType):
        postData.pop('selID')
        postData.pop('selType')
        optionStr = json.dumps(postData)
        if selType == "cond_group":
            selCondGroup = models.ConditionGroup.query.filter_by(id=selID).first()
            if selCondGroup:
                selCondGroup.options = optionStr
        elif selType == "act_group":
            selActGroup = models.ActionGroup.query.filter_by(id=selID).first()
            if selActGroup:
                selActGroup.options = optionStr
        elif selType == "condition":
            selCondition = models.Condition.query.filter_by(id=selID).first()
            if selCondition:
                selCondition.condoptions = optionStr
        elif selType == "action":
            selAction = models.Action.query.filter_by(id=selID).first()
            if selAction:
                selAction.actoptions = optionStr
        elif selType == "control":
            selControl = models.Control.query.filter_by(id=selID).first()
            if selControl:
                selControl.options = optionStr
        elif selType == "logic":
            selLogic = models.Logic.query.filter_by(id=selID).first()
            if selLogic:
                selLogic.options = optionStr
        elif selType == "monitor":
            selMonitor = models.Monitor.query.filter_by(id=selID).first()
            if selMonitor:
                selMonitor.options = optionStr

                if postData.get('bool_file') == "1":
                    if postData.get('new_file') == '1':
                        selFile = request.files['file']
                        chkPath = config.UPLOAD_FOLDER + "back/"
                        if not os.path.exists(chkPath):
                            os.makedirs(chkPath)

                        uploadPath = "back/" + selFile.filename
                        selFile.save(os.path.join(config.UPLOAD_FOLDER, uploadPath))
                        selMonitor.back_img = uploadPath
                    else:
                        selMonitor.back_img = ""
        elif selType == "element":
            selElement = models.MonitorElement.query.filter_by(id=selID).first()
            if selElement:
                selElement.elemoptions = optionStr

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@logic_setting.route('/write_variable', methods=['POST'])
@login_required
@mode_check('run')
def write_variable():
    postData = request.values
    variableAddr = postData.get('varAdd')
    variableType = postData.get('varType')
    writeValue = postData.get('writeValue')
    if check_null(writeValue) and check_null(variableAddr) and check_null(variableType):
        local_shm = LocalVar.SharedMem_LocalVar()
        response = local_shm.set_buff(variableAddr, variableType, writeValue)
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)

@logic_setting.route('/get_page_number', methods=['POST'])
@login_required
def get_page_number():
    postData = request.values
    remoteID = postData.get('remote_id')
    length = postData.get('length')
    variableAddr = postData.get('variable_addr')
    variableType = postData.get('variable_type')
    print(remoteID, length, variableAddr, variableType)
    pageNum = 0

    if check_null(remoteID) and check_null(length) and check_null(variableAddr) and check_null(variableType):
        pageNum = models.Variable.query.filter(models.Variable.remote==remoteID, models.Variable.use_flag=="1", models.Variable.addr_id<=variableAddr, models.Variable.type.ilike('%'+variableType+'%')).count()
        if(int(pageNum) > 0):
            pageNum = int((int(pageNum) - 1)/int(length)) + 1
        print(pageNum)
    else:
        pageNum = 0
    return json.dumps(pageNum)