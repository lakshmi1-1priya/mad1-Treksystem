#Handling all teh URLS and linking 
from flask import Blueprint, render_template, redirect, url_for, flash,request,session
from models import db, User,StaffProfile, Trek, Booking
from decorators import login_required, roles_required
main_bp=Blueprint("main",__name__)
#helpers
def _current_user():
    uid=session.get("user_id")
    if not uid:
        return None
    return User.query.get(uid)

#main
@main_bp.route("/")
def index():
    return render_template("index.html")

#registration
@main_bp.route("/register/trekker",methods=["GET","POST"])
def register_trekker():
    if request.method=="POST":
        name=request.form.get("name","").strip()
        email=request.form.get("email","").strip().lower()
        phone=request.form.get("phone","").strip()
        password=request.form.get("password","")
        confirm=request.form.get("confirm_password","")

        if not name or not email or not password:
            flash("Name,email and password are required.", "danger")
            return redirect(url_for("main.register_trekker"))
        if password !=confirm:  
            flash("Password do not match.", "danger")
            return redirect(url_for("main.register_trekker"))
        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return redirect(url_for("main.register_trekker"))
        user=User(name=name, email=email,phone=phone,role="trekker",is_approved=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. You can now log in.", "success")
        return redirect(url_for("main.login"))
    return render_template("register_trekker.html")

@main_bp.route("/register/staff",methods=["GET","POST"])
def register_staff():
    if request.method=="POST":
        name=request.form.get("name","").strip()
        email=request.form.get("email","").strip().lower()
        phone=request.form.get("phone","").strip()
        experience_years=request.form.get("experience_years","0").strip()
        password=request.form.get("password","")
        confirm=request.form.get("confirm_password","")

        if not name or not email or not password:
            flash("Name,email and password are required.", "danger")
            return redirect(url_for("main.register_staff"))
        if password !=confirm:  
            flash("Password do not match.", "danger")
            return redirect(url_for("main.register_staff"))
        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return redirect(url_for("main.register_staff"))
        
        try:
            experience_years=int(experience_years)
        except ValueError:
            experience_years=0

        #staff must be approved  by admin
        user=User(name=name, email=email,phone=phone,role="staff",is_approved=False)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        profile=StaffProfile(
            user_id=user.id,
            contact_details=phone,
            experience_years=experience_years,
            status="Pending"
        )    
        db.session.add(profile)
        db.session.commit()

        flash("Registration submitted. Your account needs Admin approval before you can login","info")
        return redirect(url_for("main.login"))   
    return render_template("register_staff.html")


#login/logout
@main_bp.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("email","").strip().lower()
        password=request.form.get("password","")
        user=User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            flash("Invalid email or password.","danger")
            return redirect(url_for("main.login"))
        if user.is_blacklisted:
            flash("Your account has been blacklisted. Contact teh Admin.","danger")
            return redirect(url_for("main.login"))
        if user.role=="staff" and not user.is_approved:
            flash("Your staff account is awaiting Admin approval.","warning")
            return redirect(url_for("main.login"))
        session["user_id"]=user.id
        session["role"]=user.role
        session["name"]=user.name
        flash(f"Welcome back, {user.name}!", "success")
        return redirect(url_for("main.dashboard_redirect"))
    return render_template("login.html")

@main_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.login"))

#role-based dashboard
@main_bp.route("/dashboard")
@login_required
def dashboard_redirect():
    role=session.get("role")
    if role=="admin":
        return redirect(url_for("main.admin_dashboard"))
    if role=="staff":
        return redirect(url_for("main.staff_dashboard"))
    return redirect(url_for("main.trekker_dashboard"))

#admin dashboard
@main_bp.route("/admin/dashboard")
@roles_required("admin")
def admin_dashboard():
    total_treks=Trek.query.count()
    total_staff=User.query.filter_by(role="staff").count()
    total_users=User.query.filter_by(role="trekker").count()
    total_bookings=Booking.query.count()
    pending_staff=User.query.filter_by(role="staff", is_approved=False).count()
    return render_template(
        "dashboard_admin.html",
        total_treks=total_treks,
        total_staff=total_staff,
        total_users=total_users,
        total_bookings=total_bookings,
        pending_staff=pending_staff,
    )
#staff dashboard
@main_bp.route("/staff/dashboard")
@roles_required("staff")
def staff_dashboard():
    user=_current_user()
    assigned_treks=Trek.query.filter_by(assigned_staff_id=user.id).all()
    return render_template("dashboard_staff.html",assigned_treks=assigned_treks)

#trekker(user) dashboard
@main_bp.route("/user/dashboard")
@roles_required("trekker")
def trekker_dashboard():
    user=_current_user()
    bookings=Booking.query.filter_by(user_id=user.id).all()
    open_treks=Trek.query.filter_by(status="Open").all()
    return render_template("dashboard_user.html",bookings=bookings,open_treks=open_treks)





        


