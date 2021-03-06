"""

A small Test application to show how to use Flask-MQTT.

"""

import eventlet
import json
from flask import Flask, render_template
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy


eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET'] = 'my secret key'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MQTT_BROKER_URL'] = '1.tcp.ap.ngrok.io'
app.config['MQTT_BROKER_PORT'] = 22199
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False
app.config['MQTT_LAST_WILL_TOPIC'] = 'home/lastwill'
app.config['MQTT_LAST_WILL_MESSAGE'] = 'bye'
app.config['MQTT_LAST_WILL_QOS'] = 2
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://mqtt_test:123456@127.0.0.1/mqtt_test'

# Parameters for SSL enabled
# app.config['MQTT_BROKER_PORT'] = 8883
# app.config['MQTT_TLS_ENABLED'] = True
# app.config['MQTT_TLS_INSECURE'] = True
# app.config['MQTT_TLS_CA_CERTS'] = 'ca.crt'

mqtt = Mqtt(app)
socketio = SocketIO(app)
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)


class mqtt_data(db.Model):
    __tablename__ = 'mqtt_data'
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(64))
    message = db.Column(db.String(128))

    def __init__(self, topic, message):
        self.topic = topic
        self.message = message

    def __repr__(self):
        return '<mqtt_data %r>' % self.topic + ':' + self.message


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('publish')
def handle_publish(json_str):
    data = json.loads(json_str)
    mqtt.publish(data['topic'], data['message'])


@socketio.on('subscribe')
def handle_subscribe(json_str):
    data = json.loads(json_str)
    mqtt.subscribe(data['topic'])


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
    )
    d = mqtt_data(topic=data['topic'], message=data['payload'])
    db.session.add(d)
    db.session.commit()
    #print(d)
    p = message.payload.decode()
    json_acceptable_string = p.replace("'", "\"")
    p = json.loads(json_acceptable_string)
    print(p['temperature'])
    socketio.emit('mqtt_message', data=data)


@mqtt.on_log()
def handle_logging(client, userdata, level, buf):
    print(level, buf)


if __name__ == '__main__':
    db.create_all()
    socketio.run(app, host='0.0.0.0', port=5000, use_reloader=True, debug=True)
