import flask
from flask import request, jsonify
from flask import current_app
from flask_cors import CORS
import sys
import os
import csv
import subprocess
import json

app = flask.Flask(__name__)
CORS(app)
app.config["DEBUG"] = False
app.clients = {}
app.config["HOME_PATH"] = r'/home/david/Pigrow' 
home_path  = r'/home/david/Pigrow' 
# default return 
@app.route('/', methods=['GET'])
def home():
    return "<h1>Pigrow Mobile API</h1><p>This site is a prototype API for Pigrow monitoring.</p>"

def RunSubprocess(args):
    process = subprocess.run(args, 
                         stdout=subprocess.PIPE, 
                         universal_newlines=True)
    return process;

# A route to return all of the configured triggers.
@app.route('/api/v1/triggers/getalltriggers', methods=['GET'])
def api_GetCurrentTriggers():

    results = []
    with open(os.path.join(home_path, 'config/trigger_events.txt')) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader: # each row is a list
            results.append(row)
    
    triggers = []
    for line in results:
        trigg = {}
        trigg["log"] = line[0]
        trigg["valuelabel"] = line[1]
        trigg["type"] = line[2]
        trigg["value"] = line[3]
        trigg["conditionname"] = line[4]
        trigg["set"] = line[5]
        trigg["lock"] = line[6]
        trigg["cmd"] = line[7]
        triggers.append(trigg)
    
    return jsonify(triggers)

@app.route('/api/v1/triggers/gettrigger/<conditionname>', methods=['GET'])
def api_GetTrigger(conditionname):

    results = []
    with open(os.path.join(home_path, 'config/trigger_events.txt')) as csvfile:
        reader = csv.reader(csvfile) # change contents to floats
        for row in reader: # each row is a list
            results.append(row)
    
    for line in results:
        if line[4].lower() == conditionname.lower():
            trigg = {}
            trigg["log"] = line[0]
            trigg["valuelabel"] = line[1]
            trigg["type"] = line[2]
            trigg["value"] = line[3]
            trigg["conditionname"] = line[4]
            trigg["set"] = line[5]
            trigg["lock"] = line[6]
            trigg["cmd"] = line[7]
            break

    
    return jsonify(trigg)

@app.route('/api/v1/triggers/settrigger', methods=['POST'])
def api_SetTrigger():

    results = []
    if request.method == 'POST':
        log = request.form['log']
        valueLabel = request.form['valueLabel']
        typeVal = request.form['type']
        value = request.form['value']
        conditionname = request.form['conditionname']
        setVal = request.form['setVal']
        lock = request.form['lock']
        cmd = request.form['cmd']
    with open(os.path.join(home_path, 'config/trigger_events.txt')) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader: 
            results.append(row)
    with open(os.path.join(home_path, 'config/trigger_events.txt'), 'w') as outf:
        writer = csv.writer(outf)
    
    try:
        newline = True
        for line in results:
            if line[4] == conditionname:
                writer.writerow(log,valueLabel,type,value,conditionname,setVal,lock,cmd)
                newline = False
                break
            else:
                writer.writerow(line)
        writer.writerows(reader)
        if newline == True:
            writer.writerow(log,valueLabel,type,value,conditionname,setVal,lock,cmd)
        status_code = flask.Response(status=201)
    except:
        raise InvalidUsage('Write failed', status_code=410)
    
    return status_code

# A route to get specific book details per user
@app.route('/api/v1/config/getallsensors', methods=['GET'])
def api_GetCurrentSensors():
    sensorsFull = {}
    with open(os.path.join(home_path, 'config/pigrow_config.txt')) as f:
        lines = f.read().splitlines()
        for line in lines:
            if line.startswith('sensor_'):
                linetuple = line.split('_')
                if linetuple[1] not in sensorsFull:
                    sensorsFull[linetuple[1].lower()] = {linetuple[2].split('=')[0]:line.split('=')[1]}
                else:
                    sensorsFull[linetuple[1]][linetuple[2].split('=')[0]] =  line.split('=')[1]


    return jsonify(sensorsFull)

# A route to get specific book details per user
@app.route('/api/v1/config/getconfig', methods=['GET'])
def api_GetConfig():
    sensorsFull = {}
    config = {}
    with open(os.path.join(home_path, 'config/pigrow_config.txt')) as f:
        lines = f.read().splitlines()

        for line in lines:
            if line.startswith('sensor_'):
                linetuple = line.split('_')
                if linetuple[1] not in sensorsFull:
                    sensorsFull[linetuple[1]] = {linetuple[2].split('=')[0]:line.split('=')[1]}
                else:
                    sensorsFull[linetuple[1]][linetuple[2].split('=')[0]] =  line.split('=')[1]
            else:
                if line.startswith('gpio'):
                    linetuple = line.split('_',1)
                    if linetuple[0] not in config:
                        config[linetuple[0]] = {linetuple[1].split('=')[0]:line.split('=')[1]}
                    else:
                        config[linetuple[0]][linetuple[1].split('=')[0]] =  line.split('=')[1]
    config['sensors'] = sensorsFull;

    return jsonify(config)

# A route to get specific book details per user
@app.route('/api/v1/config/getgpio', methods=['GET'])
def api_GetGpio():
    gpioFull = {}
    with open(os.path.join(home_path, 'config/pigrow_config.txt')) as f:
        lines = f.read().splitlines()
    
        for line in lines:
            if line.startswith('gpio'):
                linetuple = line.split('_',1)
                if linetuple[0] not in gpioFull:
                    gpioFull[linetuple[0]] = {linetuple[1].split('=')[0]:line.split('=')[1]}
                else:
                    gpioFull[linetuple[0]][linetuple[1].split('=')[0]] =  line.split('=')[1]

    return jsonify(gpioFull)

@app.route('/api/v1/config/setgpio', methods=['POST'])
def api_SetGpio(relayName,direction):
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    gpios = json.load(api_GetGpio())
    gp = gpios["gpio"]
    gpio = gp[relayName]
    gpioPowerState = gp[relayName + '_on']
    args = ['echo', str(gpio) + '>' + '/sys/class/gpio/export']
    out = RunSubprocess(args)
    args = ['cat', '/sys/class/gpio/gpio' + str(gpio) + '/value']
    out = RunSubprocess(args)
    gpio_status = out.strip()
    gpio_err = out.strip()
    success = True
    if gpio_status == "1":
        if gpioPowerState == 'low':
            device_status = "OFF"
        elif gpioPowerState == 'high':
            device_status = 'ON'
        else:
            device_status = "settings error"
            success = False
    elif gpio_status == '0':
        if gpioPowerState == 'low':
            device_status = "ON"
        elif gpioPowerState == 'high':
            device_status = 'OFF'
        else:
            device_status = "setting error"
            success = False
    else:
        device_status = "read error -" + gpio_status + "-"
    if success:
        GPIO.setup(gpio, GPIO.OUT)    
        if device_status == "OFF" or direction.upper() == "OFF":
            if gpioPowerState == "low":
                GPIO.output(gpio, GPIO.LOW)
            elif gpioPowerState == "high":
                GPIO.output(gpio, GPIO.HIGH)
        elif device_status == "ON" or direction.upper() == "ON":
            if gpioPowerState == "low":
                GPIO.output(gpio, GPIO.HIGH)
            elif gpioPowerState == "high":
                GPIO.output(gpio, GPIO.LOW)
        
    return success

@app.route('/api/v1/data/getlog/<logname>', defaults={'logtype': None}, methods=['GET'])
@app.route('/api/v1/data/getlog/<logname>/<logtype>', methods=['GET'])
def api_GetLog(logname,logtype='modular'):
    
    sensorsText = api_GetCurrentSensors()
    sensors = json.loads(sensorsText.data)

    if logname.lower() in sensors:
        sensor = sensors[logname]
        logPath = sensor['log']

    logResults,error = ParseLog(logPath,logtype)
    if len(logResults) == 0:
        logResults.append({'error':error})
    return jsonify(logResults)


def ParseLog(logPath, type):
    
    logsResults = []
    with open(logPath) as f:
        lines = f.read().splitlines()
        error = "";
        for line in lines:
            linePart = line.split('>');
            obj = {}
            if type is not None and type.upper() == 'CHIRP':
                try:
                    obj['time'] = linePart[0]
                except IndexError:
                    error = 'noIndex'
                try:
                    obj['moisture'] = linePart[1]
                except IndexError:
                    error = 'noIndex'
                try:
                    obj['moistureperc'] = linePart[2]
                except IndexError:
                    error = 'noIndex'
                try:
                    obj['temperature'] = linePart[3]
                except IndexError:
                    error = 'noIndex'
                try:
                    obj['light'] = linePart[4]
                except IndexError:
                    error = 'noIndex'
            else:
                for part in linePart:
                    try:
                        split = part.split('=')
                        obj[split[0]] = split[1]
                    except:
                        error = 'incorrect type maybe, default is modular'
            
            if obj != {}:
                logsResults.append(obj)
    
    return logsResults,error


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


app.run(host= '0.0.0.0')


