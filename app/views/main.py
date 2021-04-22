from app import app, models
from flask import session, redirect, request
from datetime import datetime, timedelta
from app.helper.U2PMemory import U2p_Logic


def get_menu():
    pathArr = request.path.split('/')
    pathArr.pop(0)
    if pathArr[0] == "monitor":
        menu = "monitor-" + pathArr[2]
    elif pathArr[1] == "logic":
        menu = "logic-" + pathArr[2]
    else:
        menu = pathArr[1]

    return menu


@app.route('/')
@app.route('/index')
def index():
    if session.get('is_login'):
        return redirect('/user/home')
    else:
        return redirect('/user/login')


@app.context_processor
def current_time():
    selModel = models.Authority
    userID = session.get('user_id')
    auths = selModel.query.filter_by(userid=userID).with_entities(selModel.edit, selModel.menu, selModel.read).all() if userID is not None else []
    auth_list = [auth.menu for auth in auths if auth.edit == "0" and auth.read == "0"] if userID is not None else []

    edit_auth = False
    noExist = True
    curMenu = get_menu()
    for auth in auths:
        if auth.menu == curMenu:
            noExist = False
            edit_auth = True if auth.edit == "1" else False
            break

    if noExist and session.get('usertype') == "admin":
        edit_auth = True

    now = datetime.now()
    logicModel = models.Logic
    logic = logicModel.query.with_entities(logicModel.id, logicModel.name).all()
    selModel = models.Monitor
    monitors = selModel.query.with_entities(selModel.id, selModel.name, selModel.monitor_id).all()

    # u2p_shm = U2p_Logic()
    # mode = "run" if u2p_shm.get_run_mode() == 1 else "stop"
    selSet = models.Settings.query.filter_by(name='mode').first()
    mode = selSet.value

    userid=''
    if session and session.get('user_id'):
        userid = session['user_id']
    if userid:
        selSet = models.Settings.query.filter_by(name='control_name').filter_by(userid=userid).first()
        selName = selSet.value if selSet else ""
        selSet = models.Settings.query.filter_by(name='control_logo').filter_by(userid=userid).first()
        selLogo = selSet.value if selSet else ""
    else:
        selName = ""
        selLogo = ""
    
    selSet = models.Settings.query.filter_by(name='control_name').first()
    selName = selSet.value if selSet else ""
    selSet = models.Settings.query.filter_by(name='control_logo').first()
    selLogo = selSet.value if selSet else ""

    return {'current_date': now.strftime('%Y-%m-%d'), 'current_time': now.strftime('%H:%M:%S'), "logic_list": logic,
            'monitors': monitors, 'selmode': mode, 'auth_list': auth_list, 'edit_auth': edit_auth,
            'control_name': selName, 'control_logo': selLogo}


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=60)
