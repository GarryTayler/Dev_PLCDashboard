from flask import render_template, Blueprint, request, redirect, session
from app.views.controllers.user import login_required
from app.helper.common import check_null, get_remotes
from app import models, db, config
from flask_sqlalchemy import make_url
from sqlalchemy import cast, Integer, create_engine
from app.helper.LocalVar import SharedMem_LocalVar
import json, os

monitor = Blueprint('monitor', __name__, url_prefix='/monitor')


@monitor.route('/add_monitor', methods=['POST'])
@login_required
def add_monitor():
    postData = request.values
    inputName = postData.get('input_name')
    selID = postData.get('inputID')
    if check_null(inputName) and check_null(selID):
        if int(selID) > 0:
            newMonitor = models.Monitor.query.filter_by(id=selID).first()
            newMonitor.name = inputName
        else:
            newMonitor = models.Monitor(
                options="",
                back_img="",
                name=inputName
            )
            db.session.add(newMonitor)

        db.session.commit()
        db.session.refresh(newMonitor)
        response = {'status': True, 'selid': newMonitor.id}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@monitor.route('/detail', defaults={'selid': 0})
@monitor.route('/detail/<selid>')
@login_required
def detail(selid=0):
    if int(selid) > 0:
        selMonitor = models.Monitor.query.filter_by(id=selid).first()
        if selMonitor:
            collectModel = models.DataCollect
            variable_list = collectModel.query.filter(collectModel.options.ilike('%analog-%')).all()
            image_list = models.Upload.query.filter_by(userid=session.get('user_id')).all()
            element_list = models.MonitorElement.query.filter_by(monitorid=selid)\
                .order_by(cast(models.MonitorElement.ind, Integer)).all()

            for element in element_list:
                if element.type in ['read_val', 'set_val', 'table']:
                    element = element.__dict__
                    size_options = element['sizeoptions']
                    element.pop('sizeoptions')
                    options = json.loads(element['options'])

                    element['unit'] = ""

                    if element['type'] in ['read_val', 'set_val']:
                        if ('set_val_variable_seltype' in options or 'read_val_variable_seltype' in options):
                            if('set_val_variable_seltype' in options):
                                variable_type = options['set_val_variable_selid'].split('-')[0]
                                _key_value = 'set_val'
                            else:
                                variable_type = options['read_val_variable_selid'].split('-')[0]
                                _key_value = 'read_val'
                            if(variable_type == 'analog'):
                                variable_remote = options[_key_value + '_variable_seltype'].split('-')[1]
                                print(variable_remote, options[_key_value + '_variable_selid'])
                                unit_row = models.Variable.query.filter(models.Variable.remote == variable_remote, models.Variable.type == options[_key_value + '_variable_selid']).first()
                                if(unit_row is not None):
                                    element['unit'] = unit_row.unit
                                else:
                                    element['unit'] = ''

                    if len(size_options) > 0:
                        optArr = json.loads(size_options)
                        element['width'] = str(optArr['selWidth'])
                        element['height'] = str(optArr['selHeight'])
                    else:
                        element['width'] = ''
                        element['height'] = ''

                    if element['type'] in ['read_val', 'set_val']:
                        for key, val in options.items():
                            element[key] = val
                            if key in ['read_digital_on', 'read_digital_off', 'read_digital_icon', 'set_digital_icon']:
                                selImg = models.Upload.query.filter_by(id=val).first()
                                element[key + "_img"] = selImg.userid + '/' + selImg.url if selImg else ""

                        # var_arr = element[element['type'] + '_variable_seltype'].split('-')
                        # type_arr = element[element['type'] + '_variable_selid'].split('-')
                        # local_shm = SharedMem_LocalVar(var_arr[0])
                        # data_list = local_shm.get_buff(type_arr[0], int(type_arr[1]), int(type_arr[1]) + 1,
                        #                                int(var_arr[1]))
                        # element['shm_val'] = data_list[0]['val']
                        #
                        # if type_arr[0] == 'analog':
                        #     selItem = models.Variable.query.filter_by(remote=var_arr[1]).filter_by(
                        #         type=type_arr[0]).first()
                        #     unit_val = selItem.unit if selItem else ""
                        # else:
                        #     unit_val = ""
                        #
                        # element['unit'] = unit_val

                        element['shm_val'] = '21.5'
                    elif element['type'] == 'table':
                        for key, val in options.items():
                            if 'row-' in key or 'column-' in key:
                                element[key] = val
                            elif key == "max-row" or key == "max-column":
                                element[key] = int(val)
                            elif '-selid' in key or '-seltype' in key:
                                element[key] = val

                        for ind in range(element["max-row"]):
                            for ind1 in range(element["max-column"]):
                                indStr = 'table-' + str(ind) + "-" + str(ind1)
                                # var_arr = element[indStr + '-seltype'].split('-')
                                # type_arr = element[indStr + '-selid'].split('-')
                                # local_shm = SharedMem_LocalVar(var_arr[0])
                                # data_list = local_shm.get_buff(type_arr[0], int(type_arr[1]), int(type_arr[1]) + 1,
                                #                                int(var_arr[1]))
                                # element[indStr] = data_list[0]['val']
                                element[indStr] = '21.5'

            return render_template('monitor/detail.html', selMonitor=selMonitor, variable_list=variable_list,
                                   image_list=image_list, element_list=element_list, remotes=get_remotes())
        else:
            return redirect('/')
    else:
        return redirect('/')


@monitor.route('/chart_data', methods=['POST'])
def chart_data():
    postData = request.values
    selIDs = postData.get('selids')
    if check_null(selIDs):
        id_arr = selIDs.split(',')
        dataSet = models.CollectSet.query.filter_by(name='data_set').first()
        idArr = {}
        returnArr = {}
        collectModel = models.DataCollect
        if dataSet and len(id_arr) > 0:
            engine = create_engine(make_url('sqlite:///' + config.DB_SAVE_PATH + dataSet.path))
            for id_val in id_arr:
                fetchSql = "SELECT var_value, createdAt FROM var_logs WHERE var_id = '{}' ORDER BY id DESC LIMIT 10".format(id_val)
                results = engine.execute(fetchSql)
                selRow = collectModel.query.filter_by(id=id_val).with_entities(collectModel.name).first()
                if selRow:
                    idArr[selRow.name] = id_val
                    returnArr[selRow.name] = [{'value': row.var_value, 'create': row.createdAt[:16]} for row in results]
        response = {'status': True, 'rows': returnArr, 'ids': idArr}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@monitor.route('/remove_detail', methods=['Post'])
def remove_detail():
    postData = request.values
    selRow = postData.get('selRow')
    if check_null(selRow):
        models.Monitor.query.filter_by(id=selRow).delete()
        models.MonitorElement.query.filter_by(monitorid=selRow).delete()
        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@monitor.route('/add_element', methods=['POST'])
@login_required
def add_element():
    postData = request.form.to_dict()
    elemName = postData.get('elem_name')
    selType = postData.get('seltype')
    monitorID = postData.get('monitorID')
    selID = postData.get('selid')
    if check_null(selType) and check_null(monitorID) and check_null(elemName) and check_null(selID):
        postData.pop('selid')
        postData.pop('seltype')
        postData.pop('monitorID')
        postData.pop('elem_name')
        if int(selID) > 0:
            selElement = models.MonitorElement.query.filter_by(id=selID).first()
            if selElement:
                selElement.name = elemName
                selElement.type = selType
                selElement.options = json.dumps(postData)

                db.session.commit()
                response = {'status': True}
            else:
                response = {'status': False, 'message': 'No element exists'}
        else:
            newElement = models.MonitorElement(
                ind='1000',
                type=selType,
                name=elemName,
                elemoptions='{"bool_file": "0", "header_back": "#f8f9fc", "font_color": "black", "font_size": "13.6px", "font_family": "Nunito", "body_back": "white", "body_size": "16px", "body_color": "black", "body_family": "Nunito"}',
                sizeoptions='',
                monitorid=monitorID,
                options=json.dumps(postData)
            )

            db.session.add(newElement)
            db.session.commit()

            response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@monitor.route('/remove_element', methods=['POST'])
@login_required
def remove_element():
    postData = request.values
    elemID = postData.get('elemID')
    if check_null(elemID):
        selIDS = elemID.split(',')
        for selid in selIDS:
            models.MonitorElement.query.filter_by(id=selid).delete()

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@monitor.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    postData = request.files
    if 'file' in postData:
        selFile = postData['file']
        selUserID = session.get('user_id')
        selFile1 = models.Upload.query.filter(models.Upload.url == selFile.filename)\
            .filter(models.Upload.userid == selUserID).first()
        if selFile1:
            response = {'status': False, 'message': 'Same name file exists!'}
        else:
            chkPath = config.UPLOAD_FOLDER + str(selUserID)
            if not os.path.exists(chkPath):
                os.makedirs(chkPath)

            uploadPath = str(selUserID) + '/' + selFile.filename
            selFile.save(os.path.join(config.UPLOAD_FOLDER, uploadPath))
            newUpload = models.Upload(
                userid=selUserID,
                url=selFile.filename
            )

            db.session.add(newUpload)
            db.session.commit()
            db.session.refresh(newUpload)
            response = {'status': True, 'id': newUpload.id, 'url': uploadPath}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@monitor.route('/set_size', methods=['POST'])
@login_required
def set_size():
    postData = request.form.to_dict()
    elemID = postData.get('elemID')
    if check_null(elemID):
        postData.pop('elemID')
        selElem = models.MonitorElement.query.filter_by(id=elemID).first()
        selElem.sizeoptions = json.dumps(postData)
        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)
