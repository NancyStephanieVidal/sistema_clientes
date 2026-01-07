from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from datetime import datetime
import os
import sys
import time

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_flash_messages'

# ========== CONFIGURACIÓN ==========
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    print(f"✅ DATABASE_URL encontrada en variables de entorno")
    if DATABASE_URL.startswith('postgresql://'):
        DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgres://', 1)
else:
    print("⚠️ DATABASE_URL no encontrada.")

# ========== FUNCIÓN DE CONEXIÓN ==========
def get_db_connection():
    """Conecta a PostgreSQL de Render"""
    if DATABASE_URL:
        try:
            print("🔗 Conectando a PostgreSQL de Render...")
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            print("✅ ¡Conectado a PostgreSQL en Render!")
            return conn
        except Exception as e:
            print(f"❌ Error PostgreSQL: {e}")
            raise e
    
    # Si no hay DATABASE_URL, usar SQLite local
    import sqlite3
    conn = sqlite3.connect('clientes.db')
    conn.row_factory = sqlite3.Row
    return conn

# ========== INICIALIZACIÓN DE BASE DE DATOS ==========
def init_db():
    """CREA las tablas en PostgreSQL si no existen"""
    print("\n" + "="*60)
    print("🏗️  INICIALIZANDO BASE DE DATOS POSTGRESQL")
    print("="*60)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. CREAR TABLA clientes
        print("📋 Creando tabla 'clientes'...")
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
        
        # 2. CREAR TABLA motocicletas
        print("📋 Creando tabla 'motocicletas'...")
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
        
        # 3. CREAR TABLA sucursales
        print("📋 Creando tabla 'sucursales'...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sucursales (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            domicilio TEXT NOT NULL,
            marca VARCHAR(50) NOT NULL
        )
        ''')
        
        conn.commit()
        
        # 4. VERIFICAR SI HAY DATOS
        print("🔍 Verificando datos existentes...")
        
        # Verificar sucursales
        cursor.execute('SELECT COUNT(*) FROM sucursales')
        count_sucursales = cursor.fetchone()[0]
        
        if count_sucursales == 0:
            print("📝 Insertando datos de sucursales...")
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
        
        # Verificar motocicletas
        cursor.execute('SELECT COUNT(*) FROM motocicletas')
        count_motos = cursor.fetchone()[0]
        
        if count_motos == 0:
            print("📝 Insertando datos de motocicletas...")
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
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Base de datos inicializada correctamente!")
        print(f"   - Sucursales: {count_sucursales} existentes, {3 if count_sucursales == 0 else 0} nuevas")
        print(f"   - Motocicletas: {count_motos} existentes, {10 if count_motos == 0 else 0} nuevas")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error al inicializar base de datos: {e}")
        raise e

# ========== RUTAS ==========
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/capturar')
def mostrar_formulario():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Obtener motocicletas
        cursor.execute('SELECT * FROM motocicletas ORDER BY marca, modelo')
        motocicletas = cursor.fetchall()
        
        # Obtener sucursales
        cursor.execute('SELECT * FROM sucursales ORDER BY nombre')
        sucursales = cursor.fetchall()
        
        # Formatear para template
        motos_formateadas = []
        for moto in motocicletas:
            motos_formateadas.append(f"{moto[1]} {moto[2]} ({moto[3]})")
        
        sucursales_formateadas = []
        for suc in sucursales:
            sucursales_formateadas.append(suc[1])
            
    except Exception as e:
        print(f"Error en mostrar_formulario: {e}")
        motos_formateadas = []
        sucursales_formateadas = []
    finally:
        cursor.close()
        conn.close()
    
    return render_template('clientes.html', 
                         motocicletas=motos_formateadas,
                         sucursales=sucursales_formateadas)

# ... (el resto de tus rutas se mantienen igual: guardar_cliente, lista_clientes, etc.)
# COPIA EL RESTO DE TUS RUTAS AQUÍ SIN CAMBIOS

# ========== INICIALIZAR AL INICIAR ==========
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 INICIANDO SISTEMA DE CAPTURA DE CLIENTES")
    print("="*60)
    
    # 1. Inicializar base de datos (CREA TABLAS)
    try:
        init_db()
    except Exception as e:
        print(f"⚠️ Advertencia: {e}")
        print("Continuando sin inicializar base de datos...")
    
    # 2. Configurar puerto para Render
    port = int(os.environ.get('PORT', 5000))
    is_render = 'PORT' in os.environ
    
    print(f"\n💾 Base de datos: PostgreSQL en Render")
    print(f"🌐 Servidor: http://localhost:{port}")
    print("="*60 + "\n")
    
    # 3. Ejecutar aplicación
    app.run(host='0.0.0.0', port=port, debug=not is_render)