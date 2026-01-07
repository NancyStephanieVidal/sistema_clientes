"""
API REST con FastAPI para gestionar clientes, motocicletas y sucursales
Se ejecuta en puerto 8000 (Flask sigue en 5000)
"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import psycopg2
from datetime import datetime
import uvicorn

# Importar el módulo de geolocalización
from geolocalizacion import SimuladorGeolocalizacion

# Configuración de PostgreSQL (usa la misma que tu Flask)
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'sistema_clientes',
    'user': 'postgres',
    'password': 'postgres123'
}

# Inicializar FastAPI
app = FastAPI(
    title="API Ferbel Motocicletas",
    description="API REST para gestión de clientes, motocicletas y sucursales",
    version="1.0.0",
    docs_url="/docs",  # Documentación Swagger
    redoc_url="/redoc"  # Documentación Redoc
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

# ========== FUNCIONES DE CONEXIÓN ==========
def get_db_connection():
    """Conecta a PostgreSQL"""
    return psycopg2.connect(**POSTGRES_CONFIG)

# ========== ENDPOINTS DE CLIENTES ==========
@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "API Ferbel Motocicletas",
        "version": "1.0.0",
        "endpoints": {
            "clientes": "/api/clientes",
            "motocicletas": "/api/motocicletas",
            "sucursales": "/api/sucursales",
            "recomendacion": "/api/recomendacion"
        }
    }

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
        raise HTTPException(status_code=500, detail=str(e))

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
        raise HTTPException(status_code=500, detail=str(e))

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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== ENDPOINTS DE MOTOCICLETAS ==========
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
        raise HTTPException(status_code=500, detail=str(e))

# ========== ENDPOINTS DE SUCURSALES ==========
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
        raise HTTPException(status_code=500, detail=str(e))

# ========== ENDPOINTS DE RECOMENDACIÓN ==========
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
        
        # Añadir información del cliente
        recomendacion['cliente_id'] = cliente_id
        
        return recomendacion
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recomendacion/zonas")
async def obtener_zonas_mapeadas():
    """Obtiene todas las zonas mapeadas para geolocalización"""
    return {
        "zonas_mapeadas": list(SimuladorGeolocalizacion.ZONAS_COORDENADAS.keys()),
        "sucursales": SimuladorGeolocalizacion.SUCURSALES_GEO
    }

# ========== ESTADÍSTICAS ==========
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
        raise HTTPException(status_code=500, detail=str(e))

# ========== EJECUCIÓN ==========
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 INICIANDO API REST FERBEL MOTOCICLETAS")
    print("="*60)
    print("📡 API disponible en: http://localhost:8000")
    print("📚 Documentación: http://localhost:8000/docs")
    print("📊 Redoc: http://localhost:8000/redoc")
    print("="*60 + "\n")
    
    uvicorn.run(
        "api_fastapi:app",  # Cambiado a string
        host="0.0.0.0",
        port=8000,
        reload=True
    )