import os

import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

from db import QUERIES

app = Flask(__name__)
CORS(app)


# GET REQUESTS
@app.route("/api/validate/<pw>", methods=["GET"])
def validate_password(pw):
    password = os.getenv("PASSWORD")
    return jsonify(pw == password)


@app.route("/api/events/all", methods=["GET"])
def get_all_events():
    return jsonify(QUERIES["ALL_EVENTS"]())


@app.route("/api/events/upcoming", methods=["GET"])
def get_upcoming_events():
    return jsonify(QUERIES["UPCOMING_EVENTS"]())


@app.route("/api/events/completed", methods=["GET"])
def completed_events():
    return jsonify(QUERIES["COMPLETED_EVENTS"]())


@app.route("/api/events/<int:event_id>", methods=["GET"])
def get_events(event_id):
    return jsonify(QUERIES["EVENT"](event_id))


@app.route("/api/events/<int:event_id>/sections/all/", methods=["GET"])
def get_all_sections(event_id):
    sections = [n["section_number"] for n in QUERIES["ALL_SECTIONS"](event_id)]
    return jsonify({"sections": sections})


@app.route("/api/events/<int:event_id>/riders/all/", methods=["GET"])
def get_all_riders(event_id):
    return jsonify(QUERIES["ALL_RIDERS"](event_id))


@app.route("/api/events/<int:event_id>/scores", methods=["GET"])
def get_scores(event_id):
    section_number = request.args.get("section_number")
    rider_number = request.args.get("rider_number")

    return jsonify(QUERIES["GET_SCORES"](event_id, section_number, rider_number))


# POST REQUESTS
@app.route("/api/score", methods=["POST"])
def post_score():
    data = request.get_json()
    event_id = data["event_id"]
    section_number = data["section_number"]
    rider_number = data["rider_number"]
    lap_number = data["lap_number"]
    score = data["score"]

    QUERIES["POST_SCORE"](event_id, section_number, rider_number, lap_number, score)

    return jsonify({"message": "Score added successfully"})


@app.route("/api/event/<int:event_id>", methods=["PUT"])
def complete_event(event_id):
    return jsonify(QUERIES["COMPLETE_EVENT"](event_id))


@app.route("/api/event/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    return jsonify(QUERIES["DELETE_EVENT"](event_id))


@app.route("/api/event", methods=["POST"])
def create_event():
    # Get the parameters
    event_name = request.form.get("event_name")
    event_location = request.form.get("event_location")
    event_date = request.form.get("event_date")
    sections = request.form.get("sections")
    lap_count = request.form.get("lap_count")

    # Validate the parameters
    try:
        sections = int(sections)
        lap_count = int(lap_count)
    except ValueError:
        return jsonify({"error": "Sections and laps must be integers"}), 400

    try:

        # Get the uploaded file
        file = request.files["file"]
        df = pd.read_excel(file, skiprows=2)

        # Check if variables are defined
        if (
            "NUMBER" not in df.columns
            or "NAME" not in df.columns
            or "CLASS" not in df.columns
        ):
            return jsonify({"error": "Invalid file format"}), 400
        # Create new event
        event_id = QUERIES["CREATE_EVENT"](
            event_name, event_location, event_date, lap_count
        )

        # add sections
        for i in range(1, sections + 1):
            QUERIES["CREATE_SECTION"](event_id, i)

        # helper function to get class id
        def getClass(kls):
            switcher = {"M": 1, "E": 2, "I": 3, "C": 4}
            return switcher.get(kls, "Unknown")

        # Create a dictionary to keep track of processed numbers
        processed_numbers = {}

        number = df["NUMBER"]
        name = df["NAME"]
        klass = df["CLASS"]

        # columns must be the same length
        if len(number) != len(name) or len(name) != len(klass):
            return jsonify({"error": "Invalid file format"}), 400

        insert_query = ""

        for Number, Name, Class in zip(number, name, klass):
            if pd.isnull(Number) or pd.isnull(Name) or pd.isnull(Class):
                continue
            if Number in processed_numbers:
                return (
                    jsonify(
                        {"error": f"Duplicate number {Number} for {Name}, {Class}"}
                    ),
                    400,
                )

            processed_numbers[Number] = True
            class_name = getClass(Class)
            insert_query += f"({event_id}, {int(Number)}, '{Name}', {class_name}),"
        insert_query = insert_query[:-1]

        # Insert riders
        QUERIES["CREATE_RIDERS"](insert_query)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Event created successfully"})


if __name__ == "__main__":
    app.run(debug=True)
