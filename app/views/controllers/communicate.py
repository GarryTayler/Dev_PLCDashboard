from flask import render_template, Blueprint, request
from app.views.controllers.user import login_required
from app import models, db, config
from sqlalchemy import cast, Integer
from app.helper.common import check_null, get_remotes, datatable_list, datatable_head, get_ethercat
from app.helper.const import uiSizeModbusMasterChannel, uiSizeUserDefComm, uiSizeUserDefCommFrame, uiSizeRemoteConn, \
    uiSizeModbus
from app.helper.RemoteDevice import RemoteDevice_Memory
from app.helper.ModbusMemory import Modbus_Memory
import json

communicate = Blueprint('communicate', __name__, url_prefix='/communicate')


@communicate.route('/ethercat')
@login_required
def ethercat():
    deviceModel = models.Device
    ethModel = models.EthercatDevice
    group_list = ethModel.query.outerjoin(deviceModel, ethModel.device_id == deviceModel.id).with_entities(
        ethModel.device_id, ethModel.id).add_columns(deviceModel.vendor_name).filter(ethModel.parent_id == '0').all()
    data_list = [{'vendor_name': group[2], 'id': group[1], 'device_id': group[0],
                  'devices': ethModel.query.outerjoin(deviceModel, ethModel.device_id == deviceModel.id).with_entities(
                      ethModel.id, ethModel.device_id).add_columns(deviceModel.vendor_name).filter(
                      ethModel.parent_id == group[0]).all()} for group in group_list]

    ethercat_use, ethercat_try = get_ethercat()
    return render_template('communicate/ethercat.html', group_list=data_list, ethercat_use=ethercat_use,
                           ethercat_try=ethercat_try)


@communicate.route('/remote')
@login_required
def remote():
    remote_limit = uiSizeRemoteConn
    local_ip = ''
    local_port = '5000'
    local_use = '0'
    selServer = models.LocalServer.query.first()
    if selServer:
        local_ip = selServer.ip_addr
        local_port = selServer.port_addr
        local_use = selServer.use_flag

    # rm_mem = RemoteDevice_Memory()
    # local_data = rm_mem.get_local_status()
    local_data = {}
    return render_template('communicate/remote.html', remote_limit=remote_limit, local_ip=local_ip, local_use=local_use,
                           local_port=local_port, remotes=get_remotes(), local_data=local_data)


@communicate.route('/custom')
@login_required
def custom():
    return render_template('communicate/custom.html', channel_limit=uiSizeUserDefComm,
                           frame_limit=uiSizeUserDefCommFrame)


@communicate.route('/modbus')
@login_required
def modbus():
    return render_template('communicate/modbus.html', channel_limit=uiSizeModbusMasterChannel,
                           modbus_limit=uiSizeModbus)


@communicate.route('/add_modbus', methods=['POST'])
@login_required
def add_modbus():
    postData = request.values
    use_flag = postData.get('use_flag')
    selID = postData.get('selid')
    if check_null(use_flag) and check_null(selID):
        if int(selID) > 0:
            selMod = models.Modbus.query.filter_by(id=selID).first()
            selMod.use_flag = use_flag
            selMod.type = postData.get('type')
            selMod.protocol = postData.get('protocol')
        else:
            newModbus = models.Modbus(
                use_flag=use_flag,
                type=postData.get('type'),
                protocol=postData.get('protocol'),
                options=""
            )
            db.session.add(newModbus)

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': 'Invalid request'}

    return json.dumps(response)


@communicate.route('/remove_modbus', methods=['POST'])
@login_required
def remove_modbus():
    postData = request.values
    selIDs = postData.get('selRow')
    if check_null(selIDs):
        selIDS = selIDs.split(",")
        selType = postData.get('selType')
        for selid in selIDS:
            if check_null(selType):
                if selType == "channel":
                    models.ModbusChannel.query.filter_by(id=selid).delete()
                elif selType == "custom":
                    models.CustomChannel.query.filter_by(id=selid).delete()
                elif selType == "frame":
                    models.CustomFrame.query.filter_by(id=selid).delete()
                elif selType == "remote":
                    models.RemoteClient.query.filter_by(id=selid).delete()
            else:
                models.Modbus.query.filter_by(id=selid).delete()

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


@communicate.route('/add_channel', methods=['POST'])
@login_required
def add_channel():
    postData = request.form.to_dict()
    modbusID = postData.get('modbusid')
    selID = postData.get('selid')
    if check_null(modbusID) and check_null(selID):
        postData.pop('selid')
        postData.pop('modbusid')
        if int(selID) > 0:
            selChl = models.ModbusChannel.query.filter_by(id=selID).first()
            selChl.options = json.dumps(postData)
        else:
            newChannel = models.ModbusChannel(
                modbus_id=modbusID,
                options=json.dumps(postData)
            )
            db.session.add(newChannel)

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


@communicate.route('/get_channel', methods=['POST'])
@login_required
def get_channel():
    postData = request.values
    draw, start, length, columnIndex, columnName, sortOrder = datatable_head(postData)

    selModbus = postData.get('selModbus')
    channels = models.ModbusChannel.query.filter_by(modbus_id=selModbus)
    totalCount = channels.count()

    channels = channels.offset(start).limit(length).all()
    data_list = []

    # mod_mem = Modbus_Memory()
    selModel = models.Modbus
    sel_ind = selModel.query.filter(selModel.id < selModbus).count()
    # modbus_chl = mod_mem.get_modbus_chl(sel_ind) modbus_chl[ind]
    ind = 0
    for channel in channels:
        optionArr = json.loads(channel.options)
        optionArr['id'] = channel.id
        optionArr['chl'] = "TRUE"
        optionArr['options'] = channel.options
        data_list.append(optionArr)

        ind += 1

    return json.dumps(datatable_list(data_list, totalCount, draw))


@communicate.route('/add_common', methods=['POST'])
@login_required
def add_common():
    postData = request.form.to_dict()
    modbusID = postData.get('modbusid')
    if check_null(modbusID):
        postData.pop('modbusid')
        selModbus = models.Modbus.query.filter_by(id=modbusID).first()
        if selModbus:
            selModbus.options = json.dumps(postData)
            db.session.commit()
            response = {'status': True}
        else:
            response = {'status': False, 'message': "Modbus not exists"}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


@communicate.route('/get_variable', methods=['POST'])
@login_required
def get_variable():
    postData = request.form.to_dict()
    channel_id = postData.get('channel_id')
    selType = postData.get('type')
    if check_null(channel_id) and check_null(selType):
        response = {}
        isValid = True
        if selType == "master":
            selModbus = models.ModbusChannel.query.filter_by(id=channel_id).first()
            if selModbus:
                optionVal = json.loads(selModbus.options)
                response['channel_code'] = int(optionVal['channel_code']) if 'channel_code' in optionVal else 0
                response['channel_readlen'] = int(optionVal['channel_readlen']) if 'channel_readlen' in optionVal else 0
                response['channel_writelen'] = int(
                    optionVal['channel_writelen']) if 'channel_writelen' in optionVal else 0
            else:
                isValid = False
        else:
            channel_id = "slave-" + channel_id

        if isValid:
            varModel = models.ModbusVariable
            selOrder = postData.get('order') if 'order' in postData else '1'
            variables = varModel.query.filter(varModel.channel_id == channel_id).filter(varModel.order == selOrder) \
                .order_by(cast(varModel.order, Integer)).all()

            response = {'status': True, 'data_list': [
                {'order': variable.order, 'selid': variable.selid, 'seltype': variable.seltype,
                 'sellocstr': variable.sellocstr} for variable in variables]}
        else:
            response = {'status': False, 'message': 'Channel not found'}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


@communicate.route('/add_custom_channel', methods=['POST'])
@login_required
def add_custom_channel():
    postData = request.values
    channelName = postData.get('channelName')
    channelType = postData.get('channelType')
    selID = postData.get('selid')
    if check_null(channelName) and check_null(channelType) and check_null(selID):
        if int(selID) > 0:
            selChl = models.CustomChannel.query.filter_by(id=selID).first()
            selChl.name = channelName
            selChl.type = channelType
        else:
            newChannel = models.CustomChannel(
                name=channelName,
                type=channelType,
                options=''
            )

            db.session.add(newChannel)
        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


@communicate.route('/update_custom', methods=['POST'])
@login_required
def update_custom():
    postData = request.form.to_dict()
    channel_id = postData.get('channel_id')
    if check_null(channel_id):
        selCustom = models.CustomChannel.query.filter_by(id=channel_id).first()
        if selCustom:
            postData.pop('channel_id')
            selCustom.options = json.dumps(postData)

            db.session.commit()
            response = {'status': True}
        else:
            response = {'status': False, 'message': 'Channel not found'}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


@communicate.route('/add_frame', methods=['POST'])
@login_required
def add_frame():
    postData = request.values
    frameName = postData.get('frameName')
    if check_null(frameName):
        newFrame = models.CustomFrame(
            name=frameName
        )

        db.session.add(newFrame)
        db.session.commit()

        response = {'status': True}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


def get_segment_desc(obj):
    returnStr = ''
    for key, val in obj.items():
        if 'selid' in key or 'seltype' in key or 'sellocstr' in key:
            continue
        elif key == 'segment_ascii':
            returnStr += ',True' if val == '1' else ',False'
        elif key == "segment_btype":
            returnStr += val.replace('_', ' ')
        else:
            returnStr += ", " if len(returnStr) > 0 else ""
            returnStr += val

    return returnStr


@communicate.route('/get_frame', methods=['POST'])
@login_required
def get_frame():
    postData = request.values
    frameID = postData.get('selFrame')
    if check_null(frameID):
        segments = models.FrameSegment.query.filter_by(frame_id=frameID).all()
        data_list = []
        for segment in segments:
            data = {
                'id': segment.id,
                'options': segment.options,
                'type': segment.type,
                'type_str': config.SEGMENT_TYPE[segment.type]
            }
            optObj = json.loads(segment.options) if len(segment.options) > 0 else {}
            data['desc'] = get_segment_desc(optObj)
            data_list.append(data)
        response = {'status': True, 'data': data_list}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


@communicate.route('/add_segment', methods=['POST'])
@login_required
def add_segment():
    postData = request.form.to_dict()
    frame_id = postData.get('frame_id')
    selType = postData.get('type')
    selID = postData.get('selid')
    if check_null(frame_id) and check_null(selType) and check_null(selID):
        postData.pop('frame_id')
        postData.pop('type')
        selModel = models.FrameSegment
        if int(selID) > 0:
            selSeg = selModel.query.filter_by(id=selID).first()
            if selSeg:
                selSeg.options = json.dumps(postData)
                db.session.commit()
                response = {'status': True}
            else:
                response = {'status': False, 'message': "Segment not found"}
        else:
            newSeg = selModel(
                type=selType,
                frame_id=frame_id,
                options=json.dumps(postData)
            )

            db.session.add(newSeg)
            db.session.commit()
            response = {'status': True}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


@communicate.route('/update_local', methods=['POST'])
@login_required
def update_local():
    postData = request.values
    local_ip = postData.get('ip_address')
    local_port = postData.get('port_addr')
    use_flag = postData.get('use_flag')
    if check_null(local_ip) and check_null(local_port):
        selModel = models.LocalServer
        selServer = selModel.query.first()
        if selServer:
            selServer.ip_addr = local_ip
            selServer.port_addr = local_port
            selServer.use_flag = use_flag
        else:
            newServer = selModel(
                ip_addr=local_ip,
                port_addr=local_port,
                use_flag=use_flag
            )

            db.session.add(newServer)

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


@communicate.route('/add_client', methods=['POST'])
@login_required
def add_client():
    postData = request.values
    client_id = postData.get('selid')
    if check_null(client_id):
        if int(client_id) > 0:
            selClient = models.RemoteClient.query.filter_by(id=client_id).first()
            selClient.use_flag = postData.get('use_flag')
            selClient.name = postData.get('client_name')
            selClient.ip = postData.get('client_ip')
            selClient.port = postData.get('client_port')
        else:
            newClient = models.RemoteClient(
                ip=postData.get('client_ip'),
                name=postData.get('client_name'),
                port=postData.get('client_port'),
                use_flag=postData.get('use_flag')
            )

            db.session.add(newClient)
        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


@communicate.route('/update_variable', methods=['POST'])
@login_required
def update_variable():
    postData = request.form.to_dict()
    selModel = models.Variable
    for key, val in postData.items():
        keyArr = key.split(';')
        addrVal = keyArr[1].split('-')
        if val == '0':
            selVar = selModel.query.filter_by(remote=keyArr[0]).filter_by(type=keyArr[1]).delete()
        else :
            selVar = selModel.query.filter_by(remote=keyArr[0]).filter_by(type=keyArr[1]).first()
            if selVar:
                selVar.use_flag = val
                selVar.addr_id = int(addrVal[1])
            else:
                newVar = selModel(
                    ind='',
                    name='',
                    unit='',
                    type=keyArr[1],
                    defaults='',
                    use_flag=val,
                    remote=keyArr[0],
                    addr_id=int(addrVal[1])
                )
                db.session.add(newVar)

    db.session.commit()
    return json.dumps({'status': True})


@communicate.route('/slave_list', methods=['POST'])
@login_required
def slave_list():
    postData = request.values
    deviceID = postData.get('deviceID')
    if check_null(deviceID):
        deviceModel = models.Device
        data_list = deviceModel.query.with_entities(deviceModel.id, deviceModel.vendor_name, deviceModel.group_name,
                                                    deviceModel.device_name, deviceModel.revision).filter_by(
            hide='FALSE')

        if int(deviceID) == 0:
            data_list = data_list.filter(deviceModel.type == 'DEVICE').filter(deviceModel.physics.ilike('%Y%')).all()
        else:
            selDevice = deviceModel.query.filter_by(id=deviceID).first()
            if selDevice and selDevice.type == "DEVICE" and 'K' in selDevice.physics:
                filter_list = deviceModel.query.filter_by(vendor_id=selDevice.vendor_id).filter(
                    deviceModel.id != selDevice.id).filter(deviceModel.type == "DEVICE").all()
                data_list = [item for item in filter_list if 'K' in item.physics and 'Y' not in item.physics]
            elif selDevice and selDevice.type == "DEVICE" and 'K' not in selDevice.physics and len(
                    selDevice.module_class) > 0:
                filter_list = deviceModel.query.filter_by(vendor_id=selDevice.vendor_id).filter(
                    deviceModel.id != selDevice.id).filter(deviceModel.type == "MODULE").all()
                data_list = [item for item in filter_list if
                             len(item.module_class) > 0 and item.module_class in selDevice.module_class]
            else:
                data_list = []

        selList = [{'id': data.id, 'vendor': data.vendor_name, 'group': data.group_name, 'device': data.device_name,
                    'revision': data.revision} for data in data_list]
        response = {'status': True, 'data_list': selList}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


@communicate.route('/channel_list', methods=['POST'])
def channel_list():
    draw, start, length, columnIndex, columnName, sortOrder = datatable_head(request.values)

    chlModel = models.CustomChannel
    data_list = chlModel.query
    totalCount = data_list.count()

    # if columnName == 'name':
    #     orderObj = chlModel.name.asc() if sortOrder == 'asc' else chlModel.name.desc()
    # elif columnName == 'type':
    #     orderObj = chlModel.type.asc() if sortOrder == 'asc' else chlModel.type.desc()
    # else:
    #     orderObj = chlModel.id.asc() if sortOrder == 'asc' else chlModel.id.desc()

    orderObj = chlModel.id.asc()
    data_list = data_list.order_by(orderObj).offset(start).limit(length).all()
    selList = [
        {'id': data_list[ind].id, 'ind': start + ind + 1, 'name': data_list[ind].name, 'type': data_list[ind].type,
         'options': data_list[ind].options} for ind in range(len(data_list))]

    return json.dumps(datatable_list(selList, totalCount, draw))


@communicate.route('/frame_list', methods=['POST'])
def frame_list():
    draw, start, length, columnIndex, columnName, sortOrder = datatable_head(request.values)

    chlModel = models.CustomFrame
    data_list = chlModel.query
    totalCount = data_list.count()

    # if columnName == 'name':
    #     orderObj = chlModel.name.asc() if sortOrder == 'asc' else chlModel.name.desc()
    # else:
    #     orderObj = chlModel.id.asc() if sortOrder == 'asc' else chlModel.id.desc()

    orderObj = chlModel.id.asc()
    data_list = data_list.order_by(orderObj).offset(start).limit(length).all()
    selList = [{'id': data_list[ind].id, 'ind': start + ind + 1, 'name': data_list[ind].name} for ind in
               range(len(data_list))]

    return json.dumps(datatable_list(selList, totalCount, draw))


def client_item(dataItem, ind, client_arr=None):
    if client_arr is None:
        client_arr = []
    client_item1 = client_arr[ind - 1] if len(client_arr) > 0 else {'con': 0, 'err': 0, 'status': ''}
    return {'id': dataItem.id, 'ind': ind, 'name': dataItem.name, 'client': client_item1, 'flag': dataItem.use_flag,
            'use_flag': config.USE_FLAG_KR[int(dataItem.use_flag)], 'ip': dataItem.ip, 'port': dataItem.port}


@communicate.route('/client_list', methods=['POST'])
@login_required
def client_list():
    draw, start, length, columnIndex, columnName, sortOrder = datatable_head(request.values)
    cliModel = models.RemoteClient
    data_list = cliModel.query
    totalCount = data_list.count()

    # if columnName == 'name':
    #     orderObj = cliModel.name.asc() if sortOrder == 'asc' else cliModel.name.desc()
    # else:
    #     orderObj = cliModel.id.asc() if sortOrder == 'asc' else cliModel.id.desc()

    orderObj = cliModel.id.asc()
    data_list = data_list.order_by(orderObj).offset(start).limit(length).all()
    # rm_mem = RemoteDevice_Memory()
    # client_arr = rm_mem.get_remote_clients()
    client_arr = []
    selList = [client_item(data_list[ind], start + ind + 1, client_arr) for ind in range(len(data_list))]

    return json.dumps(datatable_list(selList, totalCount, draw))


def modbus_item(modbus, ind):
    # mod_mem = Modbus_Memory()
    # shm_modbus = mod_mem.get_modbus(ind - 1) shm_modbus
    return {'id': modbus.id, 'ind': ind, 'type': config.MODBUS_TYPE[modbus.type], 'options': modbus.options,
            'protocol': config.MODBUS_PROTOCOL[modbus.protocol], 'use_flag': config.USE_FLAG_KR[int(modbus.use_flag)],
            'protocol1': modbus.protocol, 'mtype': modbus.type, 'modbus': "TRUE", 'flag': modbus.use_flag}


@communicate.route('/modbus_list', methods=['POST'])
@login_required
def modbus_list():
    draw, start, length, columnIndex, columnName, sortOrder = datatable_head(request.values)
    cliModel = models.Modbus
    data_list = cliModel.query
    totalCount = data_list.count()

    # if columnName == 'type':
    #     orderObj = cliModel.type.asc() if sortOrder == 'asc' else cliModel.type.desc()
    # elif columnName == 'protocol':
    #     orderObj = cliModel.protocol.asc() if sortOrder == 'asc' else cliModel.protocol.desc()
    # else:
    #     orderObj = cliModel.id.asc() if sortOrder == 'asc' else cliModel.id.desc()

    orderObj = cliModel.id.asc()
    data_list = data_list.order_by(orderObj).offset(start).limit(length).all()
    selList = [modbus_item(data_list[ind], start + ind + 1) for ind in range(len(data_list))]

    return json.dumps(datatable_list(selList, totalCount, draw))


@communicate.route('/add_slave', methods=['POST'])
@login_required
def add_slave():
    postData = request.values
    selIDs = postData.get('selIDs')
    parentID = postData.get('parentID')
    if check_null(selIDs) and check_null(parentID):
        for selID in selIDs.split(','):
            selModel = models.EthercatDevice
            selEth = selModel.query.filter_by(device_id=selID).filter(selModel.parent_id == parentID).first()
            if not selEth:
                newEth = selModel(
                    device_id=selID,
                    parent_id=parentID
                )
                db.session.add(newEth)

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


@communicate.route('/ethercat_detail', methods=['POST'])
@login_required
def ethercat_detail():
    postData = request.values
    selID = postData.get('selID')
    if check_null(selID) and int(selID) > 0:
        selModel = models.Device
        selDevice = selModel.query.filter_by(id=selID).with_entities(
            selModel.vendor_name, selModel.vendor_id, selModel.device_name, selModel.revision, selModel.product_id,
            selModel.module_ident).first()
        response = {'status': True, 'vendor': {'vendor_name': selDevice.vendor_name, 'vendor_id': selDevice.vendor_id,
                                               'device_name': selDevice.device_name, 'revision': selDevice.revision,
                                               'product_id': selDevice.product_id,
                                               'module_ident': selDevice.module_ident}}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)


@communicate.route('/update_ethercat', methods=['POST'])
@login_required
def update_ethercat():
    postData = request.values
    ethercat_val = postData.get('ethercat_val')
    ethercat_type = postData.get('ethercat_type')
    if check_null(ethercat_type) and check_null(ethercat_val):
        selModel = models.Settings
        selRow = selModel.query.filter_by(name=ethercat_type).first()
        if selRow:
            selRow.value = ethercat_val
        else:
            newRow = selModel(
                name=ethercat_type,
                value=ethercat_val
            )
            db.session.add(newRow)

        db.session.commit()
        response = {'status': True}
    else:
        response = {'status': False, 'message': "Invalid request"}

    return json.dumps(response)
