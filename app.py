import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFileDialog,
)
from PyQt6.QtGui import QPainter, QColor, QPen, QPolygonF, QAction
from PyQt6.QtCore import Qt, QPointF
import xml.etree.ElementTree as ET
from xml.dom import minidom

try:
    from reportlab.pdfgen import canvas as pdfcanvas
except ImportError:  # reportlab might not be installed until runtime
    pdfcanvas = None


class GridWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cell_size = 40
        self.cols = 20
        self.rows = 15
        self.width = self.cell_size * self.cols
        self.height = self.cell_size * self.rows
        self.setFixedSize(self.width, self.height)
        self.shapes = []  # list of dicts with keys: type, x, y
        self.cursor_x = 0
        self.cursor_y = 0
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.white)

        pen = QPen(QColor("lightgray"))
        painter.setPen(pen)
        for i in range(self.cols + 1):
            x = i * self.cell_size
            painter.drawLine(x, 0, x, self.height)
        for j in range(self.rows + 1):
            y = j * self.cell_size
            painter.drawLine(0, y, self.width, y)

        painter.setBrush(QColor("black"))
        for shape in self.shapes:
            x = shape["x"] * self.cell_size
            y = shape["y"] * self.cell_size
            if shape["type"] == "square":
                painter.drawRect(x, y, self.cell_size, self.cell_size)
            else:
                points = [
                    QPointF(x + self.cell_size / 2, y),
                    QPointF(x + self.cell_size, y + self.cell_size),
                    QPointF(x, y + self.cell_size),
                ]
                painter.drawPolygon(QPolygonF(points))

        pen = QPen(QColor("red"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(
            self.cursor_x * self.cell_size,
            self.cursor_y * self.cell_size,
            self.cell_size,
            self.cell_size,
        )

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Left and self.cursor_x > 0:
            self.cursor_x -= 1
        elif key == Qt.Key.Key_Right and self.cursor_x < self.cols - 1:
            self.cursor_x += 1
        elif key == Qt.Key.Key_Up and self.cursor_y > 0:
            self.cursor_y -= 1
        elif key == Qt.Key.Key_Down and self.cursor_y < self.rows - 1:
            self.cursor_y += 1
        elif key == Qt.Key.Key_S:
            self.place_square()
        elif key == Qt.Key.Key_T:
            self.place_triangle()
        self.update()

    def place_square(self):
        self.shapes.append({"type": "square", "x": self.cursor_x, "y": self.cursor_y})

    def place_triangle(self):
        self.shapes.append({"type": "triangle", "x": self.cursor_x, "y": self.cursor_y})

    def save_svg(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save as SVG", "", "SVG files (*.svg)"
        )
        if not filename:
            return
        svg = ET.Element(
            "svg",
            width=str(self.width),
            height=str(self.height),
            xmlns="http://www.w3.org/2000/svg",
            version="1.1",
        )
        for i in range(self.cols + 1):
            x = i * self.cell_size
            ET.SubElement(
                svg,
                "line",
                x1=str(x),
                y1="0",
                x2=str(x),
                y2=str(self.height),
                stroke="lightgray",
                **{"stroke-width": "1"}
            )
        for j in range(self.rows + 1):
            y = j * self.cell_size
            ET.SubElement(
                svg,
                "line",
                x1="0",
                y1=str(y),
                x2=str(self.width),
                y2=str(y),
                stroke="lightgray",
                **{"stroke-width": "1"}
            )
        for shape in self.shapes:
            x = shape["x"] * self.cell_size
            y = shape["y"] * self.cell_size
            if shape["type"] == "square":
                ET.SubElement(
                    svg,
                    "rect",
                    x=str(x),
                    y=str(y),
                    width=str(self.cell_size),
                    height=str(self.cell_size),
                    fill="black",
                )
            else:
                points = [
                    f"{x + self.cell_size / 2},{y}",
                    f"{x + self.cell_size},{y + self.cell_size}",
                    f"{x},{y + self.cell_size}",
                ]
                ET.SubElement(
                    svg, "polygon", points=" ".join(points), fill="black"
                )
        dom = minidom.parseString(ET.tostring(svg))
        with open(filename, "w", encoding="utf-8") as f:
            f.write(dom.toprettyxml())

    def save_pdf(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save as PDF", "", "PDF files (*.pdf)"
        )
        if not filename:
            return
        if pdfcanvas is None:
            raise RuntimeError("reportlab is required for PDF export")
        c = pdfcanvas.Canvas(filename, pagesize=(self.width, self.height))
        for i in range(self.cols + 1):
            x = i * self.cell_size
            c.line(x, 0, x, self.height)
        for j in range(self.rows + 1):
            y = j * self.cell_size
            y_pdf = self.height - y
            c.line(0, y_pdf, self.width, y_pdf)
        for shape in self.shapes:
            x = shape["x"] * self.cell_size
            y = shape["y"] * self.cell_size
            if shape["type"] == "square":
                y_pdf = self.height - y - self.cell_size
                c.rect(x, y_pdf, self.cell_size, self.cell_size, fill=1)
            else:
                p = c.beginPath()
                p.moveTo(x + self.cell_size / 2, self.height - y)
                p.lineTo(x + self.cell_size, self.height - y - self.cell_size)
                p.lineTo(x, self.height - y - self.cell_size)
                p.close()
                c.drawPath(p, fill=1)
        c.save()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grid Editor")
        self.grid = GridWidget()
        self.setCentralWidget(self.grid)
        file_menu = self.menuBar().addMenu("File")
        svg_action = QAction("Save as SVG", self)
        svg_action.triggered.connect(self.grid.save_svg)
        file_menu.addAction(svg_action)
        pdf_action = QAction("Save as PDF", self)
        pdf_action.triggered.connect(self.grid.save_pdf)
        file_menu.addAction(pdf_action)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
