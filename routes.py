#Handling all teh URLS and linking 
from flask import Blueprint, render_template, redirect, url_for, flash,request,session
from models import db, User,StaffProfile, Trek, Booking
from decorators import login_required, roles_required
from datetime import datetime
main_bp=Blueprint("main",__name__)
#helpers
def _current_user():
    uid=session.get("user_id")
    if not uid:
        return None
    return User.query.get(uid)
def _parse_date(value):
    """Converts an HTML date input string ('YYYY-MM-DD') to a date object, or None."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None
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
#admin-trekmanagement-create edit delete list assign staff
@main_bp.route("/admin/treks")
@roles_required("admin")
def admin_treks():
    treks=Trek.query.order_by(Trek.created_at.desc()).all()
    return render_template("admin_treks.html",treks=treks)
@main_bp.route("/admin/treks/new",methods=["GET","POST"])
@roles_required("admin")
def admin_trek_new():
    approved_staff=User.query.filter_by(role="staff", is_approved=True,is_blacklisted=False).all()
    if request.method=="POST":
        name=request.form.get("name","").strip()
        location=request.form.get("location","").strip()
        difficulty=request.form.get("difficulty","Easy")
        duration=request.form.get("duration","1")
        description=request.form.get("description","").strip()
        total_slots=request.form.get("total_slots","0")
        assigned_staff_id=request.form.get("assigned_staff_id","") or None
        status=request.form.get("status","Pending")
        start_date=_parse_date(request.form.get("start_date"))
        end_date=_parse_date(request.form.get("end_date"))
        if not name or not location:
            flash("Trek name and location are required.", "danger")
            return redirect(url_for("main.admin_trek_new"))
        
        try:
            duration=int(duration)
            total_slots=int(total_slots)
        except ValueError:
            flash("Duration and slots must be numbers.", "danger")
            return redirect(url_for("main.admin_trek_new"))

        trek=Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            duration=duration,
            description=description,
            total_slots=total_slots,
            available_slots=total_slots,
            assigned_staff_id=int(assigned_staff_id) if assigned_staff_id else None,
            status=status,
            start_date=start_date,
            end_date=end_date,
        )  
        db.session.add(trek)
        db.session.commit()

        flash(f"Trek '{trek.name}' created successfully.","success")
        return redirect(url_for("main.admin_treks"))

    return render_template("admin_trek_form.html",trek=None, approved_staff=approved_staff)

@main_bp.route("/admin/treks/<int:trek_id>/edit",methods=["GET","POST"])
@roles_required("admin")
def admin_trek_edit(trek_id):
    trek=Trek.query.get_or_404(trek_id)
    approved_staff=User.query.filter_by(role="staff",is_approved=True,is_blacklisted=False).all()

    if request.method=="POST":
        name=request.form.get("name","").strip()
        location=request.form.get("location","").strip()
        difficulty=request.form.get("difficulty","Easy")
        duration=request.form.get("duration","1")
        description=request.form.get("description","").strip()
        total_slots=request.form.get("total_slots","0")
        assigned_staff_id=request.form.get("assigned_staff_id","") or None
        status=request.form.get("status","Pending")
        start_date=_parse_date(request.form.get("start_date"))
        end_date=_parse_date(request.form.get("end_date"))

        if not name or not location:
            flash("Trek name and location are required.", "danger")
            return redirect(url_for("main.admin_trek_edit",trek_id=trek_id))
        
        try:
            duration=int(duration)
            new_total_slots=int(total_slots)
        except ValueError:
            flash("Duration and slots must be numbers.", "danger")
            return redirect(url_for("main.admin_trek_edit",trek_id=trek_id))
        
        #keeping available slots consistent when admin changes total-slots
        slots_diff=new_total_slots-trek.total_slots
        trek.available_slots=max(0,trek.available_slots+slots_diff)
        trek.total_slots=new_total_slots

        trek.name=name
        trek.location=location
        trek.difficulty=difficulty
        trek.duration=duration
        trek.description=description
        trek.assigned_staff_id=int(assigned_staff_id) if assigned_staff_id else None
        trek.status=status
        trek.start_date=start_date
        trek.end_date=end_date
        db.session.commit()
        flash(f"Trek '{trek.name}' updated successfully.","success")
        return redirect(url_for("main.admin_treks"))
    
    return render_template("admin_trek_form.html",trek=trek, approved_staff=approved_staff)

@main_bp.route("/admin/treks/<int:trek_id>/delete",methods=["POST"])
@roles_required("admin")
def admin_trek_delete(trek_id):
    trek=Trek.query.get_or_404(trek_id)
    name=trek.name
    db.session.delete(trek)
    db.session.commit()
    flash(f"Trek '{name}' has been removed.","info")
    return redirect(url_for("main.admin_treks"))


#admin-staff management(approve,blacklist,reactivate,remove)
@main_bp.route("/admin/staff")
@roles_required("admin")
def admin_staff():
    staff_list=User.query.filter_by(role="staff").order_by(User.created_at.desc()).all()
    return render_template("admin_staff.html",staff_list=staff_list)
@main_bp.route("/admin/staff/<int:user_id>/approve",methods=["POST"])
@roles_required("admin")
def admin_staff_approve(user_id):
    staff=User.query.filter_by(id=user_id,role="staff").first_or_404()
    staff.is_approved=True
    if staff.staff_profile:
        staff.staff_profile.status="Approved"
    db.session.commit()
    flash(f"{staff.name} has been approved and can now log in","success")
    return redirect(url_for("main.admin_staff"))

@main_bp.route("/admin/staff/<int:user_id>/blacklist",methods=["POST"])
@roles_required("admin")
def admin_staff_blacklist(user_id):
    staff=User.query.filter_by(id=user_id,role="staff").first_or_404()
    staff.is_blacklisted=True
    if staff.staff_profile:
        staff.staff_profile.status="Blacklisted"
    db.session.commit()
    flash(f"{staff.name} has been blacklisted and cannot log in till admin decides","warning")
    return redirect(url_for("main.admin_staff"))

@main_bp.route("/admin/staff/<int:user_id>/reactivate",methods=["POST"])
@roles_required("admin")
def admin_staff_reactivate(user_id):
    staff=User.query.filter_by(id=user_id,role="staff").first_or_404()
    staff.is_blacklisted=False
    if staff.staff_profile:
        staff.staff_profile.status = "Approved" if staff.is_approved else "Pending"
    db.session.commit()
    flash(f"{staff.name} has been Reactivated and can log in","success")
    return redirect(url_for("main.admin_staff"))

@main_bp.route("/admin/staff/<int:user_id>/remove", methods=["POST"])
@roles_required("admin")
def admin_staff_remove(user_id):
    staff=User.query.filter_by(id=user_id,role="staff").first_or_404()
    name=staff.name
    #unassign the task before removing if he is having any 
    Trek.query.filter_by(assigned_staff_id=staff.id).update({"assigned_staff_id":None})
    db.session.delete(staff)
    db.session.commit()
    flash(f"Staff member '{name}' has been removed.", "info")
    return redirect(url_for("main.admin_staff"))

#admin-trekker(user management)

@main_bp.route("/admin/users")
@roles_required("admin")
def admin_users():
    users_list=User.query.filter_by(role="trekker").order_by(User.created_at.desc()).all()
    return render_template("admin_users.html",users_list=users_list)

@main_bp.route("/admin/users/<int:user_id>/blacklist",methods=["POST"])
@roles_required("admin")
def admin_user_blacklist(user_id):
    trekker=User.query.filter_by(id=user_id,role="trekker").first_or_404()
    trekker.is_blacklisted=True
    db.session.commit()
    flash(f"{trekker.name} has been blacklisted.","warning")
    return redirect(url_for("main.admin_users"))

@main_bp.route("/admin/users/<int:user_id>/reactivate",methods=["POST"])
@roles_required("admin")
def admin_user_reactivate(user_id):
    trekker=User.query.filter_by(id=user_id,role="trekker").first_or_404()
    trekker.is_blacklisted=False
    db.session.commit()
    flash(f"{trekker.name} has been Reactivated","success")
    return redirect(url_for("main.admin_users"))

#admin-search(treks,staff,users by name or id)

@main_bp.route("/admin/search")
@roles_required("admin")
def admin_search():
    query=request.args.get("q", "").strip()
    category=request.args.get("category","treks")
    trek_results,staff_results,user_results=[],[],[]

    if query:
        is_numeric=query.isdigit()
        if category=="treks":
            q=Trek.query
            if is_numeric:
                trek_results=q.filter(Trek.id==int(query)).all()
            else:
                trek_results=q.filter(Trek.name.ilike(f"%{query}%")).all()
        elif category=="staff":
            q=User.query.filter_by(role="staff")
            if is_numeric:
                staff_results=q.filter(User.id==int(query)).all()
            else:
                staff_results=q.filter(User.name.ilike(f"%{query}%")).all()
        elif category=="users":
            q=User.query.filter_by(role="trekker")
            if is_numeric:
                user_results=q.filter(User.id==int(query)).all()
            else:
                user_results=q.filter(User.name.ilike(f"%{query}%")).all()        
    return render_template(
        "admin_search.html",
        query=query,
        category=category,
        trek_results=trek_results,
        staff_results=staff_results,
        user_results=user_results,
    )

#admin-can view bookings and full trekking history
@main_bp.route("/admin/bookings")
@roles_required("admin")
def admin_bookings():
    bookings=Booking.query.order_by(Booking.booking_date.desc()).all()
    return render_template("admin_bookings.html",bookings=bookings)
#staff-helpers
STAFF_STATUS_OPTIONS=["Open","Closed","Ongoing","Completed"]

def _assigned_trek_or_none(trek_id,staff_id):
    "Fetch a trek only if it is assigned to this staff member,else None"
    return Trek.query.filter_by(id=trek_id,assigned_staff_id=staff_id).first()
#staff dashboard
@main_bp.route("/staff/dashboard")
@roles_required("staff")
def staff_dashboard():
    user=_current_user()
    assigned_treks=Trek.query.filter_by(assigned_staff_id=user.id).all()
    #registered trekker(users) count per trek, searched by trek id
    trekker_counts={}
    for trek in assigned_treks:
        trekker_counts[trek.id]=Booking.query.filter_by(
            trek_id=trek.id,status="Booked"
        ).count()
    return render_template(
        "dashboard_staff.html",
        assigned_treks=assigned_treks,
        trekker_counts=trekker_counts,
        )
#staff profile
@main_bp.route("/staff/profile",methods=["GET","POST"])
@roles_required("staff")
def staff_profile():
    user=_current_user()
    if(request.method=="POST"):
        name=request.form.get("name","").strip()
        phone=request.form.get("phone","").strip()
        experience_years=request.form.get("experience_years","0").strip()

        if not name:
            flash("Name is required.","danger")
            return redirect(url_for("main.staff_profile"))
        
        try:
            experience_years=int(experience_years)
        except ValueError:
            experience_years=0
        user.name=name
        user.phone=phone
        session["name"]=name  #navbar greeting in sync

        if user.staff_profile:
            user.staff_profile.contact_details=phone   
            user.staff_profile.experience_years=experience_years

        new_password=request.form.get("new_password","")
        confirm_password=request.form.get("confirm_password","")
        if new_password:
            if new_password!=confirm_password:
                flash("New password do not match. Other changes were not saved","danger")
                return redirect(url_for("main.staff_profile"))
            user.set_password(new_password)
        db.session.commit()
        flash("Profile updated successfully","success")
        return redirect(url_for("main.staff_profile"))
    return render_template("staff_profile.html",user=user)

#staff-assigned trek details and management

@main_bp.route("/staff/treks/<int:trek_id>")
@roles_required("staff")
def staff_trek_detail(trek_id):
    user=_current_user()
    trek=_assigned_trek_or_none(trek_id,user.id)
    if trek is None:
        flash("That trek is not assigned to you","danger")
        return redirect(url_for("main.staff_dashboard"))
    bookings=Booking.query.filter_by(trek_id=trek.id).order_by(Booking.booking_date.desc()).all()
    return render_template(
        "staff_trek_detail.html",
        trek=trek,
        bookings=bookings,
        status_options=STAFF_STATUS_OPTIONS,
    )
#to update trek details
@main_bp.route("/staff/treks/<int:trek_id>/update",methods=["POST"])
@roles_required("staff")
def staff_trek_update(trek_id):
    user=_current_user()
    trek=_assigned_trek_or_none(trek_id,user.id)
    if trek is None:
        flash("That trek is not assigned to you.","danger")
        return redirect(url_for("main.staff_dashboard"))
    available_slots=request.form.get("available_slots","").strip()
    status=request.form.get("status",trek.status)
    try:
        available_slots=int(available_slots)
    except ValueError:
        flash("Available slots must be a number","danger")
        return redirect(url_for("main.staff_trek_detail",trek_id=trek.id))
    if available_slots<0 or available_slots>trek.total_slots:
        flash(f"Available slots must be between 0 and {trek.total_slots}.","danger")
        return redirect(url_for("main.staff_trek_detail",trek_id=trek.id))
    if status not in STAFF_STATUS_OPTIONS:
        flash("Invalid status selected","danger")
        return redirect(url_for("main.staff_trek_detail",trek_id=trek.id))
    trek.available_slots=available_slots
    trek.status=status
    db.session.commit()

    flash(f"Trek '{trek.name}' updated: slot={available_slots}, status={status}.","success")
    return redirect(url_for("main.staff_trek_detail",trek_id=trek.id)) 

@main_bp.route("/staff/trek/<int:trek_id>/bookings/<int:booking_id>/complete",methods=["POST"])
@roles_required("staff")
def staff_booking_complete(trek_id,booking_id):
    user=_current_user()
    trek=_assigned_trek_or_none(trek_id,user.id)
    if trek is None:
        flash("That trek is not assigned to you.","danger")
        return redirect(url_for("main.staff_dashboard"))
    booking=Booking.query.filter_by(id=booking_id,trek_id=trek.id).first_or_404()
    booking.status="Completed"
    db.session.commit()
    flash(f"Marked {booking.user.name}'s booking as completed.","success")
    return redirect(url_for("main.staff_trek_detail",trek_id=trek.id))

#payment_status
@main_bp.route("/staff/trek/<int:trek_id>/bookings/<int:booking_id>/mark_paid",methods=["POST"])
@roles_required("staff")
def staff_booking_mark_paid(trek_id,booking_id):
    user=_current_user()
    trek=_assigned_trek_or_none(trek_id,user.id)
    if trek is None:
        flash("That trek is not assigned to you.","danger")
        return redirect(url_for("main.staff_dashboard"))
    booking=Booking.query.filter_by(id=booking_id,trek_id=trek.id).first_or_404()
    booking.payment_status="Paid"
    db.session.commit()
    flash(f"Marked {booking.user.name}'s payment as Paid.","success")
    return redirect(url_for("main.staff_trek_detail",trek_id=trek.id))


#trekker(user) dashboard,profile,browse/search, booking
@main_bp.route("/user/dashboard")
@roles_required("trekker")
def trekker_dashboard():
    user=_current_user()
    bookings=Booking.query.filter_by(user_id=user.id).all()
    open_treks=Trek.query.filter_by(status="Open").order_by(Trek.created_at.desc()).limit(6).all()
    return render_template("dashboard_user.html",bookings=bookings,open_treks=open_treks)

@main_bp.route("/user/profile",methods=["GET","POST"])
@roles_required("trekker")
def trekker_profile():
    user=_current_user()

    if request.method=="POST":
        name=request.form.get("name","").strip()
        phone=request.form.get("phone","").strip()
        if not name:
            flash("Name is required","danger")
            return redirect(url_for("main.trekker_profile"))
        user.name=name
        user.phone=phone
        session["name"]=name #keep navbar greeting in sequence
        new_password=request.form.get("new_password","")
        confirm_password=request.form.get("confirm_password","")
        if new_password:
            if new_password!=confirm_password:
                flash("New password do not  match.Other changes not saved.","danger")
                return redirect(url_for("main.trekker_profile"))
            user.set_password(new_password)
        db.session.commit()
        flash("Profile updated successfully.","success")
        return redirect(url_for("main.trekker_profile"))
    return render_template("user_profile.html",user=user)

@main_bp.route("/user/treks")
@roles_required("trekker")
def trekker_treks():
    """Browse open treks with filters by difficulty  and location"""
    location=request.args.get("location","").strip()
    difficulty=request.args.get("difficulty","").strip()

    query=Trek.query.filter_by(status="Open")

    if location:
        query=query.filter(Trek.location.ilike(f"%{location}%")) 
    if difficulty:
        query=query.filter(Trek.difficulty==difficulty)
    treks=query.order_by(Trek.start_date.asc().nullslast()).all()

    user=_current_user()
    #ids of trek this trekker already has an active booking
    booked_trek_ids={
        b.trek_id
        for b in Booking.query.filter_by(user_id=user.id,status="Booked").all()
    }
    return render_template(
        "user_treks.html",
        treks=treks,
        location=location,
        difficulty=difficulty,
        booked_trek_ids=booked_trek_ids,
    )


@main_bp.route("/user/treks/<int:trek_id>/book",methods=["POST"])
@roles_required("trekker")
def trekker_book_trek(trek_id):
    user=_current_user()
    trek=Trek.query.get_or_404(trek_id)
    if trek.status!="Open":
        flash(f"'{trek.name}'is not open for booking right now.","danger")
        return redirect(url_for("main.trekker_treks"))
    if trek.available_slots<=0:
        flash(f"'{trek.name}' is fully booked. No slots available.","danger")
        return redirect(url_for("main.trekker_treks"))
    existing=Booking.query.filter_by(
        user_id=user.id,trek_id=trek.id,status="Booked"
    ).first()
    if existing:
        flash(f"You have already booked'{trek.name}'.","warning")
        return redirect(url_for("main.trekker_treks"))
    booking=Booking(user_id=user.id,trek_id=trek.id,status="Booked",payment_status="Pending")
    trek.available_slots-=1
    db.session.add(booking)
    db.session.commit()
    flash(f"Trek '{trek.name}' booked successfully.!","success")
    return redirect(url_for("main.trekker_dashboard"))

@main_bp.route("/user/bookings/<int:booking_id>/cancel",methods=["POST"])
@roles_required("trekker")
def trekker_cancel_booking(booking_id):
    user=_current_user()
    booking=Booking.query.filter_by(id=booking_id,user_id=user.id).first_or_404()
    if booking.status!="Booked":
        flash("Only active bookings can be cancelled","danger")
        return redirect(url_for("main.trekker_dashboard"))
    booking.status="Cancelled"
    booking.trek.available_slots+=1
    db.session.commit()
    flash(f"Booking for '{booking.trek.name}' has been cancelled","info")
    return redirect(url_for("main.trekker_dashboard"))

    
