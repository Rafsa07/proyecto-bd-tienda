from flask import Flask, render_template, request, redirect, url_for
import pg8000
from urllib.parse import urlparse
import os

app = Flask(__name__)

# --- TU URL DE SUPABASE (Pega aquí tu URI completa) ---
# Ejemplo: "postgresql://postgres.xxxx:pass@xxxx.supabase.co:5432/postgres"
DB_URL = "postgresql://postgres.wyyadxdolcatakciashc:Matemat1caS+%85@aws-0-us-west-2.pooler.supabase.com:5432/postgres"

def get_db_connection():
    # Esta pequeña función traduce la URL de Supabase para pg8000
    result = urlparse(DB_URL)
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port
    
    # Creamos la conexión (SSL es obligatorio en Supabase)
    conn = pg8000.connect(
        user=username,
        password=password,
        host=hostname,
        database=database,
        port=port,
        ssl_context=True 
    )
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/productos')
def productos():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # pg8000 usa una sintaxis SQL estándar
    cur.execute("""
        SELECT p.id_producto, p.nombre_producto, p.precio_venta, i.stock_actual 
        FROM productos p
        LEFT JOIN inventario i ON p.id_producto = i.id_producto
    """)
    lista_productos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('productos.html', productos=lista_productos)

@app.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    nombre = request.form['nombre']
    precio = float(request.form['precio']) # Convertimos a float
    stock = int(request.form['stock'])     # Convertimos a int
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 1. Insertar Producto (pg8000 usa %s igual que psycopg2)
        query_prod = "INSERT INTO productos (nombre_producto, precio_venta) VALUES (%s, %s) RETURNING id_producto"
        cur.execute(query_prod, (nombre, precio))
        id_producto_nuevo = cur.fetchone()[0]
        
        # 2. Insertar Inventario
        query_inv = "INSERT INTO inventario (id_producto, stock_actual) VALUES (%s, %s)"
        cur.execute(query_inv, (id_producto_nuevo, stock))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Error:", e)
    finally:
        cur.close()
        conn.close()
        
    return redirect(url_for('productos'))

if __name__ == '__main__':
    app.run(debug=True)