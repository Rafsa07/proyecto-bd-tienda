# 🛒 Sistema de Gestión Integral "Superzito"

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.0-000000?style=for-the-badge&logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white)
![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)

> **Un sistema robusto para la administración de inventarios híbridos (piezas y granel), control de ventas y análisis financiero en tiempo real.**

---

## 📖 Descripción del Proyecto

Este proyecto nace de la necesidad de modernizar la gestión de una tienda de abarrotes y frutería. A diferencia de los sistemas de punto de venta (POS) tradicionales, **Superzito** está diseñado específicamente para manejar la complejidad de productos que se venden por **peso (kilos/gramos)** y por **unidad (piezas)** simultáneamente.

El sistema resuelve problemas críticos como:
* Pérdida de trazabilidad en ventas a granel (ej. vender 0.450 kg de manzana).
* Descuadre de inventarios físicos vs. lógicos.
* Falta de reportes históricos de ganancias.

---

## 🚀 Despliegue (Demo en Vivo)

El proyecto cuenta con una arquitectura de despliegue continuo (CI/CD):

| Versión | Estado | Enlace | Descripción |
| :--- | :---: | :--- | :--- |
| **Producción** | 🟢 Online | [**Ver App en Render**](https://tu-proyecto.onrender.com) | Aplicación completa con Base de Datos y Backend activo. *(Nota: Puede tardar 50s en iniciar por suspensión de inactividad).* |
| **Demo Estática** | ⚡ Rápida | [**Ver en GitHub Pages**](https://rafsa07.github.io/proyecto-bd-tienda/) | Maqueta de alta fidelidad para revisión visual inmediata de la interfaz (Sin lógica de servidor). |

---

## 🛠️ Stack Tecnológico

### Backend (Lógica del Servidor)
* **Lenguaje:** Python 3.12
* **Framework:** Flask (Microframework para arquitectura modular).
* **Seguridad:** `Werkzeug.security` para Hashing de contraseñas (PBKDF2/SHA256).
* **ORM/DB Driver:** `Psycopg2` para conexiones nativas y eficientes a PostgreSQL.

### Base de Datos (Persistencia)
* **Motor:** PostgreSQL 16.
* **Cloud Provider:** Supabase (BaaS).
* **Características:** Uso de `Constraints` (Restricciones), Llaves Foráneas (FK) y tipos de datos `NUMERIC` para precisión decimal en pesaje.

### Frontend (Interfaz de Usuario)
* **Estructura:** HTML5 Semántico + Jinja2 Templating.
* **Estilos:** Bootstrap 5 (Dark Mode nativo).
* **Iconografía:** Bootstrap Icons.

---

## 📸 Capturas de Pantalla

### 1. Panel de Control de Inventario
*Visualización en tiempo real del stock, con alertas visuales y opciones CRUD.*
[INSERTAR IMAGEN DEL INVENTARIO AQUI]

### 2. Módulo de Ventas
*Interfaz optimizada para el cobro rápido, permitiendo selección de clientes y cálculo automático de totales.*
[INSERTAR IMAGEN DE VENTAS/MODAL AQUI]

### 3. Seguridad y Acceso
*Sistema de Login protegido contra inyecciones SQL y ataques de fuerza bruta básicos.*
[INSERTAR IMAGEN DEL LOGIN AQUI]

---

## 🧱 Arquitectura de la Base de Datos

El diseño de la base de datos sigue las reglas de **Normalización (3NF)** para evitar redundancia de datos.

### Diagrama Relacional (Esquema)
* **Usuarios:** Administradores del sistema.
* **Inventario:** Tabla pivote que gestiona el stock físico.
* **Historial_Ventas:** Tabla inmutable para auditoría financiera.

```mermaid
erDiagram
    USUARIOS ||--|{ INVENTARIO : Gestiona
    PRODUCTOS ||--|| INVENTARIO : "Tiene un"
    PRODUCTOS ||--o{ HISTORIAL_VENTAS : "Genera"
    
    PRODUCTOS {
        int id_producto PK
        string nombre
        numeric precio
        string tipo_unidad "Kilo/Pieza"
    }

    INVENTARIO {
        int id_inventario PK
        numeric stock_actual
        date ultima_actualizacion
    }
