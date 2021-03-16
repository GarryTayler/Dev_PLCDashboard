from flask import render_template, Blueprint, request, send_file
from app.views.controllers.user import login_required
from app.helper.common import check_null, get_remotes, datatable_list, datatable_head
from app import models, db, config
from app.helper.const import uiSizeAlarm
import json, csv

data_set = Blueprint('data_set', __name__, url_prefix='/data_set')


@data_set.route('/collect')
@login_required
def collect():
    setting = models.CollectSet.query.filter_by(name='data_set').first()
    return render_template('data_set/collect.html', remotes=get_remotes(), setting=setting)


@data_set.route('/add_variable', methods=['POST'])
@login_required
def add_variable():
    postData = request.form.to_dict()
    selIDs = postData.get('selIDs')
    if check_null(selIDs):
        selIDs = selIDs.split(',')
        for selid in selIDs:
            selArr = selid.split(';')
            selArr1 = selArr[1].split('-')

            selArr2 = selArr[2].split('-')
            variableStr = "LOCAL." if 'local-' in selArr[2] else "REMOTE." + selArr2[1] + "."
            variableStr += config.VARIABLE_MATCH[selArr1[0]] + "." + selArr1[1]

            selVar = models.Variable.query.filter_by(remote=selArr[0]).filter_by(type=selArr[1]).first()
            itemName = selVar.name if selVar and len(selVar.name) > 0 else config.VARIABLE_TYPE[selArr1[0].upper()] + \
                                                                           selArr1[1] + '(' + variableStr + ')'

            newVariable = models.DataCollect(
                width="1",
                type="line",
                use_flag="0",
                name=itemName,
                color="#ffffff",
                options=json.dumps({'selid': selArr[1], 'seltype': selArr[2], 'sellocstr': variableStr})
            )

            db.session.add(newVariable)

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@data_set.route('/remove_variable', methods=['POST'])
@login_required
def remove_variable():
    postData = request.values
    selIDS = postData.get('selRow')
    if check_null(selIDS):
        selIDS = selIDS.split(",")
        for selid in selIDS:
            models.DataCollect.query.filter_by(id=selid).delete()

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@data_set.route('/set_save', methods=['POST'])
@login_required
def set_save():
    postData = request.values
    set_name = postData.get('set_name')
    if check_null(set_name):
        setModel = models.CollectSet
        selSet = setModel.query.filter_by(name=set_name).first()
        if selSet:
            selSet.path = postData.get('save_path')
            selSet.interval = postData.get('save_interval', '')
            selSet.interval_unit = postData.get('interval_unit', '')
            selSet.limit = postData.get('alarm_limit')
            selSet.limit_val = postData.get('record_cnt', '')
            selSet.limit_unit = postData.get('record_unit', '')
        else:
            selSet = setModel(
                name=set_name,
                path=postData.get('save_path'),
                interval=postData.get('save_interval', ''),
                interval_unit=postData.get('interval_unit', ''),
                limit=postData.get('alarm_limit'),
                limit_val=postData.get('record_cnt', ''),
                limit_unit=postData.get('record_unit', '')
            )

            db.session.add(selSet)

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@data_set.route('/alarm')
@login_required
def alarm():
    setting = models.CollectSet.query.filter_by(name='alarm_set').first()
    return render_template('data_set/alarm.html', remotes=get_remotes(), alarm_limit=uiSizeAlarm, setting=setting)


@data_set.route('/create_alarm', methods=['POST'])
@login_required
def create_alarm():
    postData = request.values
    alarmName = postData.get('alarm_name')
    selID = postData.get('selid')
    if check_null(alarmName) and check_null(selID):
        if int(selID) > 0:
            selAlarm = models.Alarm.query.filter_by(id=selID).first()
            selAlarm.name = alarmName
            selAlarm.type = postData.get('alarm_type')
            selAlarm.confirm = postData.get('alarm_confirm')
            selAlarm.category = postData.get('alarm_category')
        else:
            newAlarm = models.Alarm(
                name=alarmName,
                type=postData.get('alarm_type'),
                confirm=postData.get('alarm_confirm'),
                category=postData.get('alarm_category'),
                options=""
            )
            db.session.add(newAlarm)

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid Alarm Data'}

    return json.dumps(response)


@data_set.route('/update_setting', methods=['POST'])
@login_required
def update_setting():
    postData = request.form.to_dict()
    selID = postData.get('alarm_id')
    if check_null(selID):
        selAlarm = models.Alarm.query.filter_by(id=selID).first()
        if selAlarm:
            postData.pop('alarm_id')
            selAlarm.options = json.dumps(postData)
            db.session.commit()
            response = {'status': True}
        else:
            response = {'status': False, 'message': 'No alarm exists'}
    else:
        response = {'status': False, 'message': 'Invalid option data'}

    return json.dumps(response)


@data_set.route('/remove_alarm', methods=['POST'])
@login_required
def remove_alarm():
    postData = request.values
    selIDs = postData.get('selRow')
    if check_null(selIDs):
        selIDS = selIDs.split(",")
        for selid in selIDS:
            models.Alarm.query.filter_by(id=selid).delete()

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@data_set.route('/collect_list', methods=['POST'])
def collect_list():
    draw, start, length, columnIndex, columnName, sortOrder = datatable_head(request.values)

    chlModel = models.DataCollect
    data_list = chlModel.query
    totalCount = data_list.count()

    # if columnIndex == '2':
    #     orderObj = chlModel.options.asc() if sortOrder == 'asc' else chlModel.options.desc()
    # else:
    #     orderObj = chlModel.id.asc() if sortOrder == 'asc' else chlModel.id.desc()

    orderObj = chlModel.id.asc()
    data_list = data_list.order_by(orderObj).offset(start).limit(length).all()
    selList = [{'id': data_list[ind].id, 'ind': start + ind + 1, 'name': data_list[ind].name} for ind in
               range(len(data_list))]

    return json.dumps(datatable_list(selList, totalCount, draw))


def alarm_item(alarm, ind):
    return {'id': alarm.id, 'ind': ind, 'cat_str': config.ALARM_CATEGORY[alarm.category], 'name': alarm.name,
            'firm_str': config.ALARM_CONFIRM[alarm.confirm], 'type_str': config.ALARM_TYPE[alarm.type],
            'category': alarm.category, 'confirm': alarm.confirm, 'type': alarm.type, 'options': alarm.options}


@data_set.route('/alarm_list', methods=['POST'])
def alarm_list():
    draw, start, length, columnIndex, columnName, sortOrder = datatable_head(request.values)

    chlModel = models.Alarm
    data_list = chlModel.query
    totalCount = data_list.count()

    # if columnIndex == '2':
    #     orderObj = chlModel.category.asc() if sortOrder == 'asc' else chlModel.category.desc()
    # elif columnIndex == '3':
    #     orderObj = chlModel.name.asc() if sortOrder == 'asc' else chlModel.name.desc()
    # elif columnIndex == '4':
    #     orderObj = chlModel.confirm.asc() if sortOrder == 'asc' else chlModel.confirm.desc()
    # elif columnIndex == '5':
    #     orderObj = chlModel.type.asc() if sortOrder == 'asc' else chlModel.type.desc()
    # else:
    #     orderObj = chlModel.id.asc() if sortOrder == 'asc' else chlModel.id.desc()

    orderObj = chlModel.id.asc()
    data_list = data_list.order_by(orderObj).offset(start).limit(length).all()
    selList = [alarm_item(data_list[ind], start + ind + 1) for ind in range(len(data_list))]

    return json.dumps(datatable_list(selList, totalCount, draw))


def make_collect(ind, collect_item):
    return [str(ind), collect_item.name]


def make_alarm(ind, alarm_item):
    return [str(ind), config.ALARM_CATEGORY[alarm_item.category], alarm_item.name,
            config.ALARM_CONFIRM[alarm_item.confirm], config.ALARM_TYPE[alarm_item.type]]


@data_set.route('/csv_export', defaults={'csvType': 'collect'})
@data_set.route('/csv_export/<csvType>')
@login_required
def csv_export(csvType='collect'):
    chlModel = models.DataCollect if csvType == "collect" else models.Alarm
    data_list = chlModel.query.all()
    data_list = [
        (make_collect(ind + 1, data_list[ind]) if csvType == "collect" else make_alarm(ind + 1, data_list[ind]))
        for ind in range(len(data_list))]
    with open(config.CONFIG_PATH + '\export.csv', "w", encoding='utf-8-sig', newline='') as csv_file:
        writer = csv.writer(csv_file)
        if csvType == "collect":
            writer.writerow(['번호', '변수'])
        else:
            writer.writerow(['번호', '분류', '이름', '해제', '타입'])

        for line in data_list:
            writer.writerow(line)

    fileName = '데이터수집.csv' if csvType == "collect" else '알람.csv'
    return send_file(config.CONFIG_PATH + '\export.csv', mimetype='text/csv', attachment_filename=fileName,
                     as_attachment=True)
