"""
Widgets y componentes gráficos del grafo: NodeItem, EdgeItem, GraphScene, GraphView
"""
import math
from pathlib import Path
from typing import Optional, Dict, Set, Tuple, List

from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal, QLineF, QPoint
from PyQt5.QtGui import (
    QBrush,
    QPen,
    QFont,
    QPainter,
    QColor,
    QPixmap,
    QPainterPath,
    QPolygonF,
)
from PyQt5.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsTextItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QInputDialog,
    QFileDialog,
    QGraphicsItem,
    QWidget,
    QVBoxLayout,
    QGraphicsPathItem,
    QLabel,
)

import networkx as nx

from utils import (
    DEFAULT_NODE_RADIUS,
    FONT_NODE,
    FONT_EDGE,
    SCENE_FINITE_RECT,
    ARROW_SIZE,
    make_radial_brush,
    show_warning,
    show_info,
)


# -----------------------
# NodeItem
# -----------------------
class NodeItem(QGraphicsEllipseItem):
    """Representa un nodo visual del grafo como un círculo con etiqueta"""
    
    def __init__(self, node_id: int, label: str, pos: QPointF, radius: Optional[int] = None):
        self.radius = radius if radius is not None else DEFAULT_NODE_RADIUS
        # Crear elipse centrada en (0,0) con el radio especificado
        super().__init__(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)

        self.edges: Set["EdgeItem"] = set()  # Aristas conectadas a este nodo

        # Hacer el nodo seleccionable, movible y notificar cambios de geometría
        self.setFlags(
            QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

        self.id = node_id
        self.label = label

        # Texto centrado dentro del nodo
        self.text = QGraphicsTextItem(self.label, parent=self)
        self.text.setFont(FONT_NODE)
        self.text.setDefaultTextColor(Qt.white)
        self.update_text_position()

        self.setPos(pos)

        # Crear pinceles para estado normal y hover
        self._create_brushes()
        self.is_hovered = False
        self.setZValue(10)  # Mantener nodos sobre aristas

    def _create_brushes(self):
        """Crea los pinceles con gradiente radial para el nodo"""
        self.normal_brush = make_radial_brush(
            self.radius,
            (QColor(70, 130, 200), QColor(50, 100, 180), QColor(30, 80, 150)),
        )
        self.hover_brush = make_radial_brush(
            self.radius,
            (QColor(100, 160, 220), QColor(80, 140, 200), QColor(60, 120, 180)),
        )
        self.setBrush(self.normal_brush)
        pen = QPen(QColor(20, 50, 100))
        pen.setWidth(3)
        self.setPen(pen)

    def update_text_position(self):
        """Centra el texto dentro del círculo del nodo"""
        rect = self.text.boundingRect()
        self.text.setPos(-rect.width() / 2, -rect.height() / 2)

    def set_label(self, label: str):
        """Cambia la etiqueta del nodo"""
        self.label = label
        self.text.setPlainText(label)
        self.update_text_position()

    def hoverEnterEvent(self, event):
        """Cambia apariencia cuando el mouse entra al nodo"""
        self.setCursor(Qt.PointingHandCursor)
        self.setBrush(self.hover_brush)
        self.is_hovered = True
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Restaura apariencia cuando el mouse sale del nodo"""
        self.setCursor(Qt.ArrowCursor)
        self.setBrush(self.normal_brush)
        self.is_hovered = False
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        """Maneja cambios en el nodo (posición, selección, etc.)"""
        # Actualizar aristas conectadas cuando el nodo se mueve
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            for e in list(getattr(self, "edges", [])):
                try:
                    e.update_position()
                except Exception:
                    pass
            
            # Limitar movimiento dentro del rectángulo de la escena
            new_pos = value
            scene_rect = self.scene().sceneRect()
            
            left_limit = scene_rect.left() + self.radius
            right_limit = scene_rect.right() - self.radius
            top_limit = scene_rect.top() + self.radius
            bottom_limit = scene_rect.bottom() - self.radius

            clamped_x = max(left_limit, min(new_pos.x(), right_limit))
            clamped_y = max(top_limit, min(new_pos.y(), bottom_limit))
            
            return QPointF(clamped_x, clamped_y)

        # Mostrar/ocultar panel de información cuando se selecciona/deselecciona
        if change == QGraphicsItem.ItemSelectedChange and self.scene():
            will_be_selected = bool(value)
            view = self.scene().views()[0] if self.scene().views() else None
            if will_be_selected and view and hasattr(view, 'show_node_info_panel'):
                try:
                    view.show_node_info_panel(self)
                except Exception:
                    pass
            elif not will_be_selected and view and hasattr(view, 'hide_node_info_panel'):
                try:
                    view.hide_node_info_panel()
                except Exception:
                    pass

        return super().itemChange(change, value)

    def update_radius(self, new_radius: int):
        """Cambia el radio del nodo y actualiza todo lo relacionado"""
        self.radius = new_radius
        self.setRect(-new_radius, -new_radius, 2 * new_radius, 2 * new_radius)
        self._create_brushes()
        self.update_text_position()
        # Actualizar posición de aristas conectadas
        for e in list(self.edges):
            e.update_position()


# -----------------------
# EdgeItem
# -----------------------
class EdgeItem(QGraphicsPathItem):
    """Representa una arista dirigida entre dos nodos con peso opcional"""
    
    def __init__(self, source: NodeItem, dest: NodeItem, weight: Optional[str] = None):
        super().__init__()
        self.source = source
        self.dest = dest
        self.weight = weight if weight is not None else ""
        self.arrow_head = QPolygonF()  # Polígono para la flecha
        self.text_visible = True

        # Etiqueta de peso sobre un fondo blanco
        self.text = QGraphicsTextItem(str(self.weight), parent=self)
        self.text.setFont(FONT_EDGE)
        self.text.setDefaultTextColor(QColor(0, 0, 0))
        self.text.setZValue(2)
        self.text_bg = QGraphicsRectItem(parent=self)
        self.text_bg.setZValue(1)
        self.text_bg.setBrush(QBrush(QColor(255, 255, 255, 230)))
        self.text_bg.setPen(QPen(QColor(120, 120, 120), 1))

        # Estilos de línea para estado normal y hover
        self.normal_pen = QPen(QColor(80, 80, 80), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.hover_pen = QPen(QColor(200, 100, 100), 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.setPen(self.normal_pen)
        self.setZValue(-5)  # Mantener aristas detrás de nodos
        self.setAcceptHoverEvents(True)
        self.setFlags(QGraphicsItem.ItemIsSelectable)

        # Registrar esta arista en los nodos conectados
        self.source.edges.add(self)
        if self.source != self.dest:
             self.dest.edges.add(self)

        self.update_position()

    def boundingRect(self) -> QRectF:
        """Calcula el rectángulo que contiene toda la arista (línea + flecha + texto)"""
        base_rect = self.path().boundingRect()
        children_rect = self.childrenBoundingRect()
        arrow_rect = self.arrow_head.boundingRect()
        
        total_rect = base_rect.united(children_rect).united(arrow_rect)
        
        # Agregar padding para asegurar que todo sea visible
        padding = max(self.pen().widthF(), ARROW_SIZE) + 5
        return total_rect.adjusted(-padding, -padding, padding, padding)

    def is_loop(self) -> bool:
        """Verifica si la arista es un bucle (mismo nodo origen y destino)"""
        return self.source == self.dest

    def has_reverse_edge(self) -> bool:
        """Verifica si existe una arista en la dirección opuesta"""
        if self.is_loop():
            return False
        for edge in self.dest.edges:
            if edge.dest == self.source:
                return True
        return False

    def update_position(self):
        """Recalcula la trayectoria de la arista según posición de los nodos"""
        self.prepareGeometryChange()
        if self.is_loop():
            self._update_loop_path()
        else:
            self._update_directed_path()
        self._update_text_position()

    def _update_loop_path(self):
        """Crea un bucle curvo para aristas que conectan un nodo consigo mismo"""
        path = QPainterPath()
        node_pos = self.source.pos()
        r = self.source.radius
        
        # Definir ángulos para el inicio y fin del bucle
        angle_offset = 35
        start_angle_rad = math.radians(90 + angle_offset)
        end_angle_rad = math.radians(90 - angle_offset)
        
        start_point = node_pos + QPointF(r * math.cos(start_angle_rad), -r * math.sin(start_angle_rad))
        end_point = node_pos + QPointF(r * math.cos(end_angle_rad), -r * math.sin(end_angle_rad))
        
        # Punto de control para la curva del bucle
        loop_height = r * 1.6
        ctrl_point = node_pos + QPointF(0, -loop_height)
        
        path.moveTo(start_point)
        path.quadTo(ctrl_point, end_point)
        self.setPath(path)
        
        # Calcular flecha al final del bucle
        direction_line = QLineF(ctrl_point, end_point)
        self._calculate_arrow_head(end_point, direction_line)

    def _update_directed_path(self):
        """Crea la trayectoria para aristas normales entre dos nodos diferentes"""
        p1 = self.source.scenePos()
        p2 = self.dest.scenePos()
        line = QLineF(p1, p2)
        if line.length() == 0:
            return

        full_path = QPainterPath()
        full_path.moveTo(p1)

        # Si hay arista inversa, curvar la línea para evitar superposición
        ctrl_point = None
        if self.has_reverse_edge():
            dx, dy = p2.x() - p1.x(), p2.y() - p1.y()
            ctrl_offset = 30
            norm_len = line.length()
            if norm_len > 0:
                # Punto de control perpendicular a la línea
                ctrl_point = QPointF(
                    p1.x() + dx / 2 - dy / norm_len * ctrl_offset,
                    p1.y() + dy / 2 + dx / norm_len * ctrl_offset
                )
                full_path.quadTo(ctrl_point, p2)
            else:
                full_path.lineTo(p2)
        else:
            full_path.lineTo(p2)

        # Calcular intersecciones con los bordes de los nodos
        line_to_source = QLineF(full_path.pointAtPercent(0.1), full_path.pointAtPercent(0))
        line_to_dest = QLineF(full_path.pointAtPercent(0.9), full_path.pointAtPercent(1))
        
        intersect_p1 = self._get_intersection_point(line_to_source, self.source) or p1
        intersect_p2 = self._get_intersection_point(line_to_dest, self.dest) or p2

        # Crear trayectoria final desde borde a borde
        final_path = QPainterPath()
        final_path.moveTo(intersect_p1)
        if self.has_reverse_edge() and ctrl_point:
            final_path.quadTo(ctrl_point, intersect_p2)
        else:
            final_path.lineTo(intersect_p2)
        
        self.setPath(final_path)
        
        # Calcular dirección para la flecha
        if self.has_reverse_edge() and ctrl_point:
            direction_line = QLineF(ctrl_point, intersect_p2)
        else:
            direction_line = QLineF(intersect_p1, intersect_p2)
        self._calculate_arrow_head(intersect_p2, direction_line)

    def _calculate_arrow_head(self, end_point: QPointF, direction_line: QLineF):
        """Calcula los puntos del triángulo de la flecha según la dirección"""
        # Solo mostrar flecha en bucles o cuando hay arista inversa
        if not self.is_loop() and not self.has_reverse_edge():
            self.arrow_head = QPolygonF()
            return

        if direction_line.length() == 0:
            self.arrow_head = QPolygonF()
            return
            
        # Calcular ángulo de la línea
        angle = math.atan2(-direction_line.dy(), direction_line.dx())
        
        # Puntos de las "alas" del triángulo
        rev_angle = angle + math.pi
        wing_spread_angle = math.pi / 6
        
        p2_wing = end_point + QPointF(math.cos(rev_angle - wing_spread_angle) * ARROW_SIZE, 
                                      -math.sin(rev_angle - wing_spread_angle) * ARROW_SIZE)
        p3_wing = end_point + QPointF(math.cos(rev_angle + wing_spread_angle) * ARROW_SIZE, 
                                      -math.sin(rev_angle + wing_spread_angle) * ARROW_SIZE)
        
        self.arrow_head = QPolygonF([end_point, p2_wing, p3_wing])

    def _get_intersection_point(self, line: QLineF, node: NodeItem) -> Optional[QPointF]:
        """Calcula el punto donde la línea intersecta el círculo del nodo"""
        circle_center = node.scenePos()
        line_p1, line_p2 = line.p1(), line.p2()
        dx, dy = line_p2.x() - line_p1.x(), line_p2.y() - line_p1.y()
        
        # Resolver ecuación cuadrática para intersección línea-círculo
        a = dx**2 + dy**2
        if a == 0: return None
        b = 2 * (dx * (line_p1.x() - circle_center.x()) + dy * (line_p1.y() - circle_center.y()))
        c = (line_p1.x() - circle_center.x())**2 + (line_p1.y() - circle_center.y())**2 - node.radius**2
        delta = b**2 - 4 * a * c
        if delta < 0: return None
        
        t1 = (-b + math.sqrt(delta)) / (2 * a)
        t2 = (-b - math.sqrt(delta)) / (2 * a)

        # Filtrar puntos dentro del segmento [0,1]
        points = []
        if 0 <= t1 <= 1: points.append(line_p1 + t1 * (line_p2 - line_p1))
        if 0 <= t2 <= 1: points.append(line_p1 + t2 * (line_p2 - line_p1))

        if not points: return None
        if len(points) == 1: return points[0]
        # Retornar el punto más cercano al destino
        return min(points, key=lambda p: QLineF(p, line_p2).length())

    def _update_text_position(self):
        """Posiciona la etiqueta de peso en el punto medio de la arista"""
        if not self.text_visible:
            return

        if self.is_loop():
            # Para bucles, colocar texto arriba del arco
            r = self.source.radius
            loop_height = r * 1.6
            mid_point = self.source.pos() + QPointF(0, -loop_height - 15)
        else:
            mid_point = self.path().pointAtPercent(0.5)

        text_rect = self.text.boundingRect()
        text_pos = mid_point - QPointF(text_rect.width() / 2, text_rect.height() / 2)
        self.text.setPos(text_pos)

        # Fondo blanco con padding alrededor del texto
        padding = 4
        bg_rect = QRectF(text_pos, text_rect.size()).adjusted(-padding, -padding, padding, padding)
        self.text_bg.setRect(bg_rect)

    def paint(self, painter, option, widget=None):
        """Dibuja la línea de la arista y la flecha"""
        painter.setPen(self.pen())
        painter.drawPath(self.path())
        
        # Dibujar flecha si existe
        if not self.arrow_head.isEmpty():
            painter.setPen(QPen(self.pen().color(), 1))
            painter.setBrush(self.pen().color())
            painter.drawPolygon(self.arrow_head)

    def set_weight(self, weight: str):
        """Cambia el peso de la arista"""
        self.weight = weight
        self.text.setPlainText(str(weight))
        self.update_position()

    def set_text_visibility(self, visible: bool):
        """Muestra u oculta la etiqueta de peso"""
        self.text_visible = visible
        self.text.setVisible(visible)
        self.text_bg.setVisible(visible)
        if visible:
            self.update_position()
        self.update()

    def hoverEnterEvent(self, event):
        """Resalta la arista cuando el mouse entra"""
        self.setPen(self.hover_pen)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Restaura estilo normal cuando el mouse sale"""
        self.setPen(self.normal_pen)
        super().hoverLeaveEvent(event)


# -----------------------
# GraphScene
# -----------------------
class GraphScene(QGraphicsScene):
    """Escena que contiene y gestiona todos los nodos y aristas del grafo"""
    
    graph_changed = pyqtSignal()  # Señal emitida cuando el grafo cambia

    def __init__(self):
        super().__init__()
        self.mode = "draw"  # Modo de interacción: draw, edge, delete, edit, move
        self.node_counter = 0  # Contador para IDs únicos de nodos
        self.node_items: Dict[int, NodeItem] = {}  # Diccionario id -> NodeItem
        self.edge_items: Set[EdgeItem] = set()  # Conjunto de todas las aristas
        self.edge_mode_first_node: Optional[NodeItem] = None  # Primer nodo al crear arista
        self.temp_line: Optional[QGraphicsLineItem] = None  # Línea temporal en modo edge
        self.background_image_item: Optional[QGraphicsPixmapItem] = None  # Imagen de fondo
        self.G = nx.DiGraph()  # Grafo dirigido de NetworkX para algoritmos
        self.background_image_path: Optional[str] = None
        self.grid_visible = True  # Mostrar/ocultar cuadrícula
        
        self.setSceneRect(SCENE_FINITE_RECT)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        """Dibuja el fondo con cuadrícula opcional"""
        super().drawBackground(painter, rect)
        
        # Solo dibujar cuadrícula si no hay imagen de fondo
        if not self.background_image_item and self.grid_visible:
            minor_grid_color = QColor(240, 240, 240)
            major_grid_color = QColor(220, 220, 220)
            minor_step, major_step = 20, 100
            minor_pen, major_pen = QPen(minor_grid_color, 1), QPen(major_grid_color, 2)
            left, right, top, bottom = int(rect.left()), int(rect.right()), int(rect.top()), int(rect.bottom())
            
            # Líneas menores
            first_left, first_top = left - (left % minor_step), top - (top % minor_step)
            painter.setPen(minor_pen)
            for x in range(first_left, right, minor_step): painter.drawLine(x, top, x, bottom)
            for y in range(first_top, bottom, minor_step): painter.drawLine(left, y, right, y)
            
            # Líneas mayores
            painter.setPen(major_pen)
            first_left_major, first_top_major = left - (left % major_step), top - (top % major_step)
            for x in range(first_left_major, right, major_step): painter.drawLine(x, top, x, bottom)
            for y in range(first_top_major, bottom, major_step): painter.drawLine(left, y, right, y)

        # Borde del área de trabajo
        scene_rect = self.sceneRect()
        border_pen = QPen(QColor(180, 180, 180), 5, Qt.DashLine)
        painter.setPen(border_pen)
        painter.drawRect(scene_rect)

    def toggle_grid_visibility(self, visible: bool):
        """Muestra u oculta la cuadrícula de fondo"""
        self.grid_visible = visible
        self.update()

    def set_background_image(self, image_path: str, view: Optional[QGraphicsView] = None) -> bool:
        """Carga una imagen como fondo del grafo"""
        try:
            p = Path(image_path)
            if not p.exists(): raise FileNotFoundError(f"Archivo no encontrado: {image_path}")
            pixmap = QPixmap(str(p))
            if pixmap.isNull(): raise ValueError("No se pudo leer la imagen (formato inválido).")

            if self.background_image_item:
                self.removeItem(self.background_image_item)

            self.background_image_item = QGraphicsPixmapItem(pixmap)
            self.background_image_item.setZValue(-100)  # Detrás de todo
            self.addItem(self.background_image_item)
            self.background_image_path = image_path
            
            # Ajustar área de la escena al tamaño de la imagen
            image_rect = QRectF(pixmap.rect())
            self.setSceneRect(image_rect)
            self.background_image_item.setPos(0, 0)

            self.update()
            return True
        except Exception as exc:
            show_warning("Error al cargar imagen", str(exc))
            return False

    def remove_background_image(self):
        """Elimina la imagen de fondo"""
        if self.background_image_item:
            self.removeItem(self.background_image_item)
            self.background_image_item = None
            self.background_image_path = None
            self.setSceneRect(SCENE_FINITE_RECT)
            self.update()

    def set_mode(self, mode: str):
        """Cambia el modo de interacción con el grafo"""
        self.mode = mode
        # Limpiar estado temporal del modo edge
        if mode != "edge":
            if self.edge_mode_first_node:
                self.edge_mode_first_node.setBrush(self.edge_mode_first_node.normal_brush)
                self.edge_mode_first_node = None
            if self.temp_line:
                self.removeItem(self.temp_line)
                self.temp_line = None
        
        if self.views():
            self.views()[0].setDragMode(QGraphicsView.RubberBandDrag)
            
        # Permitir movimiento de nodos en todos los modos
        for node in self.node_items.values():
            node.setFlag(QGraphicsItem.ItemIsMovable, True)

    def _logical_item_from(self, items_list):
        """Obtiene el item lógico (NodeItem o EdgeItem) de una lista de items gráficos"""
        for it in items_list:
            if isinstance(it, (NodeItem, EdgeItem)): return it
            parent = it.parentItem()
            if isinstance(parent, (NodeItem, EdgeItem)): return parent
        return None

    def mousePressEvent(self, event):
        """Maneja clics según el modo activo"""
        pos = event.scenePos()
        
        # Ignorar clics fuera del área de trabajo
        if not self.sceneRect().contains(pos):
             if not self._logical_item_from(self.items(pos)):
                self.clearSelection()
             super().mousePressEvent(event)
             return

        top = self._logical_item_from(self.items(pos))

        if self.mode == "draw":
            # Crear nodo si no se hizo clic sobre uno existente
            if not isinstance(top, NodeItem): self.create_node(pos)
        
        elif self.mode == "edge":
            # Modo de creación de aristas: seleccionar nodo origen y destino
            if isinstance(top, NodeItem):
                if self.edge_mode_first_node is None:
                    # Primer nodo: resaltar y esperar segundo clic
                    self.edge_mode_first_node = top
                    highlight = make_radial_brush(top.radius, (QColor(255, 220, 120), QColor(255, 180, 80), QColor(220, 140, 40)))
                    top.setBrush(highlight)
                    # Línea temporal para visualizar la conexión
                    self.temp_line = QGraphicsLineItem()
                    pen = QPen(QColor(255, 100, 100), 3, Qt.DashLine)
                    self.temp_line.setPen(pen)
                    self.temp_line.setZValue(10)
                    self.addItem(self.temp_line)
                    start = top.scenePos()
                    self.temp_line.setLine(start.x(), start.y(), pos.x(), pos.y())
                else:
                    # Segundo nodo: crear arista
                    self.create_edge(self.edge_mode_first_node, top)
                    self.edge_mode_first_node.setBrush(self.edge_mode_first_node.normal_brush)
                    if self.temp_line: self.removeItem(self.temp_line)
                    self.temp_line = None
                    self.edge_mode_first_node = None
            else:
                # Clic fuera de nodo: cancelar operación
                if self.edge_mode_first_node:
                    self.edge_mode_first_node.setBrush(self.edge_mode_first_node.normal_brush)
                self.edge_mode_first_node = None
                if self.temp_line: self.removeItem(self.temp_line)
                self.temp_line = None

        elif self.mode == "delete":
            # Eliminar nodo o arista bajo el cursor
            if isinstance(top, NodeItem): self.delete_node(top)
            elif isinstance(top, EdgeItem): self.delete_edge(top)

        elif self.mode == "edit":
            # Editar etiqueta de nodo o peso de arista
            if isinstance(top, NodeItem): self._edit_node_label(top)
            elif isinstance(top, EdgeItem): self._edit_edge_weight(top)

        # Limpiar selección si se hizo clic en vacío
        if not isinstance(top, (NodeItem, EdgeItem)) and self.mode != 'move':
             self.clearSelection()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Actualiza línea temporal en modo edge mientras se mueve el mouse"""
        if self.mode == "edge" and self.temp_line and self.edge_mode_first_node:
            start = self.edge_mode_first_node.scenePos()
            p = event.scenePos()
            self.temp_line.setLine(start.x(), start.y(), p.x(), p.y())
        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Doble clic para editar nodos o aristas rápidamente"""
        top = self._logical_item_from(self.items(event.scenePos()))
        if isinstance(top, NodeItem): self._edit_node_label(top)
        elif isinstance(top, EdgeItem): self._edit_edge_weight(top)
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        """Maneja atajos de teclado"""
        from PyQt5.QtGui import QKeySequence
        if event.key() == Qt.Key_Delete:
            self.delete_selected_items()
        elif event.matches(QKeySequence.SelectAll):
            self.select_all_items()
        elif event.key() == Qt.Key_D and event.modifiers() == Qt.ControlModifier:
             self.clearSelection()
        else:
            super().keyPressEvent(event)
    
    def delete_selected_items(self):
        """Elimina todos los items seleccionados"""
        selected_edges = [item for item in self.selectedItems() if isinstance(item, EdgeItem)]
        selected_nodes = [item for item in self.selectedItems() if isinstance(item, NodeItem)]

        # Eliminar aristas primero para evitar referencias inválidas
        for item in selected_edges:
            self.delete_edge(item)
        for item in selected_nodes:
            self.delete_node(item)
            
    def select_all_items(self):
        """Selecciona todos los nodos"""
        for node in self.node_items.values():
            node.setSelected(True)

    def _edit_node_label(self, node: NodeItem):
        """Abre diálogo para editar la etiqueta de un nodo"""
        text, ok = QInputDialog.getText(None, "Editar etiqueta", "Etiqueta de nodo:", text=node.label)
        if ok:
            node.set_label(text)
            if node.id in self.G.nodes:
                self.G.nodes[node.id]["label"] = text
                self.graph_changed.emit()

    def _edit_edge_weight(self, edge: EdgeItem):
        """Abre diálogo para editar el peso de una arista"""
        text, ok = QInputDialog.getText(None, "Editar peso", "Peso:", text=str(edge.weight))
        if ok:
            edge.set_weight(text)
            a, b = edge.source.id, edge.dest.id
            if self.G.has_edge(a, b):
                self.G[a][b]["weight"] = text
                self.graph_changed.emit()

    def create_node(self, pos: QPointF, label: Optional[str] = None, radius: Optional[int] = None) -> NodeItem:
        """Crea un nuevo nodo en la posición especificada"""
        from utils import DEFAULT_NODE_RADIUS
        # Buscar ID único
        nid = self.node_counter
        while nid in self.node_items:
            nid += 1
            
        label_text = label if label is not None else f"{nid}"
        node = NodeItem(nid, label_text, pos, radius=radius if radius is not None else DEFAULT_NODE_RADIUS)
        node.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.addItem(node)
        self.node_items[nid] = node
        self.G.add_node(nid, label=label_text)
        self.node_counter = max(self.node_counter, nid + 1)
        self.graph_changed.emit()
        return node

    def create_edge(self, source: NodeItem, dest: NodeItem, weight: Optional[str] = None) -> Optional[EdgeItem]:
        """Crea una nueva arista entre dos nodos"""
        a, b = source.id, dest.id
        # Evitar aristas duplicadas en la misma dirección
        if self.G.has_edge(a, b):
            show_info("Arista existente", "Ya existe una arista en esta dirección.")
            return None

        # Solicitar peso si no se proporcionó
        if weight is None:
            text, ok = QInputDialog.getText(None, "Peso de la arista", "Ingrese el peso:", text="1")
            if not ok: return None
            weight_val = text
        else:
            weight_val = weight

        edge = EdgeItem(source, dest, weight_val)
        
        # Respetar visibilidad global de pesos
        main_window = self.views()[0].window()
        if hasattr(main_window, 'toggle_weights_action'):
            is_visible = main_window.toggle_weights_action.isChecked()
            edge.set_text_visibility(is_visible)

        self.addItem(edge)
        self.edge_items.add(edge)
        self.G.add_edge(a, b, weight=weight_val)
        
        # Actualizar arista inversa si existe
        for other_edge in dest.edges:
            if other_edge.dest == source:
                other_edge.update_position()
                break
        
        self.graph_changed.emit()
        return edge

    def delete_node(self, node: NodeItem):
        """Elimina un nodo y todas sus aristas conectadas"""
        nid = node.id
        # Eliminar todas las aristas conectadas primero
        for e in list(node.edges):
            self.delete_edge(e)
        
        if node in self.items():
            self.removeItem(node)
        
        self.node_items.pop(nid, None)
        if self.G.has_node(nid):
            self.G.remove_node(nid)
        self.graph_changed.emit()

    def delete_edge(self, edge: EdgeItem):
        """Elimina una arista del grafo"""
        a, b = edge.source, edge.dest
        
        # Desregistrar arista de los nodos
        edge.source.edges.discard(edge)
        if not edge.is_loop():
            edge.dest.edges.discard(edge)
            
        if edge in self.items():
            self.removeItem(edge)
        self.edge_items.discard(edge)
        if self.G.has_edge(a.id, b.id):
            self.G.remove_edge(a.id, b.id)
        
        # Actualizar arista inversa si existe
        if not edge.is_loop():
             for rev_edge in b.edges:
                  if rev_edge.dest == a:
                       rev_edge.update_position()
                       break

        self.graph_changed.emit()

    def clear_scene(self, keep_background: bool = True):
        """Limpia todos los nodos y aristas del grafo"""
        for e in list(self.edge_items): self.removeItem(e)
        self.edge_items.clear()
        for n in list(self.node_items.values()): self.removeItem(n)
        self.node_items.clear()
        self.G.clear()
        self.node_counter = 0
        if not keep_background: self.remove_background_image()
        self.graph_changed.emit()

    def get_graph_data(self) -> dict:
        """Serializa el grafo a un diccionario para guardar"""
        data = {"nodes": [], "edges": [], "background": self.background_image_path}
        if self.background_image_item:
            data["background_pos"] = [self.background_image_item.x(), self.background_image_item.y()]
            data["background_scale"] = self.background_image_item.scale()
        # Guardar información de cada nodo
        for nid, node in self.node_items.items():
            p = node.scenePos()
            data["nodes"].append({"id": nid, "label": node.label, "x": p.x(), "y": p.y(), "radius": node.radius})
        # Guardar información de cada arista
        for e in self.edge_items:
            data["edges"].append({"a": e.source.id, "b": e.dest.id, "weight": e.weight})
        return data

    def load_graph_from_data(self, data: dict, view: Optional[QGraphicsView] = None):
        """Carga un grafo desde un diccionario serializado"""
        from utils import DEFAULT_NODE_RADIUS
        self.clear_scene(keep_background=False)
        nodes_data = data.get("nodes", [])
        
        temp_node_map = {}
        max_id = -1
        
        # Recrear todos los nodos
        for n_data in nodes_data:
            nid = int(n_data["id"])
            pos = QPointF(float(n_data.get("x", 0)), float(n_data.get("y", 0)))
            label = n_data.get("label", str(nid))
            radius = int(n_data.get("radius", DEFAULT_NODE_RADIUS))
            
            node = NodeItem(nid, label, pos, radius)
            node.setFlag(QGraphicsItem.ItemIsMovable, True)
            self.addItem(node)
            temp_node_map[nid] = node
            self.G.add_node(nid, label=label)
            max_id = max(max_id, nid)
        
        self.node_items = temp_node_map
        self.node_counter = max_id + 1

        # Recrear todas las aristas
        for ed_data in data.get("edges", []):
            a, b = int(ed_data["a"]), int(ed_data["b"])
            if a in self.node_items and b in self.node_items:
                self.create_edge(self.node_items[a], self.node_items[b], ed_data.get("weight", ""))
        
        # Restaurar imagen de fondo si existe
        bg_path = data.get("background")
        if bg_path and self.set_background_image(bg_path, view=view):
            pass

        self.graph_changed.emit()
    
    def set_node_radius_all(self, new_radius: int):
        """Cambia el radio de todos los nodos existentes"""
        from utils import DEFAULT_NODE_RADIUS
        import utils
        utils.DEFAULT_NODE_RADIUS = new_radius
        for n in self.node_items.values():
            n.update_radius(new_radius)

    def to_matrix(self) -> Tuple[List[int], List[List[str]]]:
        """Convierte el grafo a una matriz de adyacencia"""
        nodes = sorted(self.G.nodes())
        n = len(nodes)
        mat: List[List[str]] = [["0" for _ in range(n)] for _ in range(n)]
        idx = {node: i for i, node in enumerate(nodes)}
        # Llenar matriz con los pesos de las aristas
        for a, b, data in self.G.edges(data=True):
            if a in idx and b in idx:
                i, j = idx[a], idx[b]
                w_str = str(data.get("weight", "1"))
                mat[i][j] = w_str
        return nodes, mat


# -----------------------
# GraphView para paneo con botón central
# -----------------------
class GraphView(QGraphicsView):
    """Vista del grafo con funcionalidades de paneo y panel de información"""
    
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self._panning = False  # Estado de paneo con botón central
        self._last_pan_point = QPoint()
        
        # Panel flotante para mostrar información del nodo seleccionado
        self._info_panel = QWidget(self)
        self._info_panel.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 240);
                border: 2px solid #3498db;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        self._info_panel.hide()
        
        # Contenido del panel
        panel_layout = QVBoxLayout(self._info_panel)
        panel_layout.setContentsMargins(8, 8, 8, 8)
        
        self._info_text = QLabel(self._info_panel)
        self._info_text.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                color: #2c3e50;
                font-family: 'Segoe UI', Arial;
                font-size: 11px;
            }
        """)
        self._info_text.setTextFormat(Qt.RichText)
        self._info_text.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self._info_text.setWordWrap(True)
        
        panel_layout.addWidget(self._info_text)
        self._info_panel.setFixedWidth(280)
        
        self._current_node = None
        self._position_info_panel()
        
    def resizeEvent(self, event):
        """Reposiciona el panel cuando cambia el tamaño de la vista"""
        super().resizeEvent(event)
        self._position_info_panel()
        
    def _position_info_panel(self):
        """Posiciona el panel en la esquina superior izquierda con margen"""
        margin = 15
        self._info_panel.move(margin, margin)
        
    def show_node_info_panel(self, node: NodeItem):
        """Muestra el panel con información del nodo seleccionado"""
        self._current_node = node
        text = self._build_node_info_text(node)
        self._info_text.setText(text)
        
        # Ajustar tamaño del panel al contenido
        self._info_text.adjustSize()
        self._info_panel.adjustSize()
        
        self._info_panel.show()
        self._info_panel.raise_()
        
    def hide_node_info_panel(self):
        """Oculta el panel de información"""
        self._info_panel.hide()
        self._current_node = None
        
    def _build_node_info_text(self, node: NodeItem) -> str:
        """Construye el texto HTML con información del nodo y sus conexiones"""
        scene = self.scene()
        nid = node.id
        
        # Obtener aristas entrantes y salientes
        if nid not in scene.G.nodes:
            out_edges = [(e.dest.id, e.weight) for e in node.edges if e.source == node]
            in_edges = [(e.source.id, e.weight) for e in node.edges if e.dest == node]
        else:
            out_edges = [(b, scene.G[nid][b].get("weight", "")) for b in scene.G.successors(nid)]
            in_edges = [(a, scene.G[a][nid].get("weight", "")) for a in scene.G.predecessors(nid)]

        lines = [
            f"<div style='font-size: 13px; margin-bottom: 8px;'><b>Nodo:</b> {nid} — <i>{node.label}</i></div>",
        ]
        
        # Listar aristas salientes
        if out_edges:
            lines.append("<div style='margin-top: 6px;'><b>Salientes:</b></div>")
            for b, w in out_edges:
                lbl = scene.node_items[b].label if b in scene.node_items else str(b)
                lines.append(f"<div style='margin-left: 8px;'>→ {b} ({lbl}) — peso: {w}</div>")
        else:
            lines.append("<div style='margin-top: 6px;'><b>Salientes:</b> (ninguno)</div>")

        # Listar aristas entrantes
        if in_edges:
            lines.append("<div style='margin-top: 6px;'><b>Entrantes:</b></div>")
            for a, w in in_edges:
                lbl = scene.node_items[a].label if a in scene.node_items else str(a)
                lines.append(f"<div style='margin-left: 8px;'>← {a} ({lbl}) — peso: {w}</div>")
        else:
            lines.append("<div style='margin-top: 6px;'><b>Entrantes:</b> (ninguno)</div>")

        return "".join(lines)

    def mousePressEvent(self, event):
        """Inicia paneo con el botón central del mouse"""
        if event.button() == Qt.MidButton:
            self._panning = True
            self._last_pan_point = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Realiza paneo mientras se mantiene presionado el botón central"""
        if self._panning:
            delta = event.pos() - self._last_pan_point
            # Mover barras de scroll según el movimiento del mouse
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self._last_pan_point = event.pos()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Finaliza paneo al soltar el botón central"""
        if event.button() == Qt.MidButton:
            self._panning = False
            self.setCursor(Qt.ArrowCursor) 
            event.accept()
            return
        super().mouseReleaseEvent(event)
