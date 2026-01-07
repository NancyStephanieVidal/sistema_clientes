"""
API REST con FastAPI para gestionar clientes, motocicletas y sucursales
OPTIMIZADO PARA RENDER.COM
"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import psycopg2
from datetime import datetime
import os
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

# Importar el módulo de geolocalización
try:
    from geolocalizacion import SimuladorGeolocalizacion
except ImportError:
    # Si no existe, crea una versión simple
    class SimuladorGeolocalizacion:
        @staticmethod
        def recomendar_sucursal(domicilio):
            return {
                "sucursal_recomendada": "Sucursal Centro",
                "distancia_km": 5.0,
                "razon": "Más cercana a tu ubicación",
                "zona_detectada": "Zona Centro",
                "todas_distancias": {"Centro": 5.0, "Norte": 10.0, "Sur": 8.0}
            }
        
        ZONAS_COORDENADAS = {"Centro": (19.4326, -99.1332)}
        SUCURSALES_GEO = {"Sucursal Centro": "Calle Principal 123"}

# ========== CONFIGURACIÓN DE BASE DE DATOS ==========
def get_db_connection():
    """Conecta a PostgreSQL en Render o localmente"""
    try:
        # Render proporciona DATABASE_URL automáticamente
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url:
            # Para Render - la URL ya viene con formato
            # postgresql://usuario:contraseña@host:puerto/base_datos
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            
            print(f"🔗 Conectando a: {database_url[:50]}...")  # Log parcial
            conn = psycopg2.connect(database_url, sslmode='require')
            print("✅ Conexión exitosa a PostgreSQL en Render")
            return conn
        else:
            # Para desarrollo local
            print("🔗 Conectando a PostgreSQL local...")
            conn = psycopg2.connect(
                host='localhost',
                port=5433,
                database='sistema_clientes',
                user='postgres',
                password='postgres123'
            )
            print("✅ Conexión exitosa a PostgreSQL local")
            return conn
            
    except Exception as e:
        print(f"❌ Error de conexión a PostgreSQL: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error de conexión a la base de datos: {str(e)}"
        )

# ========== INICIALIZAR FASTAPI ==========
app = FastAPI(
    title="API Ferbel Motocicletas",
    description="API REST para gestión de clientes, motocicletas y sucursales",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ========== CONFIGURACIÓN CORS ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todos los orígenes
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ========== MODELOS PYDANTIC ==========
class ClienteBase(BaseModel):
    primer_nombre: str
    segundo_nombre: Optional[str] = None
    primer_apellido: str
    segundo_apellido: Optional[str] = None
    email: EmailStr
    domicilio: str
    telefono: Optional[str] = None
    motocicleta_interes: str
    sucursal: str

class ClienteResponse(ClienteBase):
    id: int
    fecha_registro: datetime

class MotocicletaResponse(BaseModel):
    id: int
    marca: str
    modelo: str
    año: int
    precio: Optional[float] = None
    tipo: Optional[str] = None

class SucursalResponse(BaseModel):
    id: int
    nombre: str
    domicilio: str
    marca: str

class RecomendacionResponse(BaseModel):
    sucursal_recomendada: str
    distancia_km: float
    razon: str
    zona_detectada: Optional[str] = None
    todas_distancias: dict

# ========== ENDPOINTS ==========
@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "🚀 API Ferbel Motocicletas - DESPLEGADA EN RENDER",
        "version": "2.0.0",
        "status": "operacional",
        "database": "PostgreSQL (Render)",
        "endpoints": {
            "clientes": "/api/clientes",
            "motocicletas": "/api/motocicletas",
            "sucursales": "/api/sucursales",
            "recomendacion": "/api/recomendacion/domicilio?domicilio=TU_DIRECCION",
            "documentacion": "/docs",
            "estadisticas": "/api/estadisticas"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Endpoint de salud para verificar que la API está funcionando"""
    try:
        # Intentar conexión a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, 500

@app.get("/api/clientes", response_model=List[ClienteResponse])
async def obtener_clientes(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Obtiene lista de clientes"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM clientes 
            ORDER BY fecha_registro DESC 
            LIMIT %s OFFSET %s
        """, (limit, offset))
        
        clientes = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convertir a lista de diccionarios
        clientes_list = []
        for cliente in clientes:
            clientes_list.append({
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
        
        return clientes_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener clientes: {str(e)}")

@app.get("/api/clientes/{cliente_id}", response_model=ClienteResponse)
async def obtener_cliente(cliente_id: int):
    """Obtiene un cliente por ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM clientes WHERE id = %s", (cliente_id,))
        cliente = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        return {
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
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener cliente: {str(e)}")

@app.post("/api/clientes", response_model=ClienteResponse, status_code=201)
async def crear_cliente(cliente: ClienteBase):
    """Crea un nuevo cliente"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO clientes 
            (primer_nombre, segundo_nombre, primer_apellido, segundo_apellido, 
             email, domicilio, telefono, motocicleta_interes, sucursal)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, fecha_registro
        """, (
            cliente.primer_nombre,
            cliente.segundo_nombre,
            cliente.primer_apellido,
            cliente.segundo_apellido,
            cliente.email,
            cliente.domicilio,
            cliente.telefono,
            cliente.motocicleta_interes,
            cliente.sucursal
        ))
        
        nuevo_id, fecha_registro = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            **cliente.dict(),
            'id': nuevo_id,
            'fecha_registro': fecha_registro
        }
        
    except psycopg2.IntegrityError as e:
        if 'unique' in str(e).lower():
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        raise HTTPException(status_code=400, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear cliente: {str(e)}")

@app.get("/api/motocicletas", response_model=List[MotocicletaResponse])
async def obtener_motocicletas(
    marca: Optional[str] = None,
    tipo: Optional[str] = None
):
    """Obtiene lista de motocicletas con filtros opcionales"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM motocicletas WHERE 1=1"
        params = []
        
        if marca:
            query += " AND LOWER(marca) = LOWER(%s)"
            params.append(marca)
        
        if tipo:
            query += " AND LOWER(tipo) = LOWER(%s)"
            params.append(tipo)
        
        query += " ORDER BY marca, modelo"
        cursor.execute(query, params)
        
        motocicletas = cursor.fetchall()
        cursor.close()
        conn.close()
        
        motos_list = []
        for moto in motocicletas:
            motos_list.append({
                'id': moto[0],
                'marca': moto[1],
                'modelo': moto[2],
                'año': moto[3],
                'precio': float(moto[4]) if moto[4] else None,
                'tipo': moto[5]
            })
        
        return motos_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener motocicletas: {str(e)}")

@app.get("/api/sucursales", response_model=List[SucursalResponse])
async def obtener_sucursales():
    """Obtiene lista de sucursales"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM sucursales ORDER BY nombre")
        sucursales = cursor.fetchall()
        cursor.close()
        conn.close()
        
        sucursales_list = []
        for suc in sucursales:
            sucursales_list.append({
                'id': suc[0],
                'nombre': suc[1],
                'domicilio': suc[2],
                'marca': suc[3]
            })
        
        return sucursales_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener sucursales: {str(e)}")

@app.get("/api/recomendacion/domicilio", response_model=RecomendacionResponse)
async def recomendar_sucursal_domicilio(domicilio: str = Query(..., min_length=5)):
    """Recomienda sucursal para un domicilio específico"""
    return SimuladorGeolocalizacion.recomendar_sucursal(domicilio)

@app.get("/api/recomendacion/cliente/{cliente_id}")
async def recomendar_sucursal_cliente(cliente_id: int):
    """Recomienda sucursal para un cliente específico por ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT domicilio FROM clientes WHERE id = %s", (cliente_id,))
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not resultado:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        domicilio = resultado[0]
        recomendacion = SimuladorGeolocalizacion.recomendar_sucursal(domicilio)
        
        recomendacion['cliente_id'] = cliente_id
        return recomendacion
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al recomendar sucursal: {str(e)}")

@app.get("/api/estadisticas")
async def obtener_estadisticas():
    """Obtiene estadísticas del sistema"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total clientes
        cursor.execute("SELECT COUNT(*) FROM clientes")
        total_clientes = cursor.fetchone()[0]
        
        # Clientes por sucursal
        cursor.execute("""
            SELECT sucursal, COUNT(*) 
            FROM clientes 
            GROUP BY sucursal 
            ORDER BY COUNT(*) DESC
        """)
        clientes_por_sucursal = cursor.fetchall()
        
        # Motocicletas por marca
        cursor.execute("""
            SELECT marca, COUNT(*) 
            FROM motocicletas 
            GROUP BY marca 
            ORDER BY COUNT(*) DESC
        """)
        motos_por_marca = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "total_clientes": total_clientes,
            "clientes_por_sucursal": [
                {"sucursal": row[0], "cantidad": row[1]} 
                for row in clientes_por_sucursal
            ],
            "motocicletas_por_marca": [
                {"marca": row[0], "cantidad": row[1]} 
                for row in motos_por_marca
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")

# ========== INICIALIZACIÓN ==========
def init_database():
    """Inicializa la base de datos si es necesario"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si las tablas existen
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tablas = [tabla[0] for tabla in cursor.fetchall()]
        
        print(f"📊 Tablas existentes: {tablas}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"⚠️  Nota: {str(e)}")

# ========== EJECUCIÓN PRINCIPAL ==========
if __name__ == "__main__":
    # Inicializar base de datos
    init_database()
    
    # Obtener puerto de Render o usar 8000 por defecto
    port = int(os.environ.get("PORT", 8000))
    
    print("\n" + "="*60)
    print("🚀 INICIANDO API FERBEL MOTOCICLETAS EN RENDER")
    print("="*60)
    print(f"📡 Puerto asignado: {port}")
    print(f"🌐 Host: 0.0.0.0")
    print(f"🔗 Base de datos: {os.environ.get('DATABASE_URL', 'Local')[:30]}...")
    print("="*60)
    print("✅ Endpoints disponibles:")
    print(f"   • API: http://0.0.0.0:{port}/")
    print(f"   • Docs: http://0.0.0.0:{port}/docs")
    print(f"   • Health: http://0.0.0.0:{port}/health")
    print("="*60 + "\n")
    
    # Iniciar servidor
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False  # IMPORTANTE: False en producción
    )