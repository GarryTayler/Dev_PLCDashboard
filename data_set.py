import json
import time
import sqlite3
from datetime import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy, make_url

from app import models
from app.config import DB_SAVE_PATH
from app.helper.LocalVar import SharedMem_LocalVar

intervalArr = {
    'SECOND': 1,
    'MINUTE': 60,
    'HOUR': 3600
}

data_set = Flask(__name__)
data_set.config['SECRET_KEY'] = 'plc-data-set-service'
data_set.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

dataSet = models.CollectSet.query.filter_by(name='data_set').first()
if dataSet and len(dataSet.path) > 0:
    sqlite3.connect(DB_SAVE_PATH + dataSet.path)
    data_set.config['SQLALCHEMY_DATABASE_URI'] = make_url('sqlite:///' + DB_SAVE_PATH + dataSet.path)
    selDB = SQLAlchemy(data_set)

    class VarLog(selDB.Model):
        __tablename__ = 'var_logs'
        __table_args__ = {'sqlite_autoincrement': True}

        id = selDB.Column(selDB.Integer, primary_key=True)
        var_id = selDB.Column(selDB.String)
        var_value = selDB.Column(selDB.String)
        createdAt = selDB.Column(selDB.String)

    selDB.create_all()


def save_val():
    if selDB:
        var_list = models.DataCollect.query.all()
        if len(var_list) > 0:
            for var in var_list:
                optionArr = json.loads(var.options) if len(var.options) > 0 else {}
                var_arr = optionArr['seltype'].split('-')
                type_arr = optionArr['selid'].split('-')
                local_shm = SharedMem_LocalVar(var_arr[0])
                data_list = local_shm.get_buff(type_arr[0], int(type_arr[1]), int(type_arr[1]) + 1, int(var_arr[1]))

                try:
                    newVal = VarLog(
                        var_id=var.id,
                        var_value=data_list[0]['val'],
                        createdAt=datetime.today().strftime('%Y-%m-%d %H:%M:%S')
                    )

                    selDB.session.add(newVal)
                    selDB.session.commit()
                except NameError:
                    print('Class not exists')


if dataSet:
    nextTime = time.time()
    while True:
        save_val()
        nextTime += intervalArr[dataSet.interval_unit] * int(dataSet.interval)
        sleepTime = nextTime - time.time()
        if sleepTime > 0:
            time.sleep(sleepTime)
