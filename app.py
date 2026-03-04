import os
from functools import wraps

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from models import Trip, User, db
from utils.budget_calculator import estimate_budget
from utils.itinerary_generator import generate_itinerary
from utils.pdf_exporter import create_itinerary_pdf


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "destina-prod-secret-change-in-env")
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
database_url = os.getenv("DATABASE_URL")

if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


INTEREST_OPTIONS = ["Adventure", "Religious", "Food", "History", "Nature"]
GUEST_EMAIL = "guest@destina.com"
GUEST_USERNAME = "Guest Traveler"


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return wrapper


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def is_admin_user(user):
    return bool(user and user.email.lower() == "admin@destina.com")


def get_or_create_guest_user():
    guest = User.query.filter_by(email=GUEST_EMAIL).first()
    if not guest:
        guest = User(
            username=GUEST_USERNAME,
            email=GUEST_EMAIL,
            password_hash=generate_password_hash("guest-account-disabled"),
        )
        db.session.add(guest)
        db.session.commit()
    return guest


def get_guest_trip_ids():
    return session.get("guest_trip_ids", [])


def track_guest_trip(trip_id):
    trip_ids = get_guest_trip_ids()
    if trip_id not in trip_ids:
        trip_ids.append(trip_id)
        session["guest_trip_ids"] = trip_ids


def get_trip_owner_id():
    user = current_user()
    if user:
        return user.id
    return get_or_create_guest_user().id


def can_access_trip(trip):
    user = current_user()
    if user and is_admin_user(user):
        return True
    if user:
        return trip.user_id == user.id
    return trip.id in get_guest_trip_ids()


@app.context_processor
def inject_globals():
    user = current_user()
    return {
        "logged_in": user is not None,
        "current_user": user,
        "is_admin": is_admin_user(user),
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    flash("User registration is disabled. Use planner directly without login.", "info")
    return redirect(url_for("planner"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if email != "admin@destina.com":
            flash("Only admin login is allowed.", "danger")
            return render_template("login.html")

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        session["user_id"] = user.id
        flash("Logged in successfully.", "success")

        if is_admin_user(user):
            return redirect(url_for("admin"))

        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    user = current_user()
    if user and is_admin_user(user):
        trips = Trip.query.order_by(Trip.created_at.desc()).limit(5).all()
    elif user:
        trips = (
            Trip.query.filter_by(user_id=user.id)
            .order_by(Trip.created_at.desc())
            .limit(5)
            .all()
        )
    else:
        trip_ids = get_guest_trip_ids()
        trips = (
            Trip.query.filter(Trip.id.in_(trip_ids))
            .order_by(Trip.created_at.desc())
            .all()
            if trip_ids
            else []
        )
    return render_template("dashboard.html", trips=trips)


@app.route("/planner", methods=["GET", "POST"])
def planner():
    if request.method == "POST":
        destination = request.form.get("destination", "").strip()
        days_raw = request.form.get("days", "").strip()
        budget_raw = request.form.get("budget", "").strip()
        interests = request.form.getlist("interests")

        if not destination or not days_raw or not budget_raw:
            flash("Destination, days and budget are required.", "danger")
            return render_template("planner.html", interest_options=INTEREST_OPTIONS)

        try:
            days = int(days_raw)
            budget = float(budget_raw)
            if days <= 0 or budget <= 0:
                raise ValueError
        except ValueError:
            flash("Please enter valid positive values for days and budget.", "danger")
            return render_template("planner.html", interest_options=INTEREST_OPTIONS)

        if not interests:
            interests = ["Nature"]

        itinerary = generate_itinerary(days=days, interests=interests, destination=destination)
        budget_data = estimate_budget(days=days, user_budget=budget, interests=interests)

        trip = Trip(
            user_id=get_trip_owner_id(),
            destination=destination,
            days=days,
            budget=budget,
            interests=",".join(interests),
            total_cost=budget_data["total_estimated_cost"],
        )
        db.session.add(trip)
        db.session.commit()
        if not current_user():
            track_guest_trip(trip.id)

        return render_template(
            "result.html",
            trip=trip,
            itinerary=itinerary,
            budget_data=budget_data,
            interests=interests,
        )

    return render_template("planner.html", interest_options=INTEREST_OPTIONS)


@app.route("/trip/<int:trip_id>")
def trip_detail(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if not can_access_trip(trip):
        flash("You are not authorized to view this trip.", "danger")
        return redirect(url_for("my_trips"))

    interests = [item for item in trip.interests.split(",") if item]
    itinerary = generate_itinerary(days=trip.days, interests=interests, destination=trip.destination)
    budget_data = estimate_budget(days=trip.days, user_budget=trip.budget, interests=interests)

    return render_template(
        "result.html",
        trip=trip,
        itinerary=itinerary,
        budget_data=budget_data,
        interests=interests,
    )


@app.route("/my-trips")
def my_trips():
    user = current_user()
    if user and is_admin_user(user):
        trips = Trip.query.order_by(Trip.created_at.desc()).all()
    elif user:
        trips = (
            Trip.query.filter_by(user_id=user.id)
            .order_by(Trip.created_at.desc())
            .all()
        )
    else:
        trip_ids = get_guest_trip_ids()
        trips = (
            Trip.query.filter(Trip.id.in_(trip_ids))
            .order_by(Trip.created_at.desc())
            .all()
            if trip_ids
            else []
        )
    return render_template("my_trips.html", trips=trips)


@app.route("/download/<int:trip_id>")
def download_itinerary(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if not can_access_trip(trip):
        flash("You are not authorized to download this itinerary.", "danger")
        return redirect(url_for("my_trips"))

    interests = [item for item in trip.interests.split(",") if item]
    itinerary = generate_itinerary(days=trip.days, interests=interests, destination=trip.destination)

    pdf_buffer = create_itinerary_pdf(trip, itinerary)
    filename = f"destina_{trip.destination.lower().replace(' ', '_')}_{trip.id}.pdf"

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf",
    )


@app.route("/admin")
@login_required
def admin():
    user = current_user()
    if not is_admin_user(user):
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    users = User.query.order_by(User.id.asc()).all()
    trips = Trip.query.order_by(Trip.created_at.desc()).all()
    return render_template("admin.html", users=users, trips=trips)


def initialize_database():
    with app.app_context():
        db.create_all()

        admin_email = "admin@destina.com"
        admin_password = "admin123"

        admin_user = User.query.filter_by(email=admin_email).first()
        if not admin_user:
            admin_user = User(
                username="Admin",
                email=admin_email,
                password_hash=generate_password_hash(admin_password),
            )
            db.session.add(admin_user)
            db.session.commit()

        get_or_create_guest_user()


initialize_database()


if __name__ == "__main__":
    initialize_database()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)