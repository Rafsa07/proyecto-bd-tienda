from flask import Flask, render_template, request, redirect, url_for, flash, session
import pg8000
from urllib.parse import urlparse
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'llave_super_secreta_cambiar_en_produccion'

# --- TU URL DE SUPABASE ---
# ¡¡IMPORTANTE!!: Pega aquí tu URL completa de Supabase
DB_URL = "postgresql://postgres.wyyadxdolcatakciashc:Matemat1caS+%85@aws-0-us-west-2.pooler.supabase.com:5432/postgres"

def get_db_connection():
    try:
        result = urlparse(DB_URL)
        conn = pg8000.connect(
            user=result.username,
            password=result.password,
            host=result.hostname,
            database=result.path[1:],
            port=result.port,
            ssl_context=True
        )
        return conn
    except Exception as e:
        print(f"Error BD: {e}")
        return None

# --- DECORADOR PARA PROTEGER RUTAS (LOGIN REQUERIDO) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión primero.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- RUTAS DE AUTENTICACIÓN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id_usuario, password FROM usuarios WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/crear-admin')
def crear_admin():
    conn = get_db_connection()
    cur = conn.cursor()
    pass_hash = generate_password_hash('admin123')
    try:
        cur.execute("INSERT INTO usuarios (username, password) VALUES (%s, %s)", ('admin', pass_hash))
        conn.commit()
        return "Usuario 'admin' creado con contraseña 'admin123'"
    except:
        return "El usuario ya existe"
    finally:
        cur.close()
        conn.close()

# --- RUTAS DEL SISTEMA ---

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/productos')
@login_required
def productos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id_producto, p.nombre_producto, p.precio_venta, i.stock_actual, p.tipo_unidad 
        FROM productos p
        LEFT JOIN inventario i ON p.id_producto = i.id_producto
        ORDER BY p.id_producto ASC
    """)
    lista_productos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('productos.html', productos=lista_productos)

@app.route('/agregar_producto', methods=['POST'])
@login_required
def agregar_producto():
    nombre = request.form['nombre']
    precio = float(request.form['precio'])
    stock = float(request.form['stock'])
    tipo = request.form['tipo_unidad']
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        query_prod = "INSERT INTO productos (nombre_producto, precio_venta, tipo_unidad) VALUES (%s, %s, %s) RETURNING id_producto"
        cur.execute(query_prod, (nombre, precio, tipo))
        id_producto_nuevo = cur.fetchone()[0]
        
        query_inv = "INSERT INTO inventario (id_producto, stock_actual) VALUES (%s, %s)"
        cur.execute(query_inv, (id_producto_nuevo, stock))
        
        conn.commit()
        flash('Producto agregado.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error: {str(e)}', 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('productos'))

@app.route('/vender/<int:id_producto>', methods=['POST'])
@login_required
def vender(id_producto):
    cantidad = float(request.form['cantidad'])
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT i.stock_actual, p.precio_venta, p.nombre_producto FROM inventario i JOIN productos p ON i.id_producto = p.id_producto WHERE i.id_producto = %s", (id_producto,))
        data = cur.fetchone()
        
        stock_actual = float(data[0])
        precio_unitario = float(data[1])
        nombre_prod = data[2]
        
        if stock_actual >= cantidad:
            total_a_cobrar = cantidad * precio_unitario
            cur.execute("UPDATE inventario SET stock_actual = stock_actual - %s WHERE id_producto = %s", (cantidad, id_producto))
            cur.execute("INSERT INTO historial_ventas (nombre_producto, cantidad_vendida, total_cobrado) VALUES (%s, %s, %s)", 
                        (nombre_prod, cantidad, total_a_cobrar))
            conn.commit()
            flash(f'Venta exitosa. Cobrar: ${total_a_cobrar:.2f}', 'success')
        else:
            flash(f'Error: Solo hay {stock_actual} disponibles.', 'warning')
            
    except Exception as e:
        conn.rollback()
        flash(f'Error venta: {str(e)}', 'danger')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('productos'))

# --- AQUÍ ESTÁN LAS RUTAS QUE TE FALTABAN ---

@app.route('/recargar_stock/<int:id_producto>', methods=['POST'])
@login_required
def recargar_stock(id_producto):
    cantidad_nueva = float(request.form['cantidad_agregar'])
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE inventario SET stock_actual = stock_actual + %s WHERE id_producto = %s", 
                    (cantidad_nueva, id_producto))
        conn.commit()
        flash('Stock recargado exitosamente.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al recargar: {str(e)}', 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('productos'))

@app.route('/eliminar_producto/<int:id_producto>', methods=['POST'])
@login_required
def eliminar_producto(id_producto):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 1. Borrar inventario
        cur.execute("DELETE FROM inventario WHERE id_producto = %s", (id_producto,))
        # 2. Borrar producto
        cur.execute("DELETE FROM productos WHERE id_producto = %s", (id_producto,))
        conn.commit()
        flash('Producto eliminado correctamente.', 'info')
    except Exception as e:
        conn.rollback()
        flash(f'Error al eliminar: {str(e)}', 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('productos'))

@app.route('/reportes')
@login_required
def reportes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DATE(fecha_venta) as fecha, SUM(total_cobrado) as ganancia_total, COUNT(*) as num_ventas
        FROM historial_ventas
        GROUP BY DATE(fecha_venta)
        ORDER BY fecha DESC
    """)
    reporte_diario = cur.fetchall()
    cur.execute("SELECT * FROM historial_ventas ORDER BY fecha_venta DESC LIMIT 50")
    detalle = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('reportes.html', diario=reporte_diario, detalle=detalle)

if __name__ == '__main__':
    app.run(debug=True)
