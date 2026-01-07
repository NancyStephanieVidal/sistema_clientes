from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from datetime import datetime
import os
import sys

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_flash_messages'

# ========== CONFIGURACIÓN ==========
# CAMBIA ESTA VARIABLE SEGÚN LO QUE QUIERAS USAR
USAR_POSTGRESQL = True  # Cambia a True para PostgreSQL, False para SQLite

# Configuración de PostgreSQL (solo si USAR_POSTGRESQL = True)
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'sistema_clientes',
    'user': 'postgres',
    'password': 'postgres123'  # <-- NUEVA CONTRASEÑA
}

# ========== FUNCIÓN DE CONEXIÓN ==========
def get_db_connection():
    """Conecta a PostgreSQL o SQLite según configuración"""
    if USAR_POSTGRESQL:
        try:
            conn = psycopg2.connect(**POSTGRES_CONFIG)
            return conn
        except Exception as e:
            print(f"❌ Error PostgreSQL: {e}")
            print("📁 Usando SQLite como respaldo...")
            # Fallback a SQLite
            import sqlite3
            conn = sqlite3.connect('clientes.db')
            conn.row_factory = sqlite3.Row
            return conn
    else:
        # Usar SQLite directamente
        import sqlite3
        conn = sqlite3.connect('clientes.db')
        conn.row_factory = sqlite3.Row
        return conn

# ========== INICIALIZACIÓN DE BASE DE DATOS ==========
def init_db():
    """Inicializa tablas y datos"""
    conn = get_db_connection()
    
    # Detectar tipo de conexión
    is_postgres = 'psycopg2' in str(type(conn))
    
    if is_postgres:
        print("📊 Inicializando PostgreSQL...")
        cursor = conn.cursor()
        
        # Tablas para PostgreSQL
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            primer_nombre VARCHAR(50) NOT NULL,
            segundo_nombre VARCHAR(50),
            primer_apellido VARCHAR(50) NOT NULL,
            segundo_apellido VARCHAR(50),
            email VARCHAR(100) UNIQUE NOT NULL,
            domicilio TEXT NOT NULL,
            telefono VARCHAR(20),
            motocicleta_interes VARCHAR(100) NOT NULL,
            sucursal VARCHAR(100) NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS motocicletas (
            id SERIAL PRIMARY KEY,
            marca VARCHAR(50) NOT NULL,
            modelo VARCHAR(100) NOT NULL,
            año INTEGER NOT NULL,
            precio DECIMAL(10, 2),
            tipo VARCHAR(50)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sucursales (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            domicilio TEXT NOT NULL,
            marca VARCHAR(50) NOT NULL
        )
        ''')
        
        # Verificar si ya hay datos
        cursor.execute('SELECT COUNT(*) FROM sucursales')
        if cursor.fetchone()[0] == 0:
            # Insertar sucursales
            sucursales = [
                ('KTM Ferbel Coapa', 'Canal de Miramontes 3000-Locales 1 y 2, Coyoacan, CDMX', 'KTM'),
                ('KTM Ferbel Satelite', 'Periferico Blvd. Manuel Avila Camacho 1920, Naucalpan, Mex.', 'KTM'),
                ('Yamaha Ferbel Patriotismo', 'Av. Patriotismo 98, Miguel Hidalgo, CDMX', 'Yamaha')
            ]
            
            for sucursal in sucursales:
                cursor.execute(
                    'INSERT INTO sucursales (nombre, domicilio, marca) VALUES (%s, %s, %s)',
                    sucursal
                )
            
            # Insertar motocicletas
            motocicletas = [
                ('KTM', 'Duke 390', 2024, 125000.00, 'Naked'),
                ('KTM', '1290 Super Duke R', 2024, 450000.00, 'Naked'),
                ('KTM', '390 Adventure', 2023, 135000.00, 'Adventure'),
                ('Yamaha', 'YZF-R1', 2024, 380000.00, 'Deportiva'),
                ('Yamaha', 'MT-07', 2024, 165000.00, 'Naked'),
                ('Yamaha', 'XTZ 250', 2023, 95000.00, 'Enduro'),
                ('Honda', 'CBR 600RR', 2024, 220000.00, 'Deportiva'),
                ('Suzuki', 'GSX-R1000', 2024, 350000.00, 'Deportiva'),
                ('Harley-Davidson', 'Sportster', 2024, 280000.00, 'Cruiser'),
                ('BMW', 'S1000RR', 2024, 420000.00, 'Deportiva')
            ]
            
            for moto in motocicletas:
                cursor.execute(
                    'INSERT INTO motocicletas (marca, modelo, año, precio, tipo) VALUES (%s, %s, %s, %s, %s)',
                    moto
                )
            
            print("✅ Datos iniciales insertados en PostgreSQL")
        
        conn.commit()
        cursor.close()
        
    else:
        # SQLite (tu código original)
        print("📊 Inicializando SQLite...")
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            primer_nombre TEXT NOT NULL,
            segundo_nombre TEXT,
            primer_apellido TEXT NOT NULL,
            segundo_apellido TEXT,
            email TEXT NOT NULL UNIQUE,
            domicilio TEXT NOT NULL,
            telefono TEXT,
            motocicleta_interes TEXT NOT NULL,
            sucursal TEXT NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS motocicletas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            año INTEGER NOT NULL,
            precio REAL,
            tipo TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sucursales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            domicilio TEXT NOT NULL,
            marca TEXT NOT NULL
        )
        ''')
        
        cursor.execute('SELECT COUNT(*) FROM sucursales')
        if cursor.fetchone()[0] == 0:
            sucursales = [
                ('KTM Ferbel Coapa', 'Canal de Miramontes 3000-Locales 1 y 2, Coyoacan, CDMX', 'KTM'),
                ('KTM Ferbel Satelite', 'Periferico Blvd. Manuel Avila Camacho 1920, Naucalpan, Mex.', 'KTM'),
                ('Yamaha Ferbel Patriotismo', 'Av. Patriotismo 98, Miguel Hidalgo, CDMX', 'Yamaha')
            ]
            cursor.executemany('INSERT INTO sucursales (nombre, domicilio, marca) VALUES (?, ?, ?)', sucursales)
            
            motocicletas = [
                ('KTM', 'Duke 390', 2024, 125000.00, 'Naked'),
                ('KTM', '1290 Super Duke R', 2024, 450000.00, 'Naked'),
                ('KTM', '390 Adventure', 2023, 135000.00, 'Adventure'),
                ('Yamaha', 'YZF-R1', 2024, 380000.00, 'Deportiva'),
                ('Yamaha', 'MT-07', 2024, 165000.00, 'Naked'),
                ('Yamaha', 'XTZ 250', 2023, 95000.00, 'Enduro'),
                ('Honda', 'CBR 600RR', 2024, 220000.00, 'Deportiva'),
                ('Suzuki', 'GSX-R1000', 2024, 350000.00, 'Deportiva'),
                ('Harley-Davidson', 'Sportster', 2024, 280000.00, 'Cruiser'),
                ('BMW', 'S1000RR', 2024, 420000.00, 'Deportiva')
            ]
            cursor.executemany('INSERT INTO motocicletas (marca, modelo, año, precio, tipo) VALUES (?, ?, ?, ?, ?)', motocicletas)
            
            print("✅ Datos iniciales insertados en SQLite")
        
        conn.commit()
    
    conn.close()
    print("🎉 Base de datos inicializada correctamente")

# ========== RUTAS (igual que antes) ==========
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/capturar')
def mostrar_formulario():
    conn = get_db_connection()
    
    # Detectar tipo de conexión
    is_postgres = 'psycopg2' in str(type(conn))
    
    if is_postgres:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM motocicletas ORDER BY marca, modelo')
        motocicletas = cursor.fetchall()
        
        cursor.execute('SELECT * FROM sucursales ORDER BY nombre')
        sucursales = cursor.fetchall()
        cursor.close()
        
        # Formatear para template
        motos_formateadas = []
        for moto in motocicletas:
            motos_formateadas.append(f"{moto[1]} {moto[2]} ({moto[3]})")
        
        sucursales_formateadas = []
        for suc in sucursales:
            sucursales_formateadas.append(suc[1])
            
    else:
        motocicletas = conn.execute('SELECT * FROM motocicletas ORDER BY marca, modelo').fetchall()
        sucursales = conn.execute('SELECT * FROM sucursales ORDER BY nombre').fetchall()
        
        # Formatear para template
        motos_formateadas = []
        for moto in motocicletas:
            motos_formateadas.append(f"{moto['marca']} {moto['modelo']} ({moto['año']})")
        
        sucursales_formateadas = []
        for suc in sucursales:
            sucursales_formateadas.append(suc['nombre'])
    
    conn.close()
    
    return render_template('clientes.html', 
                         motocicletas=motos_formateadas,
                         sucursales=sucursales_formateadas)

@app.route('/guardar-cliente', methods=['POST'])
def guardar_cliente():
    if request.method == 'POST':
        conn = get_db_connection()
        is_postgres = 'psycopg2' in str(type(conn))
        
        try:
            if is_postgres:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO clientes 
                (primer_nombre, segundo_nombre, primer_apellido, segundo_apellido, 
                 email, domicilio, telefono, motocicleta_interes, sucursal)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    request.form['primer_nombre'],
                    request.form['segundo_nombre'] or None,
                    request.form['primer_apellido'],
                    request.form['segundo_apellido'] or None,
                    request.form['email'],
                    request.form['domicilio'],
                    request.form.get('telefono') or None,
                    request.form['motocicleta_interes'],
                    request.form['sucursal']
                ))
            else:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO clientes 
                (primer_nombre, segundo_nombre, primer_apellido, segundo_apellido, 
                 email, domicilio, telefono, motocicleta_interes, sucursal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    request.form['primer_nombre'],
                    request.form['segundo_nombre'] or None,
                    request.form['primer_apellido'],
                    request.form['segundo_apellido'] or None,
                    request.form['email'],
                    request.form['domicilio'],
                    request.form.get('telefono') or None,
                    request.form['motocicleta_interes'],
                    request.form['sucursal']
                ))
            
            conn.commit()
            conn.close()
            
            flash('✅ Cliente registrado exitosamente!', 'success')
            
        except Exception as e:
            if is_postgres:
                conn.rollback()
            conn.close()
            
            if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
                flash('❌ Error: El correo electrónico ya está registrado', 'error')
            else:
                flash(f'❌ Error al registrar cliente: {str(e)}', 'error')
    
    return redirect(url_for('mostrar_formulario'))

@app.route('/lista-clientes')
def lista_clientes():
    conn = get_db_connection()
    is_postgres = 'psycopg2' in str(type(conn))
    
    if is_postgres:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clientes ORDER BY fecha_registro DESC')
        clientes_tuples = cursor.fetchall()
        cursor.close()
        
        # Convertir tuplas a diccionarios
        clientes = []
        for cliente in clientes_tuples:
            clientes.append({
                'id': cliente[0],
                'primer_nombre': cliente[1],
                'segundo_nombre': cliente[2],
                'primer_apellido': cliente[3],
                'segundo_apellido': cliente[4],
                'email': cliente[5],
                'domicilio': cliente[6],
                'telefono': cliente[7],
                'motocicleta_interes': cliente[8],
                'sucursal': cliente[9],
                'fecha_registro': cliente[10]
            })
    else:
        clientes = conn.execute('SELECT * FROM clientes ORDER BY fecha_registro DESC').fetchall()
        # Convertir Row objects a diccionarios
        clientes = [dict(cliente) for cliente in clientes]
    
    conn.close()
    
    return render_template('lista_clientes.html', clientes=clientes)

@app.route('/catalogo-motocicletas')
def catalogo_motocicletas():
    conn = get_db_connection()
    is_postgres = 'psycopg2' in str(type(conn))
    
    if is_postgres:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM motocicletas ORDER BY marca, modelo')
        motocicletas = cursor.fetchall()
        cursor.close()
    else:
        motocicletas = conn.execute('SELECT * FROM motocicletas ORDER BY marca, modelo').fetchall()
    
    conn.close()
    return render_template('catalogo_motocicletas.html', motocicletas=motocicletas)

@app.route('/sucursales')
def lista_sucursales():
    conn = get_db_connection()
    is_postgres = 'psycopg2' in str(type(conn))
    
    if is_postgres:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sucursales ORDER BY nombre')
        sucursales = cursor.fetchall()
        cursor.close()
    else:
        sucursales = conn.execute('SELECT * FROM sucursales ORDER BY nombre').fetchall()
    
    conn.close()
    return render_template('sucursales.html', sucursales=sucursales)

# ========== EJECUCIÓN ==========
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 INICIANDO SISTEMA DE CAPTURA DE CLIENTES")
    print("="*60)
    
    # Instalar psycopg2 si no está instalado y queremos PostgreSQL
    if USAR_POSTGRESQL:
        try:
            import psycopg2
        except ImportError:
            print("📦 Instalando psycopg2 para PostgreSQL...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
            import psycopg2
    
    # Inicializar la base de datos
    init_db()
    
    print(f"\n💾 Base de datos: {'PostgreSQL' if USAR_POSTGRESQL else 'SQLite'}")
    print("🌐 Servidor: http://localhost:5000")
    print("="*60 + "\n")
    
    # Ejecutar la aplicación
    app.run(debug=True, port=5000)