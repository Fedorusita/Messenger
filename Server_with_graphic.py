from flask import Flask, render_template, request
from flask_socketio import SocketIO, send
import sqlite3


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)


connected_users = {}


def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT
    )''')
    conn.commit()
    conn.close()


@socketio.on('connect')
def handle_connect():
    print("Клиент подключился!")
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('SELECT username, message FROM messages ORDER BY id DESC LIMIT 10')
    messages = c.fetchall()
    conn.close()


    for msg in messages:
        send({'username': msg[0], 'message': msg[1]}, broadcast=True)


@socketio.on('register')
def handle_register(data):
    username = data.get('username', 'Гость')
    connected_users[request.sid] = username
    print(f"{username} присоединился!")
    send({'message': f'{username} присоединился к чату!'}, broadcast=True)



@socketio.on('message')
def handle_message(data):
    username = connected_users.get(request.sid, 'Гость')
    message = data.get('message', '')

    print(f"{username}: {message}")


    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('INSERT INTO messages (username, message) VALUES (?, ?)', (username, message))
    conn.commit()
    conn.close()


    send({'username': username, 'message': message}, broadcast=True)



@socketio.on('disconnect')
def handle_disconnect():
    username = connected_users.pop(request.sid, 'Гость')  # Удаляем пользователя
    print(f"{username} отключился!")
    send({'message': f'{username} вышел из чата.'}, broadcast=True)



@socketio.on('clear_chat')
def handle_clear_chat():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('DELETE FROM messages')
    conn.commit()
    conn.close()


    send({'clear_chat': True}, broadcast=True)



@app.route('/')
def index():

    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('SELECT username, message FROM messages ORDER BY id DESC LIMIT 10')
    messages = c.fetchall()
    conn.close()


    return render_template('index.html', messages=messages)



if __name__ == '__main__':
    init_db()
    socketio.run(app, host='localhost', port=5000, allow_unsafe_werkzeug=True)
