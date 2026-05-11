from flask import Flask, render_template, request, redirect, session, flash
import psycopg2
import psycopg2.extras
import os
from werkzeug.utils import secure_filename
from supabase import create_client
import time

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_key")

# 🔑 SUPABASE
SUPABASE_URL = "https://twmehwedutbtwhstkyyk.supabase.co"
SUPABASE_KEY = "sb_publishable_ziGnT8tm69cMpDy1-bxRlA_Ky-9w2ch"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🗄️ DATABASE
DATABASE_URL = "postgresql://postgres.twmehwedutbtwhstkyyk:votacioncecyt11@aws-0-us-west-2.pooler.supabase.com:5432/postgres"

def get_db():
    return psycopg2.connect(DATABASE_URL)

# =========================
# SUBIR IMAGEN
# =========================
def subir_imagen(file):
    nombre = secure_filename(file.filename)
    nombre_unico = f"{int(time.time())}_{nombre}"
    ruta = f"candidatas/{nombre_unico}"

    supabase.storage.from_("candidatas").upload(
        ruta,
        file.read(),
        {"content-type": file.content_type}
    )

    return supabase.storage.from_("candidatas").get_public_url(ruta)

# =========================
# ELIMINAR IMAGEN
# =========================
def eliminar_imagen(url):
    try:
        if url and "supabase" in url:
            nombre = url.split("/")[-1]
            ruta = f"candidatas/{nombre}"
            supabase.storage.from_("candidatas").remove([ruta])
    except Exception as e:
        print("Error eliminando:", e)

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

    cursor.execute("SELECT voto FROM alumnos WHERE matricula=%s", (matricula,))
    alumno = cursor.fetchone()

    if alumno is None:
        flash("❌ Matrícula no válida")
        return redirect("/")

    if alumno["voto"] == 1:
        flash("⚠️ Ya votaste anteriormente")
        return redirect("/")

    cursor.execute("UPDATE candidatas SET votos=votos+1 WHERE id=%s", (candidata_id,))
    cursor.execute("UPDATE alumnos SET voto=1 WHERE matricula=%s", (matricula,))

    db.commit()
    cursor.close()
    db.close()

    flash("✅ Tu voto ha sido registrado con éxito")
    return redirect("/")

# =========================
# RESULTADOS
# =========================
@app.route("/resultados")
def resultados():
    if not session.get("can_view_results") and not session.get("admin"):
        flash("❌ Debes ingresar la contraseña")
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
# LOGIN
# =========================
@app.route("/admin_login", methods=["POST"])
def admin_login():
    password = request.form["password"]
    next_page = request.form.get("next", "admin")

    if next_page == "admin":
        if password == "admin123":
            session["admin"] = True
            return redirect("/admin")
    else:
        if password == "resultados123":
            session["can_view_results"] = True
            return redirect("/resultados")

    flash("❌ Contraseña incorrecta")
    return redirect("/")

# =========================
# ADMIN
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
# EDITAR
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

    cursor.execute("SELECT foto FROM candidatas WHERE id=%s", (candidata_id,))
    actual = cursor.fetchone()

    if "eliminar_foto" in request.form:
        if actual and actual["foto"]:
            eliminar_imagen(actual["foto"])

        cursor.execute("UPDATE candidatas SET foto=NULL WHERE id=%s", (candidata_id,))

    elif foto and foto.filename != "":
        if actual and actual["foto"]:
            eliminar_imagen(actual["foto"])

        url = subir_imagen(foto)

        cursor.execute("""
            UPDATE candidatas
            SET nombre=%s, foto=%s
            WHERE id=%s
        """, (nuevo_nombre, url, candidata_id))

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
# REINICIAR TODOS LOS VOTOS
# =========================
@app.route("/reiniciar_votos")
def reiniciar_votos():

    if not session.get("admin"):
        return redirect("/")

    db = get_db()

    cursor = db.cursor()

    # Reiniciar votos de candidatas
    cursor.execute("""
    UPDATE candidatas
    SET votos = 0
    """)

    # Permitir votar otra vez a alumnos
    cursor.execute("""
    UPDATE alumnos
    SET voto = 0
    """)

    db.commit()

    cursor.close()
    db.close()

    flash("✅ Todos los votos fueron reiniciados")

    return redirect("/admin")

# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
