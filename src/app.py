import os

import pandas as pd
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), '.env'))
print(os.getcwd())

from db import QUERIES
import pandas as pd
from flask import make_response

app = Flask(__name__)
CORS(app)


# GET REQUESTS
# Load environment variables from .env file


@app.route("/api/validate/<pw>", methods=["GET"])
def validate_password(pw):
    password = os.getenv("APP_ROOT_PASSWORD")
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


@app.route("/api/template", methods=["GET"])
def get_template():
    try:
        path = os.path.join(app.static_folder, "riding_numbers_template.xlsx")
        excel_mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return send_file(path, mimetype=excel_mime_type, as_attachment=True)
    except Exception as e:
        print(e)
        return jsonify({"message": "File could not be served"})


@app.route("/api/results_summary/<int:event_id>", methods=["GET"])
def get_results_summary(event_id):
    return jsonify(QUERIES["GET_SCORES_SUMMARY_BY_EVENTID"](event_id))



@app.route("/api/results_summary/<int:event_id>/excel", methods=["GET"])
def get_results_summary_excel(event_id):
    column_names, rows = QUERIES["GET_SCORES_SUMMARY_BY_EVENTID_EXCEL"](event_id)

    # Create a DataFrame from the data
    df = pd.DataFrame(rows, columns=column_names)

    # Convert DataFrame to CSV
    csv_data = df.to_csv(index=False)

    # Create a response with the CSV data
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = "attachment; filename=results_summary.csv"
    response.headers["Content-Type"] = "text/csv"

    return response


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

@app.route("/api/score", methods=["PUT"])
def put_score():
    data = request.get_json()
    event_id = data["event_id"]
    section_number = data["section_number"]
    rider_number = data["rider_number"]
    lap_number = data["lap_number"]
    score = data["score"]

    QUERIES["UPDATE_SCORE"](event_id, section_number, rider_number, lap_number, score)

    return jsonify({"message": "Score updated successfully"})


@app.route("/api/event/<int:event_id>", methods=["PUT"])
def complete_event(event_id):
    return jsonify(QUERIES["COMPLETE_EVENT"](event_id))


@app.route("/api/event/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    return jsonify(QUERIES["DELETE_EVENT"](event_id))


# TODO: revert all changes if anything fails
@app.route("/api/event", methods=["POST"])
def create_event():
    # Get the parameters
    event_name = request.form.get("event_name")
    event_location = request.form.get("event_location")
    event_date = request.form.get("event_date")
    sections = request.form.get("sections")
    lap_count = request.form.get("lap_count")
    password = request.form.get("password")

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
        required_columns = ["NUMBER", "NAME", "CLASS"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            error_message = f"Missing columns: {', '.join(missing_columns)}"
            return jsonify({"error": error_message}), 400
        
        

        # helper function to get class id
        switcher = {"M": 1, "E": 2, "I": 3, "C": 4}
        
        def getClass(kls):
            return switcher.get(kls.upper(), "C")

    
        number = df["NUMBER"]
        name = df["NAME"]
        klass = df["CLASS"]

        # columns must be the same length
        if len(number) != len(name) or len(name) != len(klass):
            return jsonify({"error": "Entries cannot have empty columns"}), 400
        
    
        # Create a dictionary to keep track of processed numbers
        processed_numbers = {}

        for Number, Name, Class in zip(number, name, klass):
            if pd.isnull(Number) or pd.isnull(Name) or pd.isnull(Class):
                continue
            
            if Number in processed_numbers:
                return (
                    jsonify(
                        {"error": f"Duplicate number {int(Number)} for {Name}, {Class}"}
                    ),
                    400,
                )
            processed_numbers[Number] = True
                
        # Create new event
        event_id = QUERIES["CREATE_EVENT"](
            event_name, event_location, event_date, lap_count, password
        )

        # # add sections
        [QUERIES["CREATE_SECTION"](event_id, i) for i in range(1, sections + 1)]
        
        insert_query = ""
        
        for Number, Name, Class in zip(number, name, klass):
            if pd.isnull(Number) or pd.isnull(Name) or pd.isnull(Class):
                continue

            insert_query += f"({event_id}, {int(Number)}, '{Name}', {getClass(Class)}),"

        # Insert riders
        QUERIES["CREATE_RIDERS"](insert_query[:-1])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Event created successfully"})



@app.route("/api/event/<int:event_id>/validate/<password>", methods=["GET"])
def verify_event_password(event_id, password):
    return jsonify(True if QUERIES["VERIFY_EVENT_PASSWORD"](event_id, password) else False)

@app.route("/api/event/<int:event_id>/has_password", methods=["GET"])
def get_event_password(event_id):
    return jsonify(True if QUERIES["EVENT_HAS_PASSWORD"](event_id)[0]["password"] else False)

if __name__ == "__main__":
    app.run(debug=False, port=os.getenv("PORT", 5000))
