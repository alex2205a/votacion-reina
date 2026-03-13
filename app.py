from flask import Flask, render_template, request, redirect, session
import os
import psycopg2
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "clave_super_secreta"

UPLOAD_FOLDER = "static/fotos"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


# =========================
# INDEX
# =========================
@app.route("/")
def index():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM candidatas")
    candidatas = cursor.fetchall()

    cursor.close()
    db.close()

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

    cursor.execute(
        "SELECT * FROM alumnos WHERE matricula = %s",
        (matricula,)
    )
    alumno = cursor.fetchone()

    if not alumno:
        cursor.close()
        db.close()
        return "Matrícula no válida"

    if alumno[1] == 1:
        cursor.close()
        db.close()
        return "Ya votaste"

    cursor.execute(
        "UPDATE candidatas SET votos = votos + 1 WHERE id = %s",
        (candidata_id,)
    )

    cursor.execute(
        "UPDATE alumnos SET voto = 1 WHERE matricula = %s",
        (matricula,)
    )

    db.commit()

    cursor.close()
    db.close()

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

    cursor.close()
    db.close()

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

    cursor.close()
    db.close()

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

    cursor.close()
    db.close()

    return redirect("/admin")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
