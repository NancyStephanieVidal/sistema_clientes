from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import psycopg2
from datetime import datetime
import os
import sys
import math

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_flash_messages'

# ========== CONFIGURACIÓN MODIFICADA ==========
# OBTENER DATABASE_URL DE RENDER (VARIABLE DE ENTORNO)
DATABASE_URL = os.environ.get('DATABASE_URL')

# Configuración local para desarrollo (solo si no hay DATABASE_URL)
LOCAL_POSTGRES = {
    'host': 'localhost',
    'port': 5432,
    'database': 'sistema_clientes',
    'user': 'postgres',
    'password': 'postgres123'
}

# ========== FUNCIÓN DE CONEXIÓN MODIFICADA ==========
def get_db_connection():
    """Conecta a PostgreSQL (Render o local) o usa SQLite como respaldo"""
    
    # 1. PRIMERO INTENTAR CON RENDER POSTGRESQL (PRODUCCIÓN)
    if DATABASE_URL:
        try:
            print("🚀 Intentando conectar a PostgreSQL de Render...")
            # Render usa 'postgresql://' pero psycopg2 necesita 'postgres://'
            db_url = DATABASE_URL
            if db_url.startswith('postgresql://'):
                db_url = db_url.replace('postgresql://', 'postgres://', 1)
            
            # Conexión con SSL para Render
            conn = psycopg2.connect(db_url, sslmode='require')
            print("✅ ¡Conectado a PostgreSQL en Render!")
            return conn
        except Exception as e:
            print(f"❌ Error PostgreSQL (Render): {e}")
            print("Intentando conexión local...")
    
    # 2. SEGUNDO INTENTAR CON POSTGRESQL LOCAL (DESARROLLO)
    try:
        print("🔗 Intentando conectar a PostgreSQL local...")
        conn = psycopg2.connect(**LOCAL_POSTGRES)
        print("✅ ¡Conectado a PostgreSQL local!")
        return conn
    except Exception as e:
        print(f"❌ Error PostgreSQL (local): {e}")
    
    # 3. ÚLTIMO RECURSO: SQLITE
    print("📁 Usando SQLite como respaldo...")
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

# ========== RUTA ADICIONAL PARA INICIALIZAR BD ==========
@app.route('/init-db')
def init_db_route():
    """Ruta para inicializar la base de datos manualmente"""
    try:
        init_db()
        return '''
        <h1>✅ Base de datos inicializada correctamente!</h1>
        <p>Las tablas se han creado en PostgreSQL.</p>
        <p><a href="/">Volver al inicio</a> | <a href="/capturar">Ir al formulario</a></p>
        '''
    except Exception as e:
        return f'''
        <h1>❌ Error al inicializar base de datos</h1>
        <p><strong>Error:</strong> {str(e)}</p>
        <p><a href="/">Volver al inicio</a></p>
        '''

# ========== NUEVA FUNCIÓN DE RECOMENDACIÓN ==========
def recomendar_sucursal(domicilio):
    """Recomienda sucursal basada en el domicilio"""
    domicilio_lower = domicilio.lower()
    
    # Coordenadas simuladas de zonas de CDMX
    zonas_coordenadas = {
        # Zonas Sur
        'coapa': (19.2870, -99.1302),
        'coyoacan': (19.3458, -99.1623),
        'xochimilco': (19.2579, -99.1056),
        'tlalpan': (19.2871, -99.1399),
        'vallejo': (19.4785, -99.1432),
        'iztapalapa': (19.3585, -99.0671),
        
        # Zonas Norte
        'satelite': (19.5158, -99.2346),
        'naucalpan': (19.4785, -99.2387),
        'interlomas': (19.4138, -99.2841),
        'polanco': (19.4343, -99.1993),
        
        # Zonas Centro
        'patriotismo': (19.4038, -99.1785),
        'condesa': (19.4131, -99.1772),
        'roma': (19.4161, -99.1617),
        'juarez': (19.4326, -99.1332),
        'centro': (19.4326, -99.1332)
    }
    
    # Coordenadas de sucursales
    sucursales = {
        'KTM Ferbel Coapa': (19.2870, -99.1302),
        'KTM Ferbel Satelite': (19.5158, -99.2346),
        'Yamaha Ferbel Patriotismo': (19.4038, -99.1785)
    }
    
    # Detectar zona
    zona_detectada = None
    for zona, coords in zonas_coordenadas.items():
        if zona in domicilio_lower:
            zona_detectada = zona
            break
    
    # Calcular distancias
    distancias = {}
    for sucursal, coords_suc in sucursales.items():
        if zona_detectada:
            coords_zona = zonas_coordenadas[zona_detectada]
            # Calcular distancia aproximada en km
            distancia = math.sqrt(
                (coords_suc[0] - coords_zona[0])**2 + 
                (coords_suc[1] - coords_zona[1])**2
            ) * 111  # Conversión a km
            distancias[sucursal] = round(distancia, 1)
        else:
            # Distancias por defecto
            distancias = {
                'KTM Ferbel Coapa': 8.5,
                'KTM Ferbel Satelite': 12.3,
                'Yamaha Ferbel Patriotismo': 6.8
            }
    
    # Encontrar sucursal más cercana
    sucursal_recomendada = min(distancias, key=distancias.get)
    distancia_km = distancias[sucursal_recomendada]
    
    # Razón según zona detectada
    if zona_detectada:
        if any(z in zona_detectada for z in ['coapa', 'coyoacan', 'tlalpan', 'xochimilco', 'vallejo']):
            razon = f'Ubicado en zona Sur ({zona_detectada.capitalize()}) - Sucursal más cercana'
        elif any(z in zona_detectada for z in ['satelite', 'naucalpan', 'interlomas']):
            razon = f'Ubicado en zona Norte ({zona_detectada.capitalize()}) - Sucursal más cercana'
        elif any(z in zona_detectada for z in ['polanco', 'condesa', 'roma', 'juarez']):
            razon = f'Ubicado en zona Centro/Oeste ({zona_detectada.capitalize()}) - Sucursal más cercana'
        else:
            razon = f'Zona detectada: {zona_detectada.capitalize()} - Sucursal recomendada'
    else:
        razon = 'Sucursal principal recomendada (ubicación no específica detectada)'
    
    return {
        'sucursal_recomendada': sucursal_recomendada,
        'distancia_km': distancia_km,
        'razon': razon,
        'zona_detectada': zona_detectada.capitalize() if zona_detectada else 'No identificada',
        'todas_distancias': distancias
    }

# ========== NUEVA RUTA PARA RECOMENDACIÓN ==========
@app.route('/api/recomendacion', methods=['GET'])
def api_recomendacion():
    """Endpoint para recomendación de sucursal"""
    try:
        domicilio = request.args.get('domicilio', '')
        
        if not domicilio or len(domicilio) < 3:
            return jsonify({
                'error': 'Debe proporcionar un domicilio válido (mínimo 3 caracteres)'
            }), 400
        
        recomendacion = recomendar_sucursal(domicilio)
        return jsonify(recomendacion)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== EJECUCIÓN MODIFICADA ==========
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 INICIANDO SISTEMA DE CAPTURA DE CLIENTES")
    print("="*60)
    
    # Verificar si estamos en Render
    is_render = 'RENDER' in os.environ or 'DATABASE_URL' in os.environ
    port = int(os.environ.get('PORT', 5000))
    
    # Instalar psycopg2 si no está instalado
    try:
        import psycopg2
    except ImportError:
        print("📦 Instalando psycopg2 para PostgreSQL...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
        import psycopg2
    
    # Inicializar la base de datos
    init_db()
    
    print(f"\n💾 Modo: {'PostgreSQL en Render' if DATABASE_URL else 'PostgreSQL local o SQLite'}")
    print(f"🌐 Servidor: http://0.0.0.0:{port}")
    print(f"🔧 Entorno: {'Render' if is_render else 'Local'}")
    print("="*60 + "\n")
    
    # Ejecutar la aplicación
    # En Render usa 0.0.0.0, local usa 127.0.0.1
    host = '0.0.0.0' if is_render else '127.0.0.1'
    app.run(host=host, port=port, debug=not is_render)