import os, shutil

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, abort, url_for, send_from_directory
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from helpers import apology, login_required, lookup, usd

UPLOAD_FOLDER = '/static'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


# Configure application
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///hikely.db")

@app.route("/")
@login_required
def index():
 return render_template("index.html")

def allowed_file(filename):
    return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    # check if the post request has the file part

@app.route("/add", methods=["GET", "POST"])
@login_required

def add():
    # POST
    if request.method == "POST":

        # Validate form submission
        if not request.form.get("hike"):
            return apology("missing hike")
        elif not request.form.get("description"):
            return apology("missing description")
        elif not request.form.get("country"):
            return apology("missing country")
        elif not request.form.get("state"):
            return apology("missing state")
        elif not request.form.get("town"):
            return apology("missing town")
        elif not request.form.get("rating"):
            return apology("missing rating")
        elif not request.form.get("difficulty"):
            return apology("missing difficulty")

        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            basedir = os.path.abspath(os.path.dirname(__file__))
            print(os.path.join(basedir, filename))
            file.save(os.path.join(basedir, filename))
            shutil.move(filename, "./static/"+filename)

        rows = db.execute("SELECT id FROM users WHERE id = :id", id=session["user_id"])
        if not rows:
            return apology("missing user")

        # Record addition
        db.execute("""INSERT INTO "hikes" ("user_id", "hike", "country", "state", "town", "rating", "difficulty", "description", "image")
        VALUES(:user_id, :hike, :country, :state, :town, :rating, :difficulty, :description, :image)""",
                    user_id=session["user_id"],
                    hike=request.form.get("hike"),
                    country=request.form.get("country"),
                    state=request.form.get("state"),
                    town=request.form.get("town"),
                    rating=request.form.get("rating"),
                    difficulty=request.form.get("difficulty"),
                    description=request.form.get("description"),
                    image=filename)

        # Display added hike
        flash("Added!")
        return redirect("/")

    else:
        return render_template("hike.html")

@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    return jsonify("TODO")


@app.route("/view")
@login_required
def view():
    """View Repository of Hikes"""
    hikes = db.execute(
        "SELECT * FROM hikes WHERE user_id = :user_id", user_id=session["user_id"])
    for hike in hikes:
        hike["edit"] = "http://ide50-whl24.cs50.io:8080/edit" + "?id=" + str(hike["id"])

    return render_template("view.html", hikes=hikes)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user for an account."""

    # POST
    if request.method == "POST":

        # Validate form submission
        if not request.form.get("username"):
            return apology("missing username")
        elif not request.form.get("password"):
            return apology("missing password")
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match")

        # Add user to database
        id = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
                        username=request.form.get("username"),
                        hash=generate_password_hash(request.form.get("password")))
        if not id:
            return apology("username taken")

        # Log user in
        session["user_id"] = id

        # Let user know they're registered
        flash("Registered!")
        return redirect("/")

    # GET
    else:
        return render_template("register.html")


@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    hikeId = request.args.get("id")
    hike = db.execute("SELECT * FROM hikes WHERE id = :id", id=hikeId)
    return render_template("edit.html", hike=hike[0])


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
