from flask import Flask, request
from app.helper.LocalVar import SharedMem_LocalVar
from flask_socketio import SocketIO, emit
from app import config


shm_socket = Flask(__name__)
shm_socket.config['SECRET_KEY'] = 'plc-dashboard'
socketio = SocketIO(shm_socket, cors_allowed_origins=config.CORS_ALLOW)


@socketio.on('joined')
def joined(message):
    print(request.sid)


@socketio.on('connect')
def connect():
    emit('connect', {'data': 'data'})


@socketio.on('disconnect')
def disconnect():
    print('disconnect')


@socketio.on('localvar')
def shm(data):
    var_arr = data['variable'].split('-')
    local_shm = SharedMem_LocalVar(var_arr[0])
    data_list = local_shm.get_buff(data['type'], data['start'], data['end'], int(var_arr[1]))
    emit('localvar', {'data_list': data_list, 'data': data}, room=request.sid, json=True)


if __name__ == '__main__':
    socketio.run(shm_socket, port=5500, host='0.0.0.0')
