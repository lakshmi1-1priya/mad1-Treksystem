#for the database
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db=SQLAlchemy()

class User(db.Model):
    """
    Single table for all three roles:admin,staff,user
    """
    __tablename__="users"

    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(120),nullable=False)
    email=db.Column(db.String(120),unique=True,nullable=False,index=True)
    password_hash=db.Column(db.String(255),nullable=False)
    phone=db.Column(db.String(120))
    role=db.Column(db.String(20),nullable=False,default="trekker") #admin/staff/ trekker

    #staff-approval
    is_approved=db.Column(db.Boolean, default=False) #adimn mst approve the staff
    is_blacklisted=db.Column(db.Boolean,default=False) # admin can blacklist user/staff
    created_at=db.Column(db.DateTime, default=datetime.utcnow)

    #relationships
    staff_profile=db.relationship(
        "StaffProfile",backref="user",uselist=False,cascade="all, delete-orphan"
    )
    preference=db.relationship(
        "UserPreference",backref="user",uselist=False,cascade="all, delete-orphan"
    )
    bookings=db.relationship(
        "Booking",backref="user",lazy=True,cascade="all, delete-orphan"
    )
    assigned_treks=db.relationship(
        "Trek",backref="assigned_staff",lazy=True,
        foreign_keys="Trek.assigned_staff_id"
    )

    def set_password(self, raw_password):
        self.password_hash=generate_password_hash(raw_password)
    def check_password(self,raw_password):
        return check_password_hash(self.password_hash,raw_password)
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"   
class StaffProfile(db.Model):
    """
    extra details for trek staff members
    """
    __tablename__="staff_profiles"
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id"),unique=True,nullable=False)
    contact_details=db.Column(db.String(255)) 
    experience_years=db.Column(db.Integer,default=0)
    status=db.Column(db.String(20),default="Pending") #Pending/Approved/Blacklisted 
    def __repr__(self):
        return f"<StaffProfile user_id={self.user_id}>"  
class UserPreference(db.Model):
    """
    Trekkers preferences,customized trek suggestions(1-1),tags are stored in ,-seperated string
    no extra tabel needed
    """
    __tablename__="user_preferences"
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id"),unique=True,nullable=False)
    preferred_difficulty=db.Column(db.String(20)) #Easy/Moderate/Hard
    preferred_location=db.Column(db.String(150))
    max_duration=db.Column(db.Integer) #in days
    interest_tags=db.Column(db.String(255)) #ex:waterfall,forest
    def __repr__(self):
        return f"<UserPreference user_id={self.user_id}>"
class Trek(db.Model):
    """
    trek details
    """
    __tablename__="treks" 

    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(150),nullable=False)
    location=db.Column(db.String(150),nullable=False)
    difficulty=db.Column(db.String(20),nullable=False)  #easy/medium/hard 
    duration=db.Column(db.Integer,nullable=False) #in days
    description=db.Column(db.Text)
    interest_tags=db.Column(db.String(255))
    total_slots=db.Column(db.Integer,nullable=False,default=0)
    available_slots=db.Column(db.Integer,nullable=False,default=0)
    assigned_staff_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=True)
    status=db.Column(
        db.String(20),nullable=False,default="Pending"
    ) #pending/Approved/open/closed/completed
    start_date=db.Column(db.Date)
    end_date=db.Column(db.Date)
    created_at=db.Column(db.DateTime,default=datetime.utcnow)
    bookings=db.relationship(
        "Booking", backref="trek",lazy=True,cascade="all, delete-orphan"
    )
    route_stops=db.relationship(
        "RouteStop",backref="trek",lazy=True,cascade="all, delete-orphan", order_by="RouteStop.order_index"
    )
    def __repr__(self):
        return f"<Trek {self.name} ({self.status})>"
class RouteStop(db.Model):
    """
    order stops:rest stop,safe zone,hangout,general checkpoint staff enters these when setting up the trek
    """    
    __tablename__="route_stops"

    id=db.Column(db.Integer,primary_key=True)
    trek_id=db.Column(db.Integer,db.ForeignKey("treks.id"), nullable=False)
    order_index=db.Column(db.Integer,nullable=False) #sequence along the route
    name=db.Column(db.String(50),nullable=False) #RestStop/Safe zone/hangout/checkpoint
    description=db.Column(db.Text)
    distance_from_start_km=db.Column(db.Float)
    category=db.Column(db.String(50),nullable=False)
    def __repr__(self):
        return f"<RouteStop {self.name} ({self.category}) trek_id={self.trek_id}>"
class Booking(db.Model):
    __tablename__="bookings"

    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False)
    trek_id=db.Column(db.Integer,db.ForeignKey("treks.id"),nullable=False)
    booking_date=db.Column(db.DateTime,default=datetime.utcnow) 
    status=db.Column(db.String(20),default="Booked") #Booked/Cancelled/Complete
    payment_status=db.Column(db.String(20),default="Pending") #Pending/Paid/Refunded
    def __repr__(self):
        return f"<Booking user={self.user_id} trek={self.trek_id} status={self.status}>"