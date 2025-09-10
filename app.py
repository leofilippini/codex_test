import tkinter as tk
from tkinter import filedialog
import xml.etree.ElementTree as ET
from xml.dom import minidom

try:
    from reportlab.pdfgen import canvas as pdfcanvas
except ImportError:  # reportlab might not be installed until runtime
    pdfcanvas = None


class GridEditor:
    def __init__(self, root):
        self.root = root
        self.cell_size = 40
        self.cols = 20
        self.rows = 15
        self.width = self.cell_size * self.cols
        self.height = self.cell_size * self.rows
        self.canvas = tk.Canvas(root, width=self.width, height=self.height, bg="white")
        self.canvas.pack()
        self.shapes = []  # list of dicts with keys: type, x, y

        self._draw_grid()
        self.cursor_x = 0
        self.cursor_y = 0
        self.cursor = self.canvas.create_rectangle(0, 0, self.cell_size, self.cell_size,
                                                   outline="red", width=2)

        root.bind('<Left>', self._move_left)
        root.bind('<Right>', self._move_right)
        root.bind('<Up>', self._move_up)
        root.bind('<Down>', self._move_down)
        root.bind('s', self._place_square)
        root.bind('S', self._place_square)
        root.bind('t', self._place_triangle)
        root.bind('T', self._place_triangle)

        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Save as SVG", command=self.save_svg)
        filemenu.add_command(label="Save as PDF", command=self.save_pdf)
        menubar.add_cascade(label="File", menu=filemenu)
        root.config(menu=menubar)

    def _draw_grid(self):
        for i in range(self.cols + 1):
            x = i * self.cell_size
            self.canvas.create_line(x, 0, x, self.height, fill="lightgray")
        for j in range(self.rows + 1):
            y = j * self.cell_size
            self.canvas.create_line(0, y, self.width, y, fill="lightgray")

    def _update_cursor(self):
        x1 = self.cursor_x * self.cell_size
        y1 = self.cursor_y * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        self.canvas.coords(self.cursor, x1, y1, x2, y2)

    def _move_left(self, event):
        if self.cursor_x > 0:
            self.cursor_x -= 1
            self._update_cursor()

    def _move_right(self, event):
        if self.cursor_x < self.cols - 1:
            self.cursor_x += 1
            self._update_cursor()

    def _move_up(self, event):
        if self.cursor_y > 0:
            self.cursor_y -= 1
            self._update_cursor()

    def _move_down(self, event):
        if self.cursor_y < self.rows - 1:
            self.cursor_y += 1
            self._update_cursor()

    def _place_square(self, event=None):
        x = self.cursor_x * self.cell_size
        y = self.cursor_y * self.cell_size
        self.canvas.create_rectangle(x, y, x + self.cell_size, y + self.cell_size, fill="black")
        self.shapes.append({"type": "square", "x": self.cursor_x, "y": self.cursor_y})

    def _place_triangle(self, event=None):
        x = self.cursor_x * self.cell_size
        y = self.cursor_y * self.cell_size
        points = [
            x + self.cell_size / 2, y,
            x + self.cell_size, y + self.cell_size,
            x, y + self.cell_size,
        ]
        self.canvas.create_polygon(points, fill="black")
        self.shapes.append({"type": "triangle", "x": self.cursor_x, "y": self.cursor_y})

    def save_svg(self):
        filename = filedialog.asksaveasfilename(defaultextension=".svg",
                                                filetypes=[("SVG files", "*.svg")])
        if not filename:
            return
        svg = ET.Element('svg', width=str(self.width), height=str(self.height),
                         xmlns="http://www.w3.org/2000/svg", version="1.1")
        for i in range(self.cols + 1):
            x = i * self.cell_size
            ET.SubElement(svg, 'line', x1=str(x), y1="0", x2=str(x), y2=str(self.height),
                          stroke="lightgray", **{'stroke-width': "1"})
        for j in range(self.rows + 1):
            y = j * self.cell_size
            ET.SubElement(svg, 'line', x1="0", y1=str(y), x2=str(self.width), y2=str(y),
                          stroke="lightgray", **{'stroke-width': "1"})
        for shape in self.shapes:
            x = shape["x"] * self.cell_size
            y = shape["y"] * self.cell_size
            if shape["type"] == "square":
                ET.SubElement(svg, 'rect', x=str(x), y=str(y),
                              width=str(self.cell_size), height=str(self.cell_size),
                              fill="black")
            else:
                points = [
                    f"{x + self.cell_size / 2},{y}",
                    f"{x + self.cell_size},{y + self.cell_size}",
                    f"{x},{y + self.cell_size}"
                ]
                ET.SubElement(svg, 'polygon', points=" ".join(points), fill="black")
        dom = minidom.parseString(ET.tostring(svg))
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(dom.toprettyxml())

    def save_pdf(self):
        filename = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                filetypes=[("PDF files", "*.pdf")])
        if not filename:
            return
        if pdfcanvas is None:
            raise RuntimeError("reportlab is required for PDF export")
        c = pdfcanvas.Canvas(filename, pagesize=(self.width, self.height))
        # Convert from Tkinter's top-left origin to ReportLab's bottom-left origin
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


def main():
    root = tk.Tk()
    root.title("Grid Editor")
    GridEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
