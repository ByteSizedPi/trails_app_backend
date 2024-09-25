from app import app
import os
from app import app
import os

if __name__ == "__main__":
    env = ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME", "APP_ROOT_PASSWORD", "DEBUG", "PORT"]
    
    with open("output.txt", "w") as file:
        for var in env:
            file.write(f"{var}: {os.getenv(var)}\n")
    
    app.run(debug=not not os.getenv("DEBUG"), port=os.getenv("PORT", 5000))
