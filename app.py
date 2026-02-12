import os
import sqlite3
from flask import Flask, render_template, request, redirect, session, g
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "your_secret_key"
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
DATABASE = "db.sqlite3"

# Database connection
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

# Home
@app.route("/")
def index():
    return render_template("index.html")

# Report page
@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        location = request.form["location"]
        category = request.form["category"]
        photo = request.files.get("photo")
        filename = None
        if photo and photo.filename != "":
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        db = get_db()
        db.execute(
            "INSERT INTO items (name, description, location, category, photo, status, approved) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, description, location, category, filename, "approved", 0)
        )
        db.commit()
        return redirect("/browse")
    return render_template("report.html")

# Browse items
@app.route("/browse")
def browse():
    db = get_db()
    query = "SELECT * FROM items WHERE 1=1"
    params = []

    if "role" not in session or session.get("role") not in ["staff", "admin"]:
        query += " AND approved = 1"

    q = request.args.get("q")
    category = request.args.get("category")
    status = request.args.get("status")

    if status and ("role" in session and session.get("role") in ["staff", "admin"]):
        query += " AND status = ?"
        params.append(status)

    if q:
        query += " AND name LIKE ?"
        params.append(f"%{q}%")
    if category:
        query += " AND category = ?"
        params.append(category)

    items = db.execute(query, params).fetchall()
    return render_template("browse.html", items=items)

# Claim index page – list of claimable items
@app.route("/claim", methods=["GET"])
def claim_index():
    db = get_db()
    items = db.execute(
        "SELECT * FROM items WHERE approved=1 AND status='approved'"
    ).fetchall()
    return render_template("claim_index.html", items=items)

# Claim specific item
@app.route("/claim/<int:item_id>", methods=["GET", "POST"])
def claim(item_id):
    db = get_db()
    item = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        return "Item not found", 404

    if request.method == "POST":
        student = request.form["student"]
        email = request.form["email"]
        message = request.form.get("message")
        db.execute(
            "INSERT INTO claims (item_id, student_name, email, message, status) VALUES (?, ?, ?, ?, ?)",
            (item_id, student, email, message, "pending")
        )
        db.commit()
        return redirect("/browse")

    return render_template("claim.html", item=item)

# Admin login
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        accounts = {"viewer":"viewer", "staff":"staff", "admin":"admin123"}
        if username in accounts and accounts[username] == password:
            session["user"] = username
            session["role"] = "admin" if username == "admin" else "staff"
            return redirect("/admin/panel")
        else:
            return render_template("admin_login.html", error="Invalid login")
    return render_template("admin_login.html")

# Admin panel
@app.route("/admin/panel")
def admin_panel():
    if "user" not in session or session.get("role") not in ["staff", "admin"]:
        return redirect("/admin")
    db = get_db()
    items = db.execute("SELECT * FROM items").fetchall()
    claims = db.execute("SELECT * FROM claims").fetchall()
    role = session.get("role")
    return render_template("admin_panel.html", items=items, claims=claims, role=role)

# Admin actions
@app.route("/admin/approve/<int:item_id>")
def approve_item(item_id):
    if "user" not in session or session.get("role") not in ["staff", "admin"]:
        return redirect("/admin")
    db = get_db()
    db.execute("UPDATE items SET approved = 1 WHERE id = ?", (item_id,))
    db.commit()
    return redirect("/admin/panel")

@app.route("/admin/status/<int:item_id>/<new_status>")
def update_status(item_id, new_status):
    if "user" not in session or session.get("role") not in ["staff", "admin"]:
        return redirect("/admin")
    db = get_db()
    db.execute("UPDATE items SET status = ? WHERE id = ?", (new_status, item_id))
    db.commit()
    return redirect("/admin/panel")

@app.route("/admin/claim/<int:claim_id>/<action>")
def handle_claim(claim_id, action):
    if "user" not in session or session.get("role") not in ["staff", "admin"]:
        return redirect("/admin")
    db = get_db()
    if action == "resolved":
        db.execute("UPDATE claims SET status = 'resolved' WHERE id = ?", (claim_id,))
    elif action == "rejected":
        db.execute("UPDATE claims SET status = 'rejected' WHERE id = ?", (claim_id,))
    db.commit()
    return redirect("/admin/panel")

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# Documentation page
@app.route("/doc")
def documentation():
    return render_template("doc.html")

if __name__ == "__main__":
    app.run(debug=True)
