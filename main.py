"""
Aplicación principal de Grafo Drawer
"""
import sys
import json
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt, QSettings, QRectF
from PyQt5.QtGui import QPainter, QKeySequence, QIcon, QImage
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QGraphicsView,
    QToolBar,
    QAction,
    QInputDialog,
    QMessageBox,
    QFileDialog,
    QTabWidget,
    QActionGroup,
    QMenuBar,
)

from utils import (
    DEFAULT_NODE_RADIUS,
    MAX_RECENT_FILES,
    SETTINGS_ORGANIZATION,
    SETTINGS_APPLICATION,
    MIN_ZOOM_LEVEL,
    MAX_ZOOM_LEVEL,
    load_icon,
    show_warning,
    show_info,
)
from graph_widgets import GraphScene, GraphView
from matrix_view import MatrixWidget


# -----------------------
# MainWindow
# -----------------------
class MainWindow(QMainWindow):
    """Ventana principal de la aplicación Grafo Drawer"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grafo Drawer")
        self.resize(1400, 900)
        
        # Escena que contiene el grafo
        self.scene = GraphScene()

        # Vista para visualizar e interactuar con la escena
        self.view = GraphView(self.scene)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        self.view.setFocusPolicy(Qt.StrongFocus)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.AnchorViewCenter)

        # Control de archivo y modificaciones
        self.current_file_path: Optional[str] = None
        self.is_modified = False
        self.scene.graph_changed.connect(self.set_modified)

        # Sistema de pestañas: Dibujo y Matriz
        self.tabs = QTabWidget()
        self.matrix_widget = MatrixWidget(self.scene)
        self.tabs.addTab(self.view, "Dibujo")
        self.tabs.addTab(self.matrix_widget, "Matriz de Adyacencia")
        self.setCentralWidget(self.tabs)

        # Crear interfaz
        self._create_vertical_toolbar()
        self._create_menu_bar()
        self._create_actions_shortcuts()
        
        # Iniciar en modo mover
        self.set_mode("move")
        self._apply_style()
        self.update_window_title()
        
        self.view.setFocus()

    def _create_vertical_toolbar(self):
        """Crea la barra de herramientas vertical con modos de interacción"""
        v_tb = QToolBar("Modos", self)
        v_tb.setObjectName("v_toolbar")
        v_tb.setMovable(False)
        v_tb.setFloatable(False)
        v_tb.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.addToolBar(Qt.LeftToolBarArea, v_tb)
        
        # Grupo exclusivo de modos (solo uno activo a la vez)
        mode_group = QActionGroup(self); mode_group.setExclusive(True)
        
        actions_data = [
            ("move", load_icon("move"), "Mover (P)\nArrastra nodos con clic izquierdo.\nMueve el lienzo con el botón central."),
            ("draw", load_icon("draw"), "Dibujar (D)\nCrea nodos al hacer clic en el lienzo."),
            ("edge", load_icon("edge"), "Aristas (E)\nClic en origen y destino para conectar."),
            ("edit", load_icon("edit"), "Editar (T)\nEdita etiquetas de nodos o pesos de aristas."),
            ("delete", load_icon("delete"), "Borrar (X)\nElimina nodos o aristas con un clic."),
        ]
        
        # Crear acción para cada modo
        for name, icon, tooltip in actions_data:
            act = QAction(icon if isinstance(icon, QIcon) else self.style().standardIcon(icon), name.capitalize(), self, checkable=True)
            act.triggered.connect(lambda _, n=name: self.set_mode(n))
            act.setToolTip(tooltip)
            mode_group.addAction(act)
            v_tb.addAction(act)
            setattr(self, f"act_{name}", act)
            
        self.act_move.setChecked(True)

        v_tb.addSeparator()
        
        # Controles de zoom
        self.zoom_in_action = QAction(load_icon("zoom_in"), "Aumentar Zoom", self)
        self.zoom_in_action.setToolTip("Aumentar zoom (Ctrl++)")
        self.zoom_in_action.triggered.connect(self.zoom_in)
        v_tb.addAction(self.zoom_in_action)

        self.zoom_out_action = QAction(load_icon("zoom_out"), "Disminuir Zoom", self)
        self.zoom_out_action.setToolTip("Disminuir zoom (Ctrl+-)")
        self.zoom_out_action.triggered.connect(self.zoom_out)
        v_tb.addAction(self.zoom_out_action)

    def _create_menu_bar(self):
        """Crea la barra de menú con todas las opciones"""
        menu_bar = self.menuBar()
        
        # Menú Archivo
        file_menu = menu_bar.addMenu("&Archivo")
        file_menu.addAction("Nuevo", self.new_file, "Ctrl+N")
        file_menu.addAction("Abrir...", self.open_file, "Ctrl+O")
        self.recent_files_menu = file_menu.addMenu("Abrir Recientes")
        self._update_recent_files_menu()
        file_menu.addSeparator()
        file_menu.addAction("Guardar", self.save_file, "Ctrl+S")
        file_menu.addAction("Guardar Como...", self.save_file_as, "Ctrl+Shift+S")
        file_menu.addSeparator()
        
        # Submenú de exportación
        export_menu = file_menu.addMenu("Exportar")
        export_menu.addAction("Grafo a JSON...", self.export_graph_to_json)
        export_menu.addAction("Dibujo a Imagen (PNG/JPG)...", self.export_scene_to_image)
        export_menu.addAction("Matriz a CSV...", self.matrix_widget.export_csv)
        export_menu.addAction("Matriz a JSON...", self.matrix_widget.export_json)
        file_menu.addSeparator()
        file_menu.addAction("Salir", self.close, "Ctrl+Q")

        # Menú Editar
        edit_menu = menu_bar.addMenu("&Editar")
        edit_menu.addAction("Borrar Selección", self.scene.delete_selected_items, "Del")
        edit_menu.addAction("Seleccionar Todo", self.scene.select_all_items, "Ctrl+A")
        edit_menu.addSeparator()
        edit_menu.addAction("Cambiar Tamaño de Nodos...", self.change_node_size_dialog)
        edit_menu.addAction("Aumentar Tamaño de Nodos", lambda: self._adjust_node_size(5), "Ctrl+Up")
        edit_menu.addAction("Disminuir Tamaño de Nodos", lambda: self._adjust_node_size(-5), "Ctrl+Down")
        
        # Menú Ver
        view_menu = menu_bar.addMenu("&Ver")
        view_menu.addAction("Ajustar a la Vista", self.fit_view_to_scene, "F")
        view_menu.addSeparator()

        self.zoom_in_action.setText("Aumentar Zoom")
        self.zoom_in_action.setShortcut("Ctrl++")
        view_menu.addAction(self.zoom_in_action)
        self.zoom_out_action.setText("Disminuir Zoom")
        self.zoom_out_action.setShortcut("Ctrl+-")
        view_menu.addAction(self.zoom_out_action)
        view_menu.addSeparator()
        
        # Opciones de fondo
        view_menu.addAction("Cargar Imagen de Fondo...", self.load_background_image)
        view_menu.addAction("Quitar Imagen de Fondo", self.remove_background_image)
        view_menu.addSeparator()
        
        # Toggles de visibilidad
        self.toggle_grid_action = QAction("Mostrar Cuadrícula", self, checkable=True)
        self.toggle_grid_action.setChecked(self.scene.grid_visible)
        self.toggle_grid_action.triggered.connect(self.scene.toggle_grid_visibility)
        view_menu.addAction(self.toggle_grid_action)
        
        self.toggle_weights_action = QAction("Mostrar Pesos de Aristas", self, checkable=True)
        self.toggle_weights_action.setChecked(True)
        self.toggle_weights_action.triggered.connect(self.toggle_edge_weights_visibility)
        view_menu.addAction(self.toggle_weights_action)

        view_menu.addSeparator()
        
        # Cambio entre pestañas
        tabs_group = QActionGroup(self); tabs_group.setExclusive(True)
        show_draw_action = QAction("Vista de Dibujo", self, checkable=True, triggered=lambda: self.tabs.setCurrentIndex(0))
        show_draw_action.setChecked(True)
        show_matrix_action = QAction("Vista de Matriz", self, checkable=True, triggered=self.show_matrix_tab, shortcut="M")
        view_menu.addAction(show_draw_action); view_menu.addAction(show_matrix_action)
        tabs_group.addAction(show_draw_action); tabs_group.addAction(show_matrix_action)
        
        # Menú Ayuda
        help_menu = menu_bar.addMenu("&Ayuda"); help_menu.addAction("Acerca de...", self.show_about_dialog)

    def _create_actions_shortcuts(self):
        """Asigna atajos de teclado a los modos"""
        self.act_move.setShortcut("P")
        self.act_draw.setShortcut("D")
        self.act_edge.setShortcut("E")
        self.act_edit.setShortcut("T")
        self.act_delete.setShortcut("X")
    
    def zoom_in(self):
        """Aumenta el zoom respetando el límite máximo"""
        current_scale = self.view.transform().m11()
        if current_scale * 1.15 <= MAX_ZOOM_LEVEL:
            self.view.scale(1.15, 1.15)

    def zoom_out(self):
        """Disminuye el zoom respetando el límite mínimo"""
        current_scale = self.view.transform().m11()
        if current_scale / 1.15 >= MIN_ZOOM_LEVEL:
            self.view.scale(1 / 1.15, 1 / 1.15)
        
    def set_mode(self, mode: str):
        """Cambia el modo de interacción con el grafo"""
        self.scene.set_mode(mode)
        mode_text = {"move": "Mover: Arrastra el lienzo y los nodos.", "draw": "Dibujo: Clic para crear nodos.",
                     "edge": "Aristas: Clic en origen y destino para conectar.", "edit": "Edición: Clic para editar.",
                     "delete": "Borrar: Clic para eliminar un elemento."}
        self.statusBar().showMessage(f"Modo: {mode_text.get(mode, mode)}")
        
        # Marcar acción correspondiente como activa
        action_map = {
            "move": self.act_move, "draw": self.act_draw,
            "edge": self.act_edge, "edit": self.act_edit,
            "delete": self.act_delete
        }
        if mode in action_map:
            action_map[mode].setChecked(True)

    def set_modified(self, modified=True):
        """Marca el documento como modificado (sin guardar)"""
        if self.is_modified == modified: return
        self.is_modified = modified
        self.update_window_title()

    def update_window_title(self):
        """Actualiza el título de la ventana mostrando nombre de archivo y estado"""
        title = "Grafo Drawer"
        if self.current_file_path: title = f"{Path(self.current_file_path).name} - {title}"
        if self.is_modified: title = f"*{title}"
        self.setWindowTitle(title)
        
    def _maybe_save(self) -> bool:
        """Pregunta si guardar cambios antes de una operación destructiva"""
        if not self.is_modified: return True
        ret = QMessageBox.warning(self, "Grafo Drawer", "Hay cambios sin guardar. ¿Desea guardarlos?",
                                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        if ret == QMessageBox.Save: return self.save_file()
        return ret != QMessageBox.Cancel

    def new_file(self):
        """Crea un nuevo grafo vacío"""
        if self._maybe_save():
            self.scene.clear_scene(keep_background=False)
            self.current_file_path = None
            self.set_modified(False)

    def open_file(self, path: Optional[str] = None):
        """Abre un archivo de grafo desde JSON"""
        if not self._maybe_save(): return
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Abrir grafo", "", "JSON Files (*.json)")
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as f: self.scene.load_graph_from_data(json.load(f), view=self.view)
            self.current_file_path = path
            self.set_modified(False)
            self.statusBar().showMessage(f"Grafo cargado: {path}")
            self.fit_view_to_scene()
            self._add_to_recent_files(path)
        except Exception as exc: show_warning("Error al abrir archivo", str(exc))

    def save_file(self) -> bool:
        """Guarda el grafo en el archivo actual"""
        if self.current_file_path is None: return self.save_file_as()
        try:
            with open(self.current_file_path, "w", encoding="utf-8") as f: json.dump(self.scene.get_graph_data(), f, indent=2)
            self.set_modified(False)
            self.statusBar().showMessage(f"Grafo guardado en: {self.current_file_path}")
            self._add_to_recent_files(self.current_file_path)
            return True
        except Exception as exc:
            show_warning("Error al guardar", str(exc))
            return False

    def save_file_as(self) -> bool:
        """Guarda el grafo con un nuevo nombre de archivo"""
        path, _ = QFileDialog.getSaveFileName(self, "Guardar grafo como...", "grafo_dirigido.json", "JSON Files (*.json)")
        if not path: return False
        self.current_file_path = path
        return self.save_file()
        
    def export_scene_to_image(self):
        """Exporta el dibujo del grafo a una imagen PNG o JPG"""
        if not self.scene.items():
            show_info("Exportar Imagen", "El lienzo está vacío. No hay nada que exportar.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Dibujo a Imagen",
            "grafo_dibujo.png",
            "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg)"
        )

        if not path:
            return

        # Calcular área a renderizar con padding
        rect = self.scene.itemsBoundingRect()
        padding = 50.0
        rect.adjust(-padding, -padding, padding, padding)

        # Crear imagen y pintor
        image = QImage(rect.size().toSize(), QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.white)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # Renderizar escena a imagen
        self.scene.render(painter, QRectF(image.rect()), rect)
        painter.end()

        try:
            if image.save(path):
                self.statusBar().showMessage(f"Dibujo exportado con éxito a: {path}")
            else:
                show_warning("Error al Exportar", f"No se pudo guardar la imagen en la ruta: {path}")
        except Exception as e:
            show_warning("Error al Exportar", f"Ocurrió un error inesperado: {str(e)}")

    def export_graph_to_json(self):
        """Exporta la estructura del grafo a JSON"""
        path, _ = QFileDialog.getSaveFileName(self, "Exportar grafo a JSON", "export_dirigido.json", "JSON Files (*.json)")
        if not path: return
        try:
            with open(path, "w", encoding="utf-8") as f: json.dump(self.scene.get_graph_data(), f, indent=2)
            self.statusBar().showMessage(f"Grafo exportado a: {path}")
        except Exception as exc: show_warning("Error al exportar", str(exc))

    def closeEvent(self, event):
        """Maneja el cierre de la aplicación"""
        if self._maybe_save(): event.accept()
        else: event.ignore()

    def _get_settings(self) -> QSettings:
        """Retorna objeto de configuración para persistir preferencias"""
        return QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)

    def _add_to_recent_files(self, file_path: str):
        """Agrega archivo a la lista de recientes"""
        settings = self._get_settings()
        files = settings.value("recent_files/files", [], type=str)
        if file_path in files: files.remove(file_path)
        files.insert(0, file_path)
        settings.setValue("recent_files/files", files[:MAX_RECENT_FILES])
        self._update_recent_files_menu()

    def _update_recent_files_menu(self):
        """Actualiza el menú de archivos recientes"""
        self.recent_files_menu.clear()
        files = self._get_settings().value("recent_files/files", [], type=str)
        for i, file in enumerate(files):
            action = QAction(f"&{i+1} {Path(file).name}", self, triggered=lambda _, f=file: self.open_file(f))
            self.recent_files_menu.addAction(action)
        if files: self.recent_files_menu.addSeparator()
        self.recent_files_menu.addAction("Limpiar lista", self._clear_recent_files)
        self.recent_files_menu.setEnabled(bool(files))

    def _clear_recent_files(self):
        """Limpia la lista de archivos recientes"""
        self._get_settings().remove("recent_files/files")
        self._update_recent_files_menu()

    def load_background_image(self):
        """Carga una imagen de fondo para el grafo"""
        fn, _ = QFileDialog.getOpenFileName(self, "Cargar imagen de fondo", "", "Imágenes (*.png *.jpg *.jpeg)")
        if fn and self.scene.set_background_image(fn, view=self.view): self.set_modified()

    def remove_background_image(self):
        """Elimina la imagen de fondo"""
        self.scene.remove_background_image()
        self.set_modified()
            
    def change_node_size_dialog(self):
        """Abre diálogo para cambiar el tamaño de todos los nodos"""
        from utils import DEFAULT_NODE_RADIUS
        val, ok = QInputDialog.getInt(self, "Tamaño de Nodos", "Radio (px):", DEFAULT_NODE_RADIUS, 10, 200, 1)
        if ok: self.scene.set_node_radius_all(val); self.set_modified()
            
    def _adjust_node_size(self, delta: int):
        """Ajusta el tamaño de nodos incrementalmente"""
        from utils import DEFAULT_NODE_RADIUS
        new_r = max(10, min(200, DEFAULT_NODE_RADIUS + delta))
        if new_r != DEFAULT_NODE_RADIUS: self.scene.set_node_radius_all(new_r); self.set_modified()

    def fit_view_to_scene(self):
        """Ajusta el zoom para que todos los elementos sean visibles"""
        if not self.scene.items(): 
            self.view.centerOn(0, 0)
            return
        items_rect = self.scene.itemsBoundingRect()
        # Incluir imagen de fondo si existe
        if self.scene.background_image_item: items_rect = items_rect.united(self.scene.background_image_item.sceneBoundingRect())
        self.view.fitInView(items_rect.adjusted(-50, -50, 50, 50), Qt.KeepAspectRatio)

    def show_matrix_tab(self):
        """Cambia a la pestaña de matriz de adyacencia"""
        self.tabs.setCurrentIndex(1)

    def show_about_dialog(self):
        """Muestra el diálogo Acerca de"""
        QMessageBox.about(self, "Acerca de Grafo Drawer", "<b>Grafo Drawer v1.0</b><br>"
                                                   "Herramienta para visualizar y editar grafos dirigidos.<br><br>"
                                                   "Creada con Python, PyQt5 y NetworkX.")
    
    def toggle_edge_weights_visibility(self, visible: bool):
        """Muestra u oculta los pesos de todas las aristas"""
        for edge in self.scene.edge_items:
            edge.set_text_visibility(visible)

    def wheelEvent(self, event):
        """Maneja zoom con Ctrl+rueda del mouse"""
        if event.modifiers() == Qt.ControlModifier:
            current_scale = self.view.transform().m11()
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            
            # Respetar límites de zoom
            if factor > 1 and current_scale * factor > MAX_ZOOM_LEVEL:
                return
            if factor < 1 and current_scale * factor < MIN_ZOOM_LEVEL:
                return
                
            self.view.scale(factor, factor)
        else:
            super().wheelEvent(event)

    def _apply_style(self):
        """Aplica estilos CSS personalizados a la interfaz"""
        self.setStyleSheet(f"""
            QMainWindow, QMenuBar {{ background-color: #2c3e50; color: #ecf0f1; }}
            QMenuBar::item {{ background-color: transparent; padding: 6px 12px; }}
            QMenuBar::item:selected {{ background-color: #34495e; }}
            QMenu {{ background-color: #34495e; color: #ecf0f1; border: 1px solid #2c3e50; }}
            QMenu::item:selected {{ background-color: #3498db; }}
            
            QToolBar {{
                background-color: #2c3e50;
                border-right: 1px solid #4a627a;
                spacing: 6px;
                padding: 4px;
            }}
            QToolBar QToolButton {{
                background-color: #3d5268;
                border: 1px solid #567;
                border-radius: 4px;
                padding: 5px;
            }}
            QToolBar QToolButton:hover {{
                background-color: #4a627a;
            }}
            QToolBar QToolButton:checked {{
                background-color: #3498db;
                border: 1px solid #55aaff;
            }}

            QTabWidget::pane {{ border-top: 2px solid #3498db; background: white; }}
            QTabWidget > QTabBar::tab {{ 
                background: #f0f0f0; 
                border: 1px solid #d0d0d0; 
                border-bottom: none; 
                padding: 8px 10px; 
                min-width: 120px;
                border-top-left-radius: 4px; 
                border-top-right-radius: 4px; 
                font-weight: bold; 
                color: #555; 
            }}
            QTabWidget > QTabBar::tab:selected {{ 
                background: #ffffff; 
                border-color: #3498db; 
                color: #2c3e50; 
            }}
            QStatusBar {{ background-color: #f0f0f0; color: #333; font-weight: bold; padding-left: 10px; }}
            QPushButton {{ background-color: #f0f4f8; border: 1px solid #d0d0d0; padding: 6px 12px; border-radius: 4px; }}
            QPushButton:hover {{ background-color: #e6eef8; border-color: #3498db; }}
        """)


def main():
    """Función principal que inicia la aplicación"""
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
