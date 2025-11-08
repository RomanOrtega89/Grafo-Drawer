"""
Widget de visualización de matriz de adyacencia
"""
import math
import json
import statistics
from typing import List, Dict
from collections import Counter

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush, QPixmap, QPainter, QLinearGradient, QIcon
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QCheckBox,
    QFileDialog,
    QApplication,
)

from utils import show_warning, show_info, _mix_color


# -----------------------
# MatrixWidget
# -----------------------
class MatrixWidget(QWidget):
    """Widget que muestra la matriz de adyacencia del grafo con opciones de visualización y exportación"""
    
    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.scene = scene  # Referencia a la escena del grafo
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        # Fila de controles: botón refrescar y checkboxes
        hl = QHBoxLayout()
        self.btn_refresh = QPushButton("Refrescar Matriz")
        self.chk_labels = QCheckBox("Mostrar Etiquetas (id:label)")
        self.chk_heatmap = QCheckBox("Mostrar Heatmap")
        self.chk_heatmap.setChecked(True)  # Heatmap activado por defecto
        hl.addWidget(self.btn_refresh); hl.addWidget(self.chk_labels); hl.addWidget(self.chk_heatmap); hl.addStretch()
        self.layout.addLayout(hl)

        # Sección de estadísticas de pesos
        stats_layout = QHBoxLayout()
        self.stats_label = QPushButton(flat=True, enabled=False)
        self.stats_label.setStyleSheet("border: none; text-align: left; padding: 8px; background: #f8f9fa; border-radius: 4px; font-family: 'Segoe UI'; font-size: 12px; color: #495057;")
        stats_layout.addWidget(self.stats_label); stats_layout.addStretch()
        self.layout.addLayout(stats_layout)
        
        # Leyenda del gradiente de colores del heatmap
        legend_h = QHBoxLayout()
        self.legend_pix_label = QPushButton(flat=True, enabled=False, styleSheet="border: none; padding: 0px;")
        self.legend_label_widget = QPushButton(flat=True, enabled=False, styleSheet="border: none; text-align: left; padding-left: 6px;")
        legend_h.addWidget(self.legend_pix_label); legend_h.addWidget(self.legend_label_widget); legend_h.addStretch()
        self.layout.addLayout(legend_h)

        # Tabla que muestra la matriz de adyacencia
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # Solo lectura
        self.table.setAlternatingRowColors(True)
        css = ("QTableWidget { gridline-color: #e6e6e6; font-family: 'Segoe UI', Arial; }"
               "QHeaderView::section { background: #f0f4f8; padding: 6px; font-weight: bold; border: 1px solid #d0d0d0; }")
        self.table.setStyleSheet(css)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

        # Conectar señales a sus manejadores
        self.btn_refresh.clicked.connect(self.refresh_matrix)
        self.chk_labels.stateChanged.connect(self.refresh_matrix)
        self.chk_heatmap.stateChanged.connect(self.refresh_matrix)
        self.table.cellDoubleClicked.connect(self.copy_cell_to_clipboard)
        scene.graph_changed.connect(self.refresh_matrix)  # Actualizar cuando el grafo cambie

        self.refresh_matrix()

    def _make_header_labels(self, nodes: List[int]) -> List[str]:
        """Genera las etiquetas para los encabezados de filas/columnas"""
        if not self.chk_labels.isChecked(): return [str(x) for x in nodes]
        # Formato "id:etiqueta" si está activada la opción
        return [f"{n}:{self.scene.node_items.get(n).label}" if n in self.scene.node_items else str(n) for n in nodes]

    def _parse_weight(self, w: str) -> float:
        """Convierte un peso de texto a número flotante"""
        try: return float(str(w).strip().replace(",", "."))
        except (ValueError, TypeError): return 1.0  # Peso por defecto si falla la conversión

    def _update_legend(self, vmin: float, vmax: float, color_low: QColor, color_high: QColor):
        """Actualiza la leyenda visual del gradiente de colores del heatmap"""
        width, height = 240, 18
        pix = QPixmap(width, height)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        # Crear gradiente lineal de color_low a color_high
        lg = QLinearGradient(0, 0, width, 0)
        lg.setColorAt(0.0, color_low); lg.setColorAt(1.0, color_high)
        painter.fillRect(0, 0, width, height, lg)
        painter.end()
        self.legend_pix_label.setIcon(QIcon(pix)); self.legend_pix_label.setIconSize(pix.size())
        self.legend_label_widget.setText(f"Rango de pesos: {vmin:.2f} → {vmax:.2f}")

    def _calculate_statistics(self, mat: List[List[str]]) -> Dict[str, float]:
        """Calcula estadísticas (media, mediana, moda) de los pesos de las aristas"""
        # Extraer todos los pesos no cero
        weights = [self._parse_weight(mat[i][j]) for i in range(len(mat)) for j in range(len(mat)) if mat[i][j] != "0"]
        if not weights: return {"mean": 0, "median": 0, "mode": 0, "count": 0}
        try:
            counter = Counter(weights)
            mode_val = counter.most_common(1)[0][0] if counter else 0.0
            return {"mean": round(statistics.mean(weights), 3), "median": round(statistics.median(weights), 3),
                    "mode": round(mode_val, 3), "count": len(weights)}
        except Exception: return {"mean": 0, "median": 0, "mode": 0, "count": len(weights)}

    def _update_statistics_display(self, stats: Dict[str, float]):
        """Actualiza el texto que muestra las estadísticas de los pesos"""
        if stats["count"] == 0: self.stats_label.setText("📊 Estadísticas: No hay aristas con peso")
        else: self.stats_label.setText(f"📊 Estadísticas de pesos: Media = {stats['mean']}, "
                                      f"Mediana = {stats['median']}, Moda = {stats['mode']}, "
                                      f"Total aristas = {stats['count']}")
    
    def refresh_matrix(self):
        """Regenera y actualiza la visualización de la matriz de adyacencia"""
        # Obtener matriz desde la escena
        nodes, mat = self.scene.to_matrix()
        n = len(nodes)
        
        # Actualizar estadísticas
        self._update_statistics_display(self._calculate_statistics(mat))
        
        # Configurar dimensiones de la tabla
        self.table.clear()
        self.table.setRowCount(n); self.table.setColumnCount(n)
        headers = self._make_header_labels(nodes)
        self.table.setHorizontalHeaderLabels(headers); self.table.setVerticalHeaderLabels(headers)

        # Calcular rango de valores para el heatmap
        numeric_values = [self._parse_weight(mat[i][j]) for i in range(n) for j in range(n) if mat[i][j] != "0"]
        vmin, vmax = (min(numeric_values), max(numeric_values)) if numeric_values else (0.0, 1.0)
        if math.isclose(vmin, vmax): vmax = vmin + 1.0  # Evitar división por cero

        # Actualizar o limpiar la leyenda según el estado del heatmap
        if self.chk_heatmap.isChecked() and numeric_values:
            self._update_legend(vmin, vmax, QColor(245, 245, 250), QColor(85, 65, 118))
        else:
            self.legend_pix_label.setIcon(QIcon()); self.legend_label_widget.setText("")

        # Llenar cada celda de la tabla
        for i in range(n):
            for j in range(n):
                w = str(mat[i][j])
                item = QTableWidgetItem(w)
                item.setTextAlignment(Qt.AlignCenter)
                # Tooltip con información de la arista
                lbl_i = self.scene.node_items.get(nodes[i]).label if nodes[i] in self.scene.node_items else ""
                lbl_j = self.scene.node_items.get(nodes[j]).label if nodes[j] in self.scene.node_items else ""
                item.setToolTip(f"Arista: ({lbl_i}) → ({lbl_j})\nPeso: {w}")

                # Aplicar color de heatmap si está activado
                if self.chk_heatmap.isChecked() and w != "0":
                    val = self._parse_weight(w)
                    t = (val - vmin) / (vmax - vmin) if vmax > vmin else 0.0  # Normalizar entre 0 y 1
                    bg = _mix_color(QColor(245, 245, 250), QColor(85, 65, 118), t)
                    item.setBackground(bg)
                    # Ajustar color de texto según luminosidad del fondo
                    lum = (0.299 * bg.red() + 0.587 * bg.green() + 0.114 * bg.blue())
                    item.setForeground(QColor("white" if lum < 140 else "black"))
                self.table.setItem(i, j, item)
                
    def export_csv(self):
        """Exporta la matriz de adyacencia a un archivo CSV"""
        nodes, mat = self.scene.to_matrix()
        if not nodes: return show_info("Exportar CSV", "La matriz está vacía.")
        fn, _ = QFileDialog.getSaveFileName(self, "Exportar matriz (CSV)", "matriz_dirigida.csv", "CSV Files (*.csv)")
        if not fn: return
        try:
            with open(fn, "w", encoding="utf-8-sig") as f:
                # Escribir metadatos como comentario
                stats = self._calculate_statistics(mat)
                f.write(f"# Matriz de Adyacencia Dirigida (Nodos: {len(nodes)}, Aristas: {stats['count']})\n")
                # Escribir encabezados
                header_labels = self._make_header_labels(nodes)
                f.write("," + ",".join(f'"{h}"' for h in header_labels) + "\n")
                # Escribir cada fila con su etiqueta
                for i, _ in enumerate(nodes):
                    row_header = f'"{header_labels[i]}"'
                    f.write(f"{row_header},{','.join(str(mat[i][j]) for j in range(len(nodes)))}\n")
            show_info("Exportar CSV", f"Matriz exportada con éxito: {fn}")
        except Exception as exc: show_warning("Error al exportar CSV", str(exc))

    def export_json(self):
        """Exporta la matriz de adyacencia a un archivo JSON"""
        nodes, mat = self.scene.to_matrix()
        if not nodes: return show_info("Exportar JSON", "La matriz está vacía.")
        fn, _ = QFileDialog.getSaveFileName(self, "Exportar matriz (JSON)", "matriz_dirigida.json", "JSON Files (*.json)")
        if not fn: return
        try:
            with open(fn, "w", encoding="utf-8") as f:
                # Estructura JSON con nodos y matriz
                json.dump({"nodes": self._make_header_labels(nodes), "matrix": mat}, f, ensure_ascii=False, indent=2)
            show_info("Exportar JSON", f"Matriz exportada: {fn}")
        except Exception as exc: show_warning("Error al exportar JSON", str(exc))

    def copy_cell_to_clipboard(self, row: int, column: int):
        """Copia el valor de una celda al portapapeles al hacer doble clic"""
        it = self.table.item(row, column)
        if it: QApplication.clipboard().setText(it.text())
