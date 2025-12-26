from flask import Flask, render_template, request, redirect, session
import sqlite3
import csv
import matplotlib.pyplot as plt
import os

from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)
app.secret_key = "admin_secret_key"


def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            rating INTEGER,
            comments TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/submit-feedback", methods=["POST"])
def submit_feedback():
    name = request.form["name"]
    email = request.form["email"]
    rating = request.form["rating"]
    comments = request.form["comments"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO feedback (name, email, rating, comments) VALUES (?, ?, ?, ?)",
        (name, email, rating, comments)
    )
    conn.commit()
    conn.close()

    return redirect("/")

# 🔴 THIS ROUTE IS MISSING IN YOUR CODE
@app.route("/admin-dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feedback")
    feedback = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM feedback")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(rating) FROM feedback")
    avg = cursor.fetchone()[0]

    conn.close()
    ratings = [row[3] for row in feedback]

    plt.figure()
    plt.hist(ratings, bins=5)
    plt.title("Feedback Ratings")
    plt.xlabel("Rating")
    plt.ylabel("Count")

    chart_path = "static/ratings.png"
    plt.savefig(chart_path)
    plt.close()

    return render_template(
        "admin.html",
        feedback=feedback,
        total=total,
        average=round(avg, 2) if avg else 0
    )
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["admin"] = True
            return redirect("/admin-dashboard")
        else:
            return "Invalid credentials"

    return render_template("login.html")
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/login")
@app.route("/export")
def export_csv():
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feedback")
    data = cursor.fetchall()
    conn.close()

    with open("feedback.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Name", "Email", "Rating", "Comments"])
        writer.writerows(data)

    return "CSV file exported successfully!"
@app.route("/delete/<int:id>")
def delete_feedback(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM feedback WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin-dashboard")
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_feedback(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # When form is submitted (UPDATE)
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        rating = request.form["rating"]
        comments = request.form["comments"]

        cursor.execute("""
            UPDATE feedback
            SET name = ?, email = ?, rating = ?, comments = ?
            WHERE id = ?
        """, (name, email, rating, comments, id))

        conn.commit()
        conn.close()
        return redirect("/admin-dashboard")

    # When page is opened (FETCH old data)
    cursor.execute("SELECT * FROM feedback WHERE id = ?", (id,))
    feedback = cursor.fetchone()
    conn.close()

    return render_template("edit.html", feedback=feedback)





if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True,
        use_reloader=False
    )

