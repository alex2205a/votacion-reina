from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.utils import secure_filename
import psycopg2

app = Flask(__name__)
app.secret_key = "clave_super_secreta"

UPLOAD_FOLDER = "static/fotos"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =========================
# CONEXION BASE DE DATOS
# =========================
def get_db():

    DATABASE_URL = os.environ.get("DATABASE_URL")

    # SI ESTA EN RENDER -> POSTGRESQL
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        return conn

    # SI ESTA EN TU PC -> SQLITE
    conn = sqlite3.connect("votacion.db")
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# INDEX (ALUMNOS)
# =========================
@app.route("/")
def index():

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM candidatas")
    candidatas = cursor.fetchall()

    return render_template("index.html", candidatas=candidatas)


# =========================
# VOTAR
# =========================
@app.route("/votar", methods=["POST"])
def votar():

    matricula = request.form["matricula"]
    candidata_id = request.form["candidata"]

    db = get_db()
    cursor = db.cursor()

    # verificar alumno
    cursor.execute("SELECT * FROM alumnos WHERE matricula=%s", (matricula,))
    alumno = cursor.fetchone()

    if not alumno:
        return "Matrícula no válida"

    if alumno[2] == 1:
        return "Ya votaste"

    cursor.execute(
        "UPDATE candidatas SET votos = votos + 1 WHERE id=%s",
        (candidata_id,)
    )

    cursor.execute(
        "UPDATE alumnos SET voto = 1 WHERE matricula=%s",
        (matricula,)
    )

    db.commit()

    return redirect("/resultados")


# =========================
# RESULTADOS
# =========================
@app.route("/resultados")
def resultados():

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM candidatas")
    candidatas = cursor.fetchall()

    return render_template("resultados.html", candidatas=candidatas)


# =========================
# LOGIN ADMIN
# =========================
@app.route("/admin_login", methods=["POST"])
def admin_login():

    if request.form["password"] == "admin123":
        session["admin"] = True
        return redirect("/admin")

    return "Contraseña incorrecta"


# =========================
# PANEL ADMIN
# =========================
@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/")

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM candidatas")
    candidatas = cursor.fetchall()

    return render_template("admin.html", candidatas=candidatas)


# =========================
# EDITAR CANDIDATA
# =========================
@app.route("/editar", methods=["POST"])
def editar():

    if not session.get("admin"):
        return "No autorizado"

    candidata_id = request.form["id"]
    nuevo_nombre = request.form["nombre"]
    foto = request.files["foto"]

    db = get_db()
    cursor = db.cursor()

    if foto and foto.filename != "":

        filename = secure_filename(foto.filename)
        ruta = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        foto.save(ruta)

        cursor.execute("""
        UPDATE candidatas
        SET nombre=%s, foto=%s
        WHERE id=%s
        """, (nuevo_nombre, filename, candidata_id))

    else:

        cursor.execute("""
        UPDATE candidatas
        SET nombre=%s
        WHERE id=%s
        """, (nuevo_nombre, candidata_id))

    db.commit()

    return redirect("/admin")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect("/")


# =========================
# INICIAR SERVIDOR
# =========================
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)
