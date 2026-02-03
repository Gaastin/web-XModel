from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'clave_secreta_xmodel_roblox_2026_no_compartir'

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB
DATABASE = 'database.db'

ADMIN_PASSWORD = '2009241030'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            image TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_id INTEGER,
            service_name TEXT NOT NULL,
            username TEXT NOT NULL,
            contact TEXT NOT NULL,
            roblox_user TEXT,
            message TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            status TEXT DEFAULT 'nuevo',
            FOREIGN KEY(service_id) REFERENCES services(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/store")
def store():
    conn = get_db()
    services = conn.execute("SELECT * FROM services ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("store.html", services=services)

@app.route("/service/<int:service_id>", methods=["GET", "POST"])
def service_detail(service_id):
    conn = get_db()
    service = conn.execute("SELECT * FROM services WHERE id = ?", (service_id,)).fetchone()
    if not service:
        conn.close()
        return "Servicio no encontrado", 404

    if request.method == "POST":
        username    = request.form.get("username", "").strip()
        contact     = request.form.get("contact", "").strip()
        roblox_user = request.form.get("roblox_user", "").strip()
        message     = request.form.get("message", "").strip()

        if not username or not contact:
            conn.close()
            return "Faltan datos obligatorios", 400

        conn.execute('''
            INSERT INTO requests (service_id, service_name, username, contact, roblox_user, message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (service_id, service['name'], username, contact, roblox_user, message))
        conn.commit()
        conn.close()
        return render_template("success.html", service_name=service['name'])

    conn.close()
    return render_template("product.html", service=service)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get('admin_logged_in'):
        if request.method == "POST":
            password = request.form.get("password")
            if password == ADMIN_PASSWORD:
                session['admin_logged_in'] = True
                flash("Acceso correcto", "success")
                return redirect(url_for("admin"))
            else:
                flash("Clave incorrecta", "error")
        return render_template("admin_login.html")

    conn = get_db()
    message = None

    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            name = request.form.get("name", "").strip()
            description = request.form.get("description", "").strip()
            try:
                price = float(request.form.get("price", "0"))
            except:
                price = 0
            image_file = request.files.get("image_file")
            image_filename = ""

            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_filename = filename

            if name and description and price > 0:
                conn.execute('INSERT INTO services (name, description, price, image) VALUES (?, ?, ?, ?)',
                             (name, description, price, image_filename))
                conn.commit()
                message = "Servicio agregado"
            else:
                message = "Error en los datos"

        elif action == "delete":
            try:
                sid = int(request.form.get("service_id"))
                conn.execute("DELETE FROM services WHERE id = ?", (sid,))
                conn.commit()
                message = "Eliminado"
            except:
                message = "Error al eliminar"

    services = conn.execute("SELECT * FROM services ORDER BY id DESC").fetchall()
    requests = conn.execute("SELECT * FROM requests ORDER BY created_at DESC LIMIT 50").fetchall()
    conn.close()

    return render_template("admin.html", services=services, requests=requests, message=message)

@app.route("/admin/logout")
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for("admin"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)