"""
Utilidades y constantes para Grafo Drawer
"""
from pathlib import Path
from typing import Tuple
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QBrush, QFont, QRadialGradient, QColor, QIcon
from PyQt5.QtWidgets import QMessageBox

# -----------------------
# Constantes
# -----------------------
# Radio por defecto para dibujar nodos en píxeles
DEFAULT_NODE_RADIUS = 40

# Fuentes para texto de nodos y aristas
FONT_NODE = QFont("Arial", 12, QFont.Bold)
FONT_EDGE = QFont("Arial", 11, QFont.Bold)

# Rectángulo que limita el área de dibujo del canvas
SCENE_FINITE_RECT = QRectF(-7500, -7500, 15000, 15000)

# Número máximo de archivos recientes a recordar
MAX_RECENT_FILES = 5

# Configuración para guardar preferencias de la aplicación
SETTINGS_ORGANIZATION = "GraphDrawer"
SETTINGS_APPLICATION = "GraphDrawerApp"

# Tamaño de las flechas en las aristas dirigidas
ARROW_SIZE = 20

# Límites de zoom: 10% mínimo, 1000% máximo
MIN_ZOOM_LEVEL = 0.1  # 10%
MAX_ZOOM_LEVEL = 10.0  # 1000%

# Directorio donde se encuentran los iconos SVG de la aplicación
ICONS_DIR = Path(__file__).parent / "icons"


# -----------------------
# Funciones Helper
# -----------------------

def load_icon(name: str) -> QIcon:
    """
    Carga un icono desde la carpeta icons/
    Si no tiene extensión, asume .svg automáticamente
    """
    p = ICONS_DIR / name
    # Si no tiene extensión, agregar .svg
    if not p.suffix:
        p = p.with_suffix(".svg")
    if p.exists():
        return QIcon(str(p))
    # Retornar icono vacío si no existe para evitar errores
    return QIcon()


def make_radial_brush(radius: float, center_colors: Tuple[QColor, ...]) -> QBrush:
    """
    Crea un pincel con gradiente radial para efectos visuales
    Los colores se interpolan desde el centro hacia afuera
    """
    grad = QRadialGradient(0, 0, max(1.0, radius))
    n = len(center_colors)
    # Distribuir colores uniformemente en el gradiente
    for i, c in enumerate(center_colors):
        grad.setColorAt(i / max(1, n - 1), c)
    return QBrush(grad)


def show_warning(title: str, text: str):
    """Muestra un cuadro de diálogo de advertencia."""
    QMessageBox.warning(None, title, text)


def show_info(title: str, text: str):
    """Muestra un cuadro de diálogo de información."""
    QMessageBox.information(None, title, text)


def _mix_color(c1: QColor, c2: QColor, t: float) -> QColor:
    """
    Interpola dos colores según el parámetro t (0.0 a 1.0)
    t=0 retorna c1, t=1 retorna c2, valores intermedios mezclan ambos
    """
    # Limitar t entre 0 y 1
    t = max(0.0, min(1.0, t))
    # Interpolar cada canal RGB
    r = int(round(c1.red() * (1 - t) + c2.red() * t))
    g = int(round(c1.green() * (1 - t) + c2.green() * t))
    b = int(round(c1.blue() * (1 - t) + c2.blue() * t))
    return QColor(r, g, b)
