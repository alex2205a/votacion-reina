import sqlite3

conexion = sqlite3.connect("votacion.db")
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS alumnos (
    matricula TEXT PRIMARY KEY,
    voto INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS candidatas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    votos INTEGER DEFAULT 0,
    foto TEXT
)
""")

# Crear 1000 matrículas de prueba
for i in range(1000):
    matricula = f"400426{i:03}"
    cursor.execute("INSERT OR IGNORE INTO alumnos (matricula) VALUES (?)", (matricula,))

# Crear 8 candidatas
for i in range(1, 9):
    cursor.execute("""
    INSERT INTO candidatas (nombre, foto)
    VALUES (?, ?)
    """, (f"Candidata {i}", "default.jpg"))

conexion.commit()
conexion.close()

print("Base de datos creada correctamente")