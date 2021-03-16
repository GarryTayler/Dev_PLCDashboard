import logging

from app.config_common import *


# DEBUG can only be set to True in a development environment for security reasons
DEBUG = True
DEBUG_TB_INTERCEPT_REDIRECTS = False

# Secret key for generating tokens
SECRET_KEY = "plc-dashboard"
WTF_CSRF_TIME_LIMIT = 3600

# Admin credentials
ADMIN_CREDENTIALS = ("admin", "pa$$word")

# Database choice
SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
SQLALCHEMY_TRACK_MODIFICATIONS = True

# Configuration of a Gmail account for sending mails
MAIL_SERVER = "smtp.googlemail.com"
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = "flask.boilerplate"
MAIL_PASSWORD = "flaskboilerplate123"
ADMINS = ['flask.boilerplate@gmail.com']

# Number of times a password is hashed
BCRYPT_LOG_ROUNDS = 12

LOG_LEVEL = logging.DEBUG
LOG_FILENAME = "activity.log"
LOG_MAXBYTES = 1024
LOG_BACKUPS = 2

CONFIG_PATH = r'F:\work\khd\plc-dashboard\plc\app\helper'

V_DIGITAL = "DIGITAL"
V_ANALOG = "ANALOG"
V_STRING = "STRING"
V_SCHEDULE = "SCHEDULE"
V_PERIOD = "TIME_PERIOD"
V_CHANGE = "CHANGE"
V_CLOCK = "CLOCK"
V_REFER = "REFER_TO"
V_ALARM = "ALARM"
V_TIME = "TIME"
V_DATE = "DATE"
V_DELAY = "DELAY"
V_UCALC = "USER_CALC"
V_FUNC = "FUNCTION"
V_RECIPE = "RECIPE"
V_SHELLEXEC = "SHELL_EXEC"
V_CUSTOM = "USER_DEF_COMM"
V_GROUPACT = "ACT_GROUP"
V_CONTROL = "CONTROL"

USE_FLAG = {
    1: 'YES',
    0: 'NO'
}

USE_FLAG_KR = {
    1: '사용함',
    0: '사용안함'
}

VARIABLE_TYPE = {
    V_DIGITAL: '디지털',
    V_ANALOG: '아날로그',
    V_STRING: '문자열',
    V_SCHEDULE: '스케쥴',
    V_PERIOD: '시간구간',
    V_CHANGE: '변경감지',
    V_CLOCK: '시간주기',
    V_REFER: '다른조건',
    V_ALARM: '알람발생',
    V_TIME: '시간',
    V_DATE: '날짜',
    V_DELAY: '지연',
    V_UCALC: '사용자수식',
    V_FUNC: '함수실행',
    V_RECIPE: '레시피실행',
    V_SHELLEXEC: 'Shell명령실행',
    V_CUSTOM: "사용자정의통신",
    V_GROUPACT: "동작그룹 실행",
    V_CONTROL: "제어실행"
}

VARIABLE_DAY = {
    'DAY': '일',
    'WEEK': '주',
    'MONTH': '달',
    'YEAR': '년'
}

VARIABLE_SCHEDULE = {
    'NONE': '종료없음',
    'EXEC_NUM': '실행횟수'
}

ACTION_GROUP_MODE = {
    "SEQ": "순차제어모드",
    "SCAN": "스캔모드"
}

CONTROL_PANEL_MODE = {
    'NONE': '없음',
    'PRIORITY': '우선순위지정',
    'FIRST_ONLY': '선입우선',
    'LAST_ONLY': '후입우선'
}

ALARM_CONFIRM = {
    '0': '조건불만족',
    '1': '사용자확인시',
    '2': '조건불만족+사용자확인시'
}

ALARM_TYPE = {
    'DIGITAL': '디지털',
    'LOWER_LIMIT': '하한',
    'UPPER_LIMIT': '상한',
    'IN_RANGE': '범위안',
    'OUT_RANGE': '범위밖',
    'CHANGE': '변경감지'
}

ALARM_CATEGORY = {
    'info': '로그',
    'warn': '경고',
    'error': '에러'
}

VARIABLE_WEEK = {
    '0': '일',
    '1': '월',
    '2': '화',
    '3': '수',
    '4': '목',
    '5': '금',
    '6': '토'
}

SHELL_DUPLICATE = {
    'KILL_PREV_PROCESS': '이전프로세스 종료',
    'NO_START_IF_EXIST': '중복실행안함'
}

VARIABLE_MATCH = {
    'digital': 'DG',
    'analog': 'AN',
    'string': 'ST',
    'date': 'DT',
    'time': 'TM'
}

UPLOAD_FOLDER = "F:/kcg_data/wsk/PLC/dev_plc_src/app/static/upload/"

MODBUS_TYPE = {
    'MASTER': 'Master',
    'SLAVE': 'Slave'
}

MODBUS_PROTOCOL = {
    'TCP': 'Modbus TCP',
    'RTU': 'Modbus RTU'
}

SEGMENT_TYPE = {
    '<H>': '상수(HEX)',
    '<S>': '문자열',
    '<V>': '변수 입력',
    '<B>': 'BCC 입력',
}

LOGIC_MODE = {
    'NONE': '없음',
    'PRIORITY': '우선순위지정',
    'FIRST_ONLY': '선입우선',
    'LAST_ONLY': '후입우선'
}

USER_TYPE = {
    'admin': '관리자',
    'user': '유저'
}

INTERVAL_LIST = [
    'General',
    'Alarm',
    'EtherCAT',
    'Logic',
    'Modbus',
    'Remote_Device',
    'Shared_Memory'
]

CORS_ALLOW = "http://localhost:5000"
DB_SAVE_PATH = r"F:/kcg_data/wsk/PLC/sql/"
