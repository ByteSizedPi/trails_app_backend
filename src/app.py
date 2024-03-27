from flask import Flask

from config.db import get_connection

app = Flask(__name__)


@app.route("/api/events", methods=["GET"])
def get_events():
    pass


if __name__ == "__main__":
    app.run(debug=True)
