import sys
import sqlite3
import random

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QTabWidget,
    QLabel
)

from PySide6.QtCharts import (
    QChart,
    QChartView,
    QLineSeries,
    QValueAxis,
    QBarSeries,
    QBarSet,
    QBarCategoryAxis
)

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont


# =========================================================
# CLASE PRINCIPAL DEL SISTEMA HMI
# =========================================================
class IntegratedSystem(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("HMI: Telemetría + SQLite")
        self.resize(750, 520)

        # Ruta de la base de datos
        self.db_path = "hmi_telemetry.db"

        # Crear base de datos
        self.init_database()

        # =================================================
        # TABS PRINCIPALES
        # =================================================
        self.tabs = QTabWidget()

        self.tabs.addTab(
            self.crear_tab_adquisicion(),
            "📡 Adquisición en Vivo"
        )

        self.tabs.addTab(
            self.crear_tab_historico(),
            "📊 Histórico Máximo"
        )

        self.setCentralWidget(self.tabs)

        # =================================================
        # TIMER
        # =================================================
        self.timer = QTimer()
        self.timer.timeout.connect(self.adquirir_y_procesar)

        self.tiempo_x = 0

    # =====================================================
    # BASE DE DATOS SQLITE
    # =====================================================
    def init_database(self):
        """
        Crea la base de datos y la tabla si no existen.
        """

        try:
            with sqlite3.connect(self.db_path) as conn:

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS datos_sensor (

                        id INTEGER PRIMARY KEY AUTOINCREMENT,

                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

                        tiempo REAL,

                        lectura REAL
                    )
                """)

                conn.commit()

                print("Base de datos inicializada correctamente.")

        except sqlite3.Error as e:
            print("Error creando la base de datos:", e)

    # =====================================================
    # CONSULTA SQL DEL TALLER
    # =====================================================
    def query_top10_max(self):
        """
        Consulta SQL requerida:

        SELECT      -> Selecciona columnas
        WHERE       -> Filtra lecturas válidas
        ORDER BY    -> Ordena de mayor a menor
        LIMIT 10    -> Trae únicamente 10 registros
        """

        try:
            with sqlite3.connect(self.db_path) as conn:

                cursor = conn.execute("""
                    SELECT tiempo, lectura

                    FROM datos_sensor

                    WHERE lectura > 0

                    ORDER BY lectura DESC

                    LIMIT 10
                """)

                resultados = cursor.fetchall()

                return resultados

        except sqlite3.Error as e:
            print("Error realizando query:", e)
            return []

    # =====================================================
    # TAB 1 -> ADQUISICIÓN EN VIVO
    # =====================================================
    def crear_tab_adquisicion(self):

        # Serie de línea
        self.series_linea = QLineSeries()
        self.series_linea.setName("Lectura Sensor")

        # Chart principal
        self.chart_linea = QChart()
        self.chart_linea.addSeries(self.series_linea)
        self.chart_linea.setTitle("Monitoreo en Tiempo Real")

        # =========================
        # EJE X
        # =========================
        self.axis_x = QValueAxis()
        self.axis_x.setRange(0, 50)
        self.axis_x.setTitleText("Tiempo")

        self.chart_linea.addAxis(
            self.axis_x,
            Qt.AlignBottom
        )

        self.series_linea.attachAxis(self.axis_x)

        # =========================
        # EJE Y
        # =========================
        self.axis_y = QValueAxis()
        self.axis_y.setRange(0, 100)
        self.axis_y.setTitleText("Lectura")

        self.chart_linea.addAxis(
            self.axis_y,
            Qt.AlignLeft
        )

        self.series_linea.attachAxis(self.axis_y)

        # =========================
        # BOTÓN INICIAR
        # =========================
        self.btn_toggle = QPushButton(
            "▶ Iniciar Adquisición"
        )

        self.btn_toggle.setFixedHeight(40)

        self.btn_toggle.clicked.connect(
            self.toggle_adquisicion
        )

        # =========================
        # LABEL ESTADO
        # =========================
        self.lbl_estado = QLabel(
            "Estado: Sistema detenido"
        )

        self.lbl_estado.setAlignment(Qt.AlignCenter)

        # =========================
        # LAYOUT
        # =========================
        layout = QVBoxLayout()

        layout.addWidget(QChartView(self.chart_linea))
        layout.addWidget(self.lbl_estado)
        layout.addWidget(self.btn_toggle)

        widget = QWidget()
        widget.setLayout(layout)

        return widget

    # =====================================================
    # INICIAR / DETENER
    # =====================================================
    def toggle_adquisicion(self):

        if self.timer.isActive():

            self.timer.stop()

            self.btn_toggle.setText(
                "▶ Iniciar Adquisición"
            )

            self.lbl_estado.setText(
                "Estado: Sistema detenido"
            )

        else:

            self.timer.start(150)

            self.btn_toggle.setText(
                "⏹ Detener Adquisición"
            )

            self.lbl_estado.setText(
                "Estado: Adquiriendo datos..."
            )

    # =====================================================
    # ADQUISICIÓN + SQLITE
    # =====================================================
    def adquirir_y_procesar(self):

        # =========================================
        # GENERAR DATO SIMULADO
        # =========================================
        self.tiempo_x += 1

        valor_y = round(
            random.uniform(20, 80),
            2
        )

        # =========================================
        # AGREGAR AL GRÁFICO
        # =========================================
        self.series_linea.append(
            self.tiempo_x,
            valor_y
        )

        # Scroll horizontal automático
        if self.tiempo_x > 50:

            self.axis_x.setRange(
                self.tiempo_x - 50,
                self.tiempo_x
            )

        # =========================================
        # EVITAR ACUMULACIÓN EXCESIVA EN RAM
        # =========================================
        if self.series_linea.count() > 100:

            self.series_linea.removePoints(
                0,
                self.series_linea.count() - 100
            )

        # =========================================
        # GUARDAR EN SQLITE
        # =========================================
        try:

            with sqlite3.connect(self.db_path) as conn:

                conn.execute("""
                    INSERT INTO datos_sensor
                    (tiempo, lectura)

                    VALUES (?, ?)
                """, (self.tiempo_x, valor_y))

                conn.commit()

        except sqlite3.Error as e:
            print("Error guardando datos:", e)

        # =========================================
        # ACTUALIZAR LABEL
        # =========================================
        self.lbl_estado.setText(
            f"Estado: Adquiriendo | Último valor: {valor_y}"
        )

    # =====================================================
    # TAB 2 -> HISTÓRICO MÁXIMO
    # =====================================================
    def crear_tab_historico(self):

        # Chart de barras
        self.chart_barras = QChart()

        self.chart_barras.setTitle(
            "Top 10 Lecturas Máximas"
        )

        self.chart_view_barras = QChartView(
            self.chart_barras
        )

        # =========================================
        # BOTÓN CONSULTA
        # =========================================
        self.btn_cargar = QPushButton(
            "📂 Cargar Histórico Máximo"
        )

        self.btn_cargar.setFixedHeight(40)

        self.btn_cargar.clicked.connect(
            self.cargar_historico_maximo
        )

        # =========================================
        # LABEL
        # =========================================
        self.lbl_info = QLabel(
            "Presione el botón para consultar "
            "las 10 lecturas máximas."
        )

        self.lbl_info.setAlignment(Qt.AlignCenter)

        font = QFont()
        font.setItalic(True)

        self.lbl_info.setFont(font)

        # =========================================
        # LAYOUT
        # =========================================
        layout = QVBoxLayout()

        layout.addWidget(self.chart_view_barras)
        layout.addWidget(self.lbl_info)
        layout.addWidget(self.btn_cargar)

        widget = QWidget()
        widget.setLayout(layout)

        return widget

    # =====================================================
    # CARGAR HISTÓRICO
    # =====================================================
    def cargar_historico_maximo(self):

        resultados = self.query_top10_max()

        # =========================================
        # VALIDAR SI HAY DATOS
        # =========================================
        if not resultados:

            self.lbl_info.setText(
                "⚠ No existen datos almacenados."
            )

            return

        # =========================================
        # LIMPIAR CHART ANTERIOR
        # =========================================
        self.chart_barras.removeAllSeries()

        for axis in self.chart_barras.axes():
            self.chart_barras.removeAxis(axis)

        # =========================================
        # CREAR BARRAS
        # =========================================
        bar_set = QBarSet("Lecturas")

        # Color barras
        bar_set.setColor(QColor("#2E75B6"))

        categorias = []

        # =========================================
        # AGREGAR DATOS
        # =========================================
        for i, (tiempo, lectura) in enumerate(resultados):

            bar_set.append(round(lectura, 2))

            categorias.append(
                f"t={int(tiempo)}"
            )

        # =========================================
        # SERIES DE BARRAS
        # =========================================
        series_barras = QBarSeries()

        series_barras.append(bar_set)

        # Mostrar valores encima de barras
        series_barras.setLabelsVisible(True)

        self.chart_barras.addSeries(series_barras)

        # =========================================
        # EJE X
        # =========================================
        axis_x = QBarCategoryAxis()

        axis_x.append(categorias)

        axis_x.setTitleText(
            "Tiempo"
        )

        self.chart_barras.addAxis(
            axis_x,
            Qt.AlignBottom
        )

        series_barras.attachAxis(axis_x)

        # =========================================
        # EJE Y
        # =========================================
        max_valor = max(
            lectura for _, lectura in resultados
        )

        axis_y = QValueAxis()

        axis_y.setRange(
            0,
            max_valor * 1.15
        )

        axis_y.setTitleText(
            "Valor de Lectura"
        )

        self.chart_barras.addAxis(
            axis_y,
            Qt.AlignLeft
        )

        series_barras.attachAxis(axis_y)

        # =========================================
        # LABEL INFO
        # =========================================
        self.lbl_info.setText(
            f"✅ Se cargaron {len(resultados)} "
            f"lecturas máximas."
        )


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = IntegratedSystem()

    window.show()

    sys.exit(app.exec())