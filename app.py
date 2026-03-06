from flask import Flask, render_template, request, redirect, session
import os
from werkzeug.utils import secure_filename
import psycopg2

app = Flask(__name__)
app.secret_key = "clave_super_secreta"

UPLOAD_FOLDER = "static/fotos"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =========================
# CONEXION BASE DE DATOS (POSTGRES RENDER)
# =========================
def get_db():
    DATABASE_URL = os.environ.get("DATABASE_URL")

    conn = psycopg2.connect(DATABASE_URL)
    return conn


# =========================
# CREAR TABLAS AUTOMATICAMENTE
# =========================
def crear_tablas():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS candidatas (
        id SERIAL PRIMARY KEY,
        nombre TEXT,
        foto TEXT,
        votos INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS alumnos (
        matricula TEXT PRIMARY KEY,
        voto INTEGER DEFAULT 0
    )
    """)

    conn.commit()

    # insertar candidatas si no existen
    cur.execute("SELECT COUNT(*) FROM candidatas")
    total = cur.fetchone()[0]

    if total == 0:

        cur.execute("""
        INSERT INTO candidatas (nombre, foto, votos)
        VALUES
        ('Candidata 1','c1.jpg',0),
        ('Candidata 2','c2.jpg',0),
        ('Candidata 3','c3.jpg',0)
        """)

    conn.commit()
    cur.close()
    conn.close()


# =========================
# INDEX
# =========================
@app.route("/")
def index():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM candidatas")
    candidatas = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("index.html", candidatas=candidatas)


# =========================
# VOTAR
# =========================
@app.route("/votar", methods=["POST"])
def votar():

    matricula = request.form["matricula"]
    candidata_id = request.form["candidata"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM alumnos WHERE matricula = %s",
        (matricula,)
    )

    alumno = cur.fetchone()

    if not alumno:
        return "Matrícula no válida"

    if alumno[1] == 1:
        return "Ya votaste"

    cur.execute(
        "UPDATE candidatas SET votos = votos + 1 WHERE id = %s",
        (candidata_id,)
    )

    cur.execute(
        "UPDATE alumnos SET voto = 1 WHERE matricula = %s",
        (matricula,)
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/resultados")


# =========================
# RESULTADOS
# =========================
@app.route("/resultados")
def resultados():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM candidatas")
    candidatas = cur.fetchall()

    cur.close()
    conn.close()

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

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM candidatas")
    candidatas = cur.fetchall()

    cur.close()
    conn.close()

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

    conn = get_db()
    cur = conn.cursor()

    if foto and foto.filename != "":

        filename = secure_filename(foto.filename)
        ruta = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        foto.save(ruta)

        cur.execute("""
        UPDATE candidatas
        SET nombre=%s, foto=%s
        WHERE id=%s
        """, (nuevo_nombre, filename, candidata_id))

    else:

        cur.execute("""
        UPDATE candidatas
        SET nombre=%s
        WHERE id=%s
        """, (nuevo_nombre, candidata_id))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/admin")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():

    session.pop("admin", None)
    return redirect("/")


# =========================
# INICIAR APP
# =========================
crear_tablas()

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
