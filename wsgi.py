from app import app
import os

if __name__ == "__main__":
    app.run(debug = not not os.getenv("DEBUG"), port=os.getenv("PORT", 5000))
