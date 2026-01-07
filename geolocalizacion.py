"""
Módulo para simular geolocalización y recomendar sucursales cercanas
"""
import re
from typing import Dict, List, Tuple

class SimuladorGeolocalizacion:
    """
    Simula la geolocalización usando palabras clave de colonias/zonas
    """
    
    # Mapeo de zonas a coordenadas simuladas
    ZONAS_COORDENADAS = {
        'coyoacan': (19.3294, -99.1617),
        'coapa': (19.2870, -99.1336),
        'naucalpan': (19.4785, -99.2373),
        'miguel hidalgo': (19.4158, -99.1830),
        'satelite': (19.5089, -99.2332),
        'patriotismo': (19.4064, -99.1792),
        'centro': (19.4326, -99.1332),
        'roma': (19.4189, -99.1616),
        'condesa': (19.4117, -99.1750),
        'polanco': (19.4332, -99.1946)
    }
    
    # Coordenadas simuladas de las sucursales (lat, lon)
    SUCURSALES_GEO = {
        'KTM Ferbel Coapa': (19.2870, -99.1336),
        'KTM Ferbel Satelite': (19.5089, -99.2332),
        'Yamaha Ferbel Patriotismo': (19.4064, -99.1792)
    }
    
    @classmethod
    def extraer_zonas(cls, domicilio: str) -> List[str]:
        """
        Extrae zonas/colonias del domicilio
        """
        domicilio_lower = domicilio.lower()
        zonas_encontradas = []
        
        for zona in cls.ZONAS_COORDENADAS.keys():
            if zona in domicilio_lower:
                zonas_encontradas.append(zona)
        
        return zonas_encontradas
    
    @staticmethod
    def calcular_distancia_simulada(coord1: Tuple[float, float], 
                                  coord2: Tuple[float, float]) -> float:
        """
        Calcula distancia simulada usando fórmula simplificada
        """
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Fórmula simplificada para simulación
        distancia = ((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) ** 0.5 * 100
        return round(distancia, 2)
    
    @classmethod
    def recomendar_sucursal(cls, domicilio: str) -> Dict:
        """
        Recomienda la sucursal más cercana basada en el domicilio
        """
        # Extraer zonas del domicilio
        zonas = cls.extraer_zonas(domicilio)
        
        if not zonas:
            return {
                'sucursal_recomendada': 'KTM Ferbel Coapa',
                'distancia_km': 'No determinada',
                'razon': 'No se pudo identificar zona en domicilio',
                'todas_distancias': {},
                'zona_detectada': None
            }
        
        # Tomar la primera zona encontrada como referencia
        zona_principal = zonas[0]
        coord_cliente = cls.ZONAS_COORDENADAS.get(zona_principal)
        
        if not coord_cliente:
            return {
                'sucursal_recomendada': 'KTM Ferbel Coapa',
                'distancia_km': 'No determinada',
                'razon': 'Zona no mapeada',
                'todas_distancias': {},
                'zona_detectada': zona_principal
            }
        
        # Calcular distancias a todas las sucursales
        distancias = {}
        for sucursal, coord_sucursal in cls.SUCURSALES_GEO.items():
            distancia = cls.calcular_distancia_simulada(coord_cliente, coord_sucursal)
            distancias[sucursal] = distancia
        
        # Encontrar la más cercana
        sucursal_cercana = min(distancias.items(), key=lambda x: x[1])
        
        return {
            'sucursal_recomendada': sucursal_cercana[0],
            'distancia_km': sucursal_cercana[1],
            'razon': f'Cliente en zona {zona_principal}',
            'todas_distancias': distancias,
            'zona_detectada': zona_principal
        }