"""
Módulo de categorías de pago a proveedor para MULTISERVICIOS LAS AMERICAS C.A.

Define la estructura de segmentación de pagos por categoría, modelo de moto
y ciclo de pago (A o B).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any


class CicloPago(Enum):
    """Enum para los ciclos de pago A y B."""
    A = "A"
    B = "B"


class CategoriaPago(Enum):
    """Enum para las categorías de pago a proveedor."""
    CAT1_ALTA_ROTACION = "1"  # Alta Rotación / "Lomito" (100% Contado)
    CAT2_FINANCIAMIENTO_60 = "2"  # Financiamiento a 60 Días
    CAT3_FINANCIAMIENTO_4M = "3"  # Financiamiento a 4 Meses (Prueba Limitada)


@dataclass
class ModeloMoto:
    """Modelo de moto asociado a una categoría."""
    nombre: str
    # Permitir agregar más atributos en el futuro


@dataclass
class CondicionPago:
    """Condiciones de pago para una categoría."""
    nombre: str
    # Categoría 1: 100% contado, no aplica financiamiento
    # Categoría 2: 30% inicial + 70% en 4 cuotas quincenales
    # Categoría 3: 30% inicial + 70% en 8 cuotas quincenales
    tipo: str  # "contado", "financiado_60", "financiado_4m"
    inicial_pct: float  # Porcentaje de inicial (0 para contado, 30 para los otros)
    total_cuotas: int  # Número total de cuotas
    cuotas_quincenales: bool  # Siempre quincenales


@dataclass
class ConfigCicloPago:
    """Configuración del ciclo de pago (días específicos del mes)."""
    ciclo: CicloPago
    dias_pago: List[int]  # Días del mes en que se pagan las cuotas
    descripcion: str


@dataclass
class CategoriaData:
    """Datos completos de una categoría de pago."""
    id: str
    nombre: str
    descripcion: str
    modelos: List[ModeloMoto]
    condicion: CondicionPago
    ciclos_disponibles: List[ConfigCicloPago]  # Puede tener 1 o 2 ciclos


@dataclass
class ProveedorMotos:
    """Estructura completa para un proveedor de motos."""
    nombre: str
    rfc_ou_identificacion: str = "MULTISERVICIOS LAS AMERICAS C.A"
    categorias: List[CategoriaData] = field(default_factory=list)


# Definición de las categorías para MULTISERVICIOS LAS AMERICAS C.A

# Categoría 1: Alta Rotación / "Lomito" (100% Contado)
categoria_1_modelos = [
    ModeloMoto(nombre="Socialista"),
    ModeloMoto(nombre="BWS"),
    ModeloMoto(nombre="Kavak"),
    ModeloMoto(nombre="DT 250"),
    ModeloMoto(nombre="GR 250"),
]

categoria_1 = CategoriaData(
    id=CategoriaPago.CAT1_ALTA_ROTACION.value,
    nombre="Categoría 1 – Alta Rotación / 'Lomito' (100% Contado)",
    descripcion="Venta exclusiva de contado / por asignación. No aplica financiamiento a plazos para asegurar la reposición inmediata de unidades.",
    modelos=categoria_1_modelos,
    condicion=CondicionPago(
        nombre="100% Contado",
        tipo="contado",
        inicial_pct=0.0,
        total_cuotas=0,
        cuotas_quincenales=False,
    ),
    ciclos_disponibles=[],
)

# Categoría 2: Financiamiento a 60 Días
categoria_2_modelos = [
    ModeloMoto(nombre="León"),
    ModeloMoto(nombre="BR200"),
    ModeloMoto(nombre="BRZ"),
    ModeloMoto(nombre="BRX"),
]

ciclo_a = ConfigCicloPago(
    ciclo=CicloPago.A,
    dias_pago=[3, 18],
    descripcion="Ciclo A: Días 3 y 18 de cada mes",
)

ciclo_b = ConfigCicloPago(
    ciclo=CicloPago.B,
    dias_pago=[10, 25],
    descripcion="Ciclo B: Días 10 y 25 de cada mes",
)

categoria_2 = CategoriaData(
    id=CategoriaPago.CAT2_FINANCIAMIENTO_60.value,
    nombre="Categoría 2 – Financiamiento a 60 Días",
    descripcion="30% de Inicial + Saldo en 4 cuotas quincenales. Las condiciones son variables; el cliente puede elegir el ciclo de pago.",
    modelos=categoria_2_modelos,
    condicion=CondicionPago(
        nombre="30% Inicial + 70% en 4 cuotas quincenales",
        tipo="financiado_60",
        inicial_pct=30.0,
        total_cuotas=4,
        cuotas_quincenales=True,
    ),
    ciclos_disponibles=[ciclo_a, ciclo_b],
)

# Categoría 3: Financiamiento a 4 Meses (Prueba Limitada)
categoria_3_modelos = [
    ModeloMoto(nombre="X1"),
    ModeloMoto(nombre="Milan"),
    ModeloMoto(nombre="Runner"),
    ModeloMoto(nombre="Cobra"),
    ModeloMoto(nombre="SBR (Caballito de hierro)"),
    ModeloMoto(nombre="BRF"),
]

categoria_3 = CategoriaData(
    id=CategoriaPago.CAT3_FINANCIAMIENTO_4M.value,
    nombre="Categoría 3 – Financiamiento a 4 Meses (Prueba Limitada)",
    descripcion="30% de Inicial + Saldo en 8 cuotas quincenales. Prueba limitada; la variabilidad de cuotas/porcentaje puede ajustarse en el futuro.",
    modelos=categoria_3_modelos,
    condicion=CondicionPago(
        nombre="30% Inicial + 70% en 8 cuotas quincenales",
        tipo="financiado_4m",
        inicial_pct=30.0,
        total_cuotas=8,
        cuotas_quincenales=True,
    ),
    ciclos_disponibles=[ciclo_a, ciclo_b],
)

# Proveedor principal
MULTISERVICIOS_LAS_AMERICAS = ProveedorMotos(
    nombre="MULTISERVICIOS LAS AMERICAS C.A",
    rfc_ou_identificacion="MULTISERVICIOS LAS AMERICAS C.A",
    categorias=[categoria_1, categoria_2, categoria_3],
)

# Mapeo de modelo a categoría para validación rápida
MODELO_A_CATEGORIA: Dict[str, str] = {}

# Categoría 1 modelos
for m in categoria_1_modelos:
    MODELO_A_CATEGORIA[m.nombre] = categoria_1.id

# Categoría 2 modelos
for m in categoria_2_modelos:
    MODELO_A_CATEGORIA[m.nombre] = categoria_2.id

# Categoría 3 modelos
for m in categoria_3_modelos:
    MODELO_A_CATEGORIA[m.nombre] = categoria_3.id


def obtener_categoria_por_modelo(nombre_modelo: str) -> str:
    """Obtiene el ID de la categoría por nombre de modelo."""
    return MODELO_A_CATEGORIA.get(nombre_modelo)


def obtener_categoria_por_id(cat_id: str) -> CategoriaData:
    """Obtiene los datos de una categoría por su ID."""
    for cat in MULTISERVICIOS_LAS_AMERICAS.categorias:
        if cat.id == cat_id:
            return cat
    return None


def obtener_ciclo_pago(categoria: CategoriaData, ciclo: CicloPago) -> ConfigCicloPago:
    """Obtiene la configuración del ciclo de pago para una categoría."""
    for c in categoria.ciclos_disponibles:
        if c.ciclo == ciclo:
            return c
    return None


# Datos de ejemplo para demostración
SIMULACION_DATOS = {
    "proveedor": MULTISERVICIOS_LAS_AMERICAS,
    "ultima_actualizacion": "2026-10-23",
}