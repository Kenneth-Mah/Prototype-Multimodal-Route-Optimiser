########  imports  ##########
from MSCFunction import *
from flask import Flask, json, request, render_template
import numpy as np
app = Flask(__name__)

def np_encoder(object):
    if isinstance(object, np.generic):
        return object.item()

#############################
# Additional code goes here #
#############################

@app.route('/')
def home_page():
    return render_template('index.html')

@app.route('/result', methods=['POST'])
def result():
    # cannot use request.form.to_dict() because it doesn't seem to work with checkbox list
    departure = request.form["departure"]
    arrival = request.form["arrival"]
    time = request.form["time"]

    # mode_raw is from a checkbox
    mode_raw = request.form.getlist("mode")
    mode = "M"
    if "Air" not in mode_raw:
        mode = "S"
    elif "Ocean" not in mode_raw:
        mode = "A"

    # opti_raw is from a radio
    opti_raw = request.form["opti"]
    opti_dict = {"Time":0, "Cost":1, "Carbon":2}
    opti = opti_dict[opti_raw]

    connect = request.form["connect"]

    form_data = {"departure": departure, "arrival": arrival, "time": time, "mode_raw": mode_raw, "opti_raw": opti_raw, "connect": connect}
    output = MSCModel(mode, departure, arrival, time, opti, connect)

    return render_template("main.html", form_data = form_data, json_output = json.dumps(output, default = np_encoder))

@app.route('/newresult', methods=['POST'])
def newresult():
    # cannot use request.form.to_dict() because it doesn't seem to work with checkbox list
    departure = request.form["departure"]
    arrival = request.form["arrival"]
    time = request.form["time"]

    # mode_raw is from a checkbox
    mode_raw = request.form["mode"].split(",")
    mode = "M"
    if "Air" not in mode_raw:
        mode = "S"
    elif "Ocean" not in mode_raw:
        mode = "A"

    # opti_raw is from a radio
    opti_raw = request.form["opti"]
    opti_dict = {"Time":0, "Cost":1, "Carbon":2}
    opti = opti_dict[opti_raw]

    connect = request.form["connect"]
    # data cleaning for customisers
    remove_ports = request.form["exclude_ports"].split(",")
    if remove_ports == ['']:
        remove_ports = []

    remove_trips = request.form["exclude_trips"].split(",")
    if remove_trips == ['']:
        remove_trips = []
    else:
        new_remove_trips = []
        for i in range(len(remove_trips)):
            if i % 4 == 0:
                one_trip = []
                one_trip.append(remove_trips[i])
            elif i % 4 == 3:
                one_trip.append(remove_trips[i])
                new_remove_trips.append(one_trip)
            else:
                one_trip.append(remove_trips[i])
        remove_trips = new_remove_trips

    new_constraints = request.form["new_constraints"].split(",")

    form_data = {"departure": departure, "arrival": arrival, "time": time, "mode_raw": mode_raw, "opti_raw": opti_raw, "connect": connect}
    output = MSCModel(mode, departure, arrival, time, opti, connect, 
        exclude_ports = remove_ports, exclude_trips = remove_trips, constraints = new_constraints)

    return render_template("main.html", form_data = form_data, json_output = json.dumps(output, default = np_encoder))

#########  run app  #########
app.run(debug=True)