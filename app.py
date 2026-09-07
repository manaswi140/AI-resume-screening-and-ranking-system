import os
import sqlite3
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from ranking import rank_resumes
from text_processing import preprocess_text  # optional reuse


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_default_secret_key")

# Uploads
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = (".pdf", ".docx")


# Helpers
def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn


def allowed_file(filename: str) -> bool:
    return filename.lower().endswith(ALLOWED_EXTENSIONS)


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("You must log in first!", "error")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapper


# Routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, password, username FROM users WHERE email = ?", (email,)
        )
        user = cursor.fetchone()
        conn.close()

        if not user:
            flash("User not found", "error")
            return redirect(url_for("login"))

        stored_password = user["password"]
        if not check_password_hash(stored_password, password):
            flash("Invalid password", "error")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        # After login go to dashboard
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")

        if not email or not username or not password:
            flash("All fields are required!", "error")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (email, username, password) VALUES (?, ?, ?)",
                (email, username, hashed_password),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            flash("Email already registered!", "error")
            return redirect(url_for("register"))

        conn.close()
        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/forgotpassword", methods=["GET", "POST"])
def forgotpassword():
    # AJAX POST → JSON; GET → render page
    if request.method == "POST":
        email = request.form.get("email", "").strip()

        if not email:
            return jsonify({"status": "error", "message": "Email is required!"}), 400

        # Optional: check if email exists (but do not reveal status)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        cursor.fetchone()
        conn.close()

        # Here you would generate a token and email a reset link.
        # For now, always return a generic success message.
        return jsonify(
            {
                "status": "success",
                "message": "If this email is registered, a reset link has been sent.",
            }
        )

    return render_template("forgotpassword.html")


@app.route("/dashboard")
@login_required
def dashboard():
    username = session.get("username")
    user_id = session.get("user_id")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT resume_name, score, created_at
        FROM rank_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()

    last_screening = None
    if row:
        last_screening = {
            "resume_name": row["resume_name"],
            "score": row["score"],
            "created_at": row["created_at"],
        }

    return render_template(
        "dashboard.html",
        current_user={"username": username},
        last_screening=last_screening,
    )


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    # Clear previous upload session on fresh GET
    if request.method == "GET":
        session.pop("uploaded_files", None)
        return render_template("uploads.html")

    # POST: handle files
    if "resumes" not in request.files:
        flash("No files selected!", "error")
        return render_template("uploads.html")

    files = request.files.getlist("resumes")
    file_paths = []

    for file in files:
        if not file or not file.filename:
            continue
        if not allowed_file(file.filename):
            continue

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        file_paths.append(filepath)

    if file_paths:
        session["uploaded_files"] = file_paths
        flash(f"{len(file_paths)} resumes uploaded!", "success")
    else:
        flash("No valid PDF/DOCX files!", "error")

    return render_template("uploads.html")


@app.route("/rank", methods=["GET", "POST"])
@login_required
def rank():
    if "uploaded_files" not in session:
        flash("No resumes uploaded!", "error")
        return redirect(url_for("upload"))

    if request.method == "POST":
        job_description = request.form.get("job_description", "")
        file_paths = session.get("uploaded_files", [])

        # Rank resumes
        rankings = rank_resumes(file_paths, job_description)

        # Save top resume into rank_history
        if rankings:
            best_resume_name, best_score = rankings[0]
            user_id = session.get("user_id")

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO rank_history (user_id, resume_name, score)
                VALUES (?, ?, ?)
                """,
                (user_id, best_resume_name, best_score),
            )
            conn.commit()
            conn.close()

        return render_template("results.html", rankings=rankings)

    return render_template("rank.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    flash("Logged out successfully!", "info")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
