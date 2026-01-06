from flask import Flask, render_template, request, redirect, url_for, flash, session
import pg8000
from urllib.parse import urlparse
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'llave_super_secreta_cambiar_en_produccion'


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


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión primero.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


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


@app.route('/')
@login_required
def index():
    return render_template('index.html')
@app.route('/proveedores')
@login_required
def proveedores():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM proveedores ORDER BY id_proveedor ASC")
    lista_proveedores = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('proveedores.html', proveedores=lista_proveedores)

@app.route('/agregar_proveedor', methods=['POST'])
@login_required
def agregar_proveedor():
    empresa = request.form['empresa']
    contacto = request.form['contacto']
    telefono = request.form['telefono']
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO proveedores (empresa, contacto, telefono) VALUES (%s, %s, %s)", 
                    (empresa, contacto, telefono))
        conn.commit()
        flash('Proveedor registrado exitosamente.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error: {str(e)}', 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('proveedores'))

@app.route('/productos')
@login_required
def productos():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT p.id_producto, p.nombre_producto, p.precio_venta, i.stock_actual, p.tipo_unidad, pr.empresa 
        FROM productos p
        LEFT JOIN inventario i ON p.id_producto = i.id_producto
        LEFT JOIN proveedores pr ON p.id_proveedor = pr.id_proveedor
        ORDER BY p.id_producto ASC
    """)
    lista_productos = cur.fetchall()
    

    cur.execute("SELECT id_proveedor, empresa FROM proveedores ORDER BY empresa")
    lista_proveedores = cur.fetchall()

    try:
        cur.execute("SELECT c.id_cliente, p.nombre FROM clientes c JOIN persona p ON c.id_persona = p.id_persona")
        lista_clientes = cur.fetchall()
    except:
        lista_clientes = [] 

    cur.close()
    conn.close()
    return render_template('productos.html', 
                           productos=lista_productos, 
                           proveedores=lista_proveedores,
                           clientes=lista_clientes)

@app.route('/agregar_producto', methods=['POST'])
@login_required
def agregar_producto():
    nombre = request.form['nombre']
    precio = float(request.form['precio'])
    stock = float(request.form['stock'])
    tipo = request.form['tipo_unidad']
    id_proveedor = request.form['id_proveedor'] 
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:

        query_prod = "INSERT INTO productos (nombre_producto, precio_venta, tipo_unidad, id_proveedor) VALUES (%s, %s, %s, %s) RETURNING id_producto"
        cur.execute(query_prod, (nombre, precio, tipo, id_proveedor))
        id_producto_nuevo = cur.fetchone()[0]
        
        query_inv = "INSERT INTO inventario (id_producto, stock_actual) VALUES (%s, %s)"
        cur.execute(query_inv, (id_producto_nuevo, stock))
        
        conn.commit()
        flash('Producto agregado correctamente.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error: {str(e)}', 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('productos'))


@app.route('/clientes')
@login_required
def clientes():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.id_cliente, p.nombre, p.telefono, p.email, c.direccion 
        FROM clientes c 
        JOIN persona p ON c.id_persona = p.id_persona
    """)
    lista_clientes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('clientes.html', clientes=lista_clientes)

@app.route('/agregar_cliente', methods=['POST'])
@login_required
def agregar_cliente():
    nombre = request.form['nombre']
    telefono = request.form['telefono']
    email = request.form['email']
    direccion = request.form['direccion']
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:

        cur.execute("INSERT INTO persona (nombre, telefono, email) VALUES (%s, %s, %s) RETURNING id_persona", (nombre, telefono, email))
        id_persona_nueva = cur.fetchone()[0]
        
        cur.execute("INSERT INTO clientes (id_persona, direccion) VALUES (%s, %s)", (id_persona_nueva, direccion))
        conn.commit()
        flash('Cliente registrado.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error: {str(e)}', 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('clientes'))

@app.route('/vender/<int:id_producto>', methods=['POST'])
@login_required
def vender(id_producto):
    cantidad = float(request.form['cantidad'])

    id_cliente_generico = 1 
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:

        cur.execute("""
            SELECT i.stock_actual, p.precio_venta, p.nombre_producto 
            FROM inventario i 
            JOIN productos p ON i.id_producto = p.id_producto 
            WHERE i.id_producto = %s
        """, (id_producto,))
        data = cur.fetchone()
        
        if not data:
            raise Exception("Producto no encontrado")

        stock_actual = float(data[0])
        precio_unitario = float(data[1])
        nombre_prod = data[2]
        total_venta = cantidad * precio_unitario
        
        if stock_actual >= cantidad:

            cur.execute("""
                INSERT INTO ventas (id_cliente, id_encargado, total, fecha_venta)
                VALUES (%s, %s, %s, NOW()) RETURNING id_venta
            """, (id_cliente_generico, session['user_id'], total_venta))
            id_venta_nueva = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """, (id_venta_nueva, id_producto, cantidad, precio_unitario, total_venta))

            cur.execute("UPDATE inventario SET stock_actual = stock_actual - %s WHERE id_producto = %s", (cantidad, id_producto))
            
            cur.execute("INSERT INTO historial_ventas (nombre_producto, cantidad_vendida, total_cobrado) VALUES (%s, %s, %s)", 
                        (nombre_prod, cantidad, total_venta))

            conn.commit()
            flash(f'Venta #{id_venta_nueva} registrada. Cobrar: ${total_venta:.2f}', 'success')
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
        cur.execute("DELETE FROM inventario WHERE id_producto = %s", (id_producto,))

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

@app.route('/buscar', methods=['POST'])
def buscar():
    termino = request.form['busqueda']
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    query_insegura = f"SELECT id_producto, nombre_producto, precio_venta, 0, tipo_unidad FROM productos WHERE nombre_producto LIKE %s"

    termino_con_comodines = f"%{termino}%" 
   
    try:
        cur.execute(query_insegura)
        resultados = cur.fetchall()
    except Exception as e:
        resultados = []
        print(f"ERROR EN ATAQUE: {e}")
    finally:
        cur.close()
        conn.close()
        
    return render_template('productos.html', productos=resultados)
if __name__ == '__main__':
    app.run(debug=True)
