#starts the flask app
from flask import Flask
from config import Config
from models import db, User

def create_admin():
    """
    ensures only one pre existing user(no admin self registration)
    """
    admin=User.query.filter_by(role="admin").first()
    if admin is None:
        admin=User(
            name=Config.ADMIN_NAME,
            email=Config.ADMIN_EMAIL,
            role="admin",
            is_approved=True,
        )
        admin.set_password(Config.ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()
        print(f"[seed] Admin created -> {Config.ADMIN_EMAIL}/{Config.ADMIN_PASSWORD}")
    else:
        print("[seed] Admin already exists,skipping")
def create_app():
    app=Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    from routes import main_bp
    app.register_blueprint(main_bp)
    with app.app_context():
        db.create_all()   #table creation
        create_admin() #programmatic admin seeding
    return app 
if __name__=="__main__":
    app=create_app()
    app.run(debug=True)

           
