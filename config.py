#its like storing the setting of the current app
import os
BASE_DIR=os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY=os.environ.get("SECRET_KEY","dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI=os.environ.get(
        "DATABASE_URL",f"sqlite:///{os.path.join(BASE_DIR,'trekking.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS=False

    #pre-created admin
    ADMIN_EMAIL="admin@trekking.com"
    ADMIN_PASSWORD="Admin@123"
    ADMIN_NAME="System Admin"