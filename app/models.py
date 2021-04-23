from app import db, bcrypt
from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String)
    usertype = db.Column(db.String)
    _password = db.Column(db.String)
    accept = db.Column(db.Integer)
    setting = db.Column(db.Integer)

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, plaintext):
        self._password = bcrypt.generate_password_hash(plaintext)

    def check_password(self, plaintext):
        return bcrypt.check_password_hash(self.password, plaintext)


class Condition(db.Model, UserMixin):
    __tablename__ = 'conditions'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    type = db.Column(db.String)
    use_flag = db.Column(db.Integer)
    condgroup = db.Column(db.String)
    options = db.Column(db.Text)
    condoptions = db.Column(db.Text)
    ind = db.Column(db.String)


class ConditionGroup(db.Model, UserMixin):
    __tablename__ = 'condition_group'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    options = db.Column(db.Text)
    controlid = db.Column(db.String)
    operator = db.Column(db.String)
    reverse = db.Column(db.String)


class ActionGroup(db.Model, UserMixin):
    __tablename__ = 'action_group'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    options = db.Column(db.Text)
    controlid = db.Column(db.String)
    mode = db.Column(db.String)
    cnt = db.Column(db.String)


class Control(db.Model, UserMixin):
    __tablename__ = 'control'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    logicid = db.Column(db.String)
    options = db.Column(db.Text)
    use_flag = db.Column(db.String)
    priority = db.Column(db.String)
    mode = db.Column(db.String)
    ind = db.Column(db.String)


class Logic(db.Model, UserMixin):
    __tablename__ = 'logic'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    options = db.Column(db.Text)
    use_flag = db.Column(db.String)
    mode = db.Column(db.String)
    logicid = db.Column(db.String)


class ExecFunc(db.Model, UserMixin):
    __tablename__ = 'exec_func'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    group = db.Column(db.String)
    group_title = db.Column(db.String)
    name = db.Column(db.String)
    func_title = db.Column(db.String)
    desc = db.Column(db.Text)
    image = db.Column(db.String)


class FuncInput(db.Model, UserMixin):
    __tablename__ = 'func_input'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    func_name = db.Column(db.String)
    input = db.Column(db.String)
    input_desc = db.Column(db.String)
    data_type = db.Column(db.String)
    control = db.Column(db.String)
    combo_member = db.Column(db.String)
    default_value = db.Column(db.String)
    min_value = db.Column(db.String)
    max_value = db.Column(db.String)
    string_max_len = db.Column(db.String)


class FuncOutput(db.Model, UserMixin):
    __tablename__ = 'func_output'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    func_name = db.Column(db.String)
    output = db.Column(db.String)
    output_desc = db.Column(db.String)
    var_type = db.Column(db.String)


class Action(db.Model, UserMixin):
    __tablename__ = 'actions'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    use_flag = db.Column(db.String)
    order = db.Column(db.Integer)
    type = db.Column(db.String)
    actgroup = db.Column(db.String)
    options = db.Column(db.Text)
    actoptions = db.Column(db.Text)
    ind = db.Column(db.String)


class Permission(db.Model, UserMixin):
    __tablename__ = 'permissions'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    perm_item = db.Column(db.String)
    permission = db.Column(db.Integer)


class SettingInterval(db.Model, UserMixin):
    __tablename__ = 'set_interval'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    set_id = db.Column(db.Integer)
    set_name = db.Column(db.String)
    interval = db.Column(db.String)


class RecipeDef(db.Model, UserMixin):
    __tablename__ = 'recipe_def'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)


class RecipeVar(db.Model, UserMixin):
    __tablename__ = 'recipe_var'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    def_id = db.Column(db.Integer)
    order = db.Column(db.Integer)
    name = db.Column(db.String)
    type = db.Column(db.String)
    ind = db.Column(db.Integer)
    selid = db.Column(db.String)
    sellocstr = db.Column(db.String)


class RecipeValue(db.Model, UserMixin):
    __tablename__ = 'recipe_val'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    def_id = db.Column(db.Integer)
    var_id = db.Column(db.Integer)
    value = db.Column(db.String)
    ind = db.Column(db.Integer)
    options = db.Column(db.String)
    name_id = db.Column(db.String)


class RecipeName(db.Model, UserMixin):
    __tablename__ = 'recipe_name'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    def_id = db.Column(db.Integer)
    order = db.Column(db.Integer)
    name = db.Column(db.String)


class Alarm(db.Model, UserMixin):
    __tablename__ = 'alarms'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    type = db.Column(db.String)
    category = db.Column(db.String)
    confirm = db.Column(db.String)
    options = db.Column(db.Text)


class Variable(db.Model, UserMixin):
    __tablename__ = 'variable'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    remote = db.Column(db.Integer)
    name = db.Column(db.String)
    type = db.Column(db.String)
    ind = db.Column(db.String)
    use_flag = db.Column(db.String)
    defaults = db.Column(db.String)
    unit = db.Column(db.String)
    addr_id = db.Column(db.Integer)


class Monitor(db.Model, UserMixin):
    __tablename__ = 'monitors'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    options = db.Column(db.Text)
    back_img = db.Column(db.String)
    monitor_id = db.Column(db.String)


class MonitorElement(db.Model, UserMixin):
    __tablename__ = 'monitor_element'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    type = db.Column(db.String)
    monitorid = db.Column(db.String)
    options = db.Column(db.Text)
    ind = db.Column(db.String)
    elemoptions = db.Column(db.Text)
    sizeoptions = db.Column(db.String)


class DataCollect(db.Model, UserMixin):
    __tablename__ = 'data_collect'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    use_flag = db.Column(db.String)
    options = db.Column(db.Text)
    color = db.Column(db.String)
    type = db.Column(db.String)
    width = db.Column(db.String)


class Upload(db.Model, UserMixin):
    __tablename__ = 'uploads'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String)
    url = db.Column(db.Text)


class Modbus(db.Model, UserMixin):
    __tablename__ = 'modbus'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    use_flag = db.Column(db.String)
    type = db.Column(db.String)
    protocol = db.Column(db.String)
    options = db.Column(db.Text)


class ModbusChannel(db.Model, UserMixin):
    __tablename__ = 'modbus_channel'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    modbus_id = db.Column(db.String)
    options = db.Column(db.Text)


class ModbusVariable(db.Model, UserMixin):
    __tablename__ = 'modbus_variable'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.String)
    order = db.Column(db.String)
    selid = db.Column(db.String)
    seltype = db.Column(db.String)
    sellocstr = db.Column(db.String)


class CustomChannel(db.Model, UserMixin):
    __tablename__ = 'custom_channel'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    type = db.Column(db.String)
    options = db.Column(db.Text)


class CustomFrame(db.Model, UserMixin):
    __tablename__ = 'custom_frame'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)


class FrameSegment(db.Model, UserMixin):
    __tablename__ = 'frame_segment'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    frame_id = db.Column(db.String)
    type = db.Column(db.String)
    options = db.Column(db.Text)


class LocalServer(db.Model, UserMixin):
    __tablename__ = 'local_server'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    ip_addr = db.Column(db.String)
    port_addr = db.Column(db.String)
    use_flag = db.Column(db.String)


class RemoteClient(db.Model, UserMixin):
    __tablename__ = 'remote_client'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    use_flag = db.Column(db.String)
    name = db.Column(db.String)
    ip = db.Column(db.String)
    port = db.Column(db.String)
    remote_id = db.Column(db.Integer)


class EthercatDevice(db.Model, UserMixin):
    __tablename__ = 'ethercat_device'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String)
    parent_id = db.Column(db.String)


class Device(db.Model, UserMixin):
    __tablename__ = 'devices'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.String)
    vendor_name = db.Column(db.String)
    group_type = db.Column(db.String)
    group_name = db.Column(db.String)
    physics = db.Column(db.String)
    device_name = db.Column(db.String)
    revision = db.Column(db.String)
    type = db.Column(db.String)
    product_id = db.Column(db.String)
    module_ident = db.Column(db.String)
    slot_index = db.Column(db.String)
    slot_pdo = db.Column(db.String)
    min_instance = db.Column(db.String)
    max_instance = db.Column(db.String)
    module_class = db.Column(db.String)
    hide = db.Column(db.String)


class Settings(db.Model, UserMixin):
    __tablename__ = 'settings'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    value = db.Column(db.Text)
    userid = db.Column(db.Integer)

class CollectSet(db.Model, UserMixin):
    __tablename__ = 'collect_set'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    path = db.Column(db.String)
    interval = db.Column(db.String)
    interval_unit = db.Column(db.String)
    limit = db.Column(db.String)
    limit_val = db.Column(db.String)
    limit_unit = db.Column(db.String)


class Authority(db.Model, UserMixin):
    __tablename__ = 'authority'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String)
    menu = db.Column(db.String)
    read = db.Column(db.String)
    edit = db.Column(db.String)


class Timezone(db.Model, UserMixin):
    __tablename__ = 'timezone'
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    zone = db.Column(db.String)
