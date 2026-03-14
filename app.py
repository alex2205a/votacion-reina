from flask import Flask, render_template, request, redirect, session, flash
import psycopg2
import psycopg2.extras
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "clave_super_secreta"

UPLOAD_FOLDER = "static/fotos"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

DATABASE_URL = "postgresql://postgres.twmehwedutbtwhstkyyk:votacioncecyt11@aws-0-us-west-2.pooler.supabase.com:5432/postgres"


# =========================
# CONEXION DB
# =========================
def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


# =========================
# INDEX
# =========================
@app.route("/")
def index():

    db = get_db()
    cursor = db.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute("""
SELECT id,nombre,foto,votos
FROM candidatas
ORDER BY id ASC
""")
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
    cursor = db.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute(
        "SELECT voto FROM alumnos WHERE matricula=%s",
        (matricula,)
    )

    alumno = cursor.fetchone()

    # MATRÍCULA NO EXISTE
    if alumno is None:
        flash("❌ Matrícula no válida")
        cursor.close()
        db.close()
        return redirect("/")

    # YA VOTÓ
    if alumno["voto"] == 1:
        flash("⚠️ Ya votaste anteriormente")
        cursor.close()
        db.close()
        return redirect("/")

    # REGISTRAR VOTO
    cursor.execute(
        "UPDATE candidatas SET votos=votos+1 WHERE id=%s",
        (candidata_id,)
    )

    cursor.execute(
        "UPDATE alumnos SET voto=1 WHERE matricula=%s",
        (matricula,)
    )

    db.commit()
    cursor.close()
    db.close()

    # Flash de éxito y no redirigir
    flash("✅ Tu voto ha sido registrado con éxito")

    # Devuelve el mismo template con candidatas
    db = get_db()
    cursor = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("""
        SELECT id,nombre,foto,votos
        FROM candidatas
        ORDER BY id ASC
    """)
    candidatas = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template("index.html", candidatas=candidatas)


# =========================
# RESULTADOS
# =========================
@app.route("/resultados")
def resultados():
    if not session.get("can_view_results") and not session.get("admin"):
        flash("❌ Debes ingresar la contraseña para ver los resultados")
        return redirect("/")

    db = get_db()
    cursor = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("""
        SELECT id,nombre,foto,votos 
        FROM candidatas
        ORDER BY votos DESC
    """)
    candidatas = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("resultados.html", candidatas=candidatas)
# =========================
# LOGIN ADMIN
# =========================
@app.route("/admin_login", methods=["POST"])
def admin_login():
    password = request.form["password"]
    next_page = request.form.get("next", "admin")  # admin por defecto

    if next_page == "admin":
        if password == "admin123":
            session["admin"] = True
            return redirect("/admin")
        else:
            flash("❌ Contraseña de admin incorrecta")
            return redirect("/")

    elif next_page == "resultados":
        if password == "resultados123":
            session["can_view_results"] = True
            return redirect("/resultados")
        else:
            flash("❌ Contraseña para ver resultados incorrecta")
            return redirect("/")


# =========================
# PANEL ADMIN
# =========================
@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/")

    db = get_db()
    cursor = db.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute("""
    SELECT id,nombre,foto,votos
    FROM candidatas
    ORDER BY id ASC
    """)

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
    cursor = db.cursor(cursor_factory=psycopg2.extras.DictCursor)

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
    port = int(os.environ.get("PORT", 10000))  # usa el puerto de Render o 10000 por defecto
    app.run(host="0.0.0.0", port=port, debug=True)
