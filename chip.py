from matplotlib import patheffects
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches
import jsonpickle

from eda_tree import EDANode

PIN_SIZE = (2, 2)
STDCELL_SIZE = (8, 8)


class Position():
    def __init__(self, x0, y0, x1, y1):
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1


class ChipCell():
    def __init__(self, name: str, position: Position, type: str, id: str):
        self.name = name
        self.position = position
        self.type = type
        self.id = id


class ChipWire():
    def __init__(self, x0: int, y0: int, x1: int, y1: int, track: int):
        if x0 != x1 and y0 != y1:
            raise Exception(
                "Attempted to create a wire that was not vertical or horizontal")

        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1


class Chip():
    def __init__(self, width, height, inputs, outputs):
        self.width = width
        self.height = height
        self.cells: list[ChipCell] = []
        self.wires: list[ChipWire] = []

        self.pin_x0 = PIN_SIZE[0] * 0.5
        self.pin_y0 = PIN_SIZE[1] * 0.5

        self.cell_x0 = PIN_SIZE[0]
        self.cell_y0 = PIN_SIZE[1] * 2

        for pin in inputs:
            self.cells.append(ChipCell(
                pin,
                Position(self.pin_x0,
                         self.pin_y0,
                         self.pin_x0 + PIN_SIZE[0],
                         self.pin_y0 + PIN_SIZE[1]),
                "pin",
                "Input_" + pin))

            self.pin_x0 += PIN_SIZE[0] * 2

        for pin in outputs:
            self.cells.append(ChipCell(
                pin,
                Position(self.pin_x0,
                         self.pin_y0,
                         self.pin_x0 + PIN_SIZE[0],
                         self.pin_y0 + PIN_SIZE[1]),
                "pin",
                "Output_" + pin))

            self.pin_x0 += PIN_SIZE[0] * 2

    # add_stdcell(tree) recursively adds all the standard cells from tree into tree
    def add_tree(self, tree: EDANode):
        if tree.behavior.name == "Input":
            return

        if self.cell_x0 + STDCELL_SIZE[1] > self.width:
            self.cell_x0 = PIN_SIZE[0]
            self.cell_y0 = self.cell_y0 + STDCELL_SIZE[1]

        self.cells.append(ChipCell(
            tree.behavior.name,
            Position(self.cell_x0, self.cell_y0, self.cell_x0 +
                     STDCELL_SIZE[0], self.cell_y0 + STDCELL_SIZE[1]),
            "stdcell",
            tree.uuid.hex
        ))

        self.cell_x0 += STDCELL_SIZE[1]

        for child in tree.children:
            self.add_tree(child)

    def __plot_rectangle__(self, ax: Axes, x0: float, y0: float, x1: float, y1: float, color: str, text: str | None = None):
        verts = [(x0, y0),
                 (x0, y1),
                 (x1, y1),
                 (x1, y0),
                 (x0, y0)]

        codes = [
            Path.MOVETO,
            Path.LINETO,
            Path.LINETO,
            Path.LINETO,
            Path.CLOSEPOLY,
        ]

        path = Path(verts, codes)
        patch = patches.PathPatch(path, facecolor=color)

        ax.add_patch(patch)
        if (text != None):
            text = ax.text(x0, y0, text, ha='left',
                           va='bottom', size=12)

    def __type_to_color__(self, type):
        match type:
            case "pin": return "lightblue"
            case "stdcell": return "lightgreen"
            case "chip": return "white"
            case _: raise Exception("Unknown cell type", type)

    def dump_image(self, path):
        fig, ax = plt.subplots()

        border_width = 0.0625

        ax.set_xlim(self.width * -border_width,
                    self.width * (1 + border_width))
        ax.set_ylim(self.height * -border_width,
                    self.height * (1 + border_width))

        self.__plot_rectangle__(ax, 0, 0, self.width, self.height, "white")

        for box in self.cells:
            self.__plot_rectangle__(ax, box.position.x0, box.position.y0,
                                    box.position.x1, box.position.y1, self.__type_to_color__(box.type), box.name)

        plt.savefig(path)

    def route(self, tree):
        raise Exception("Unimplemented")

    def dump_json(self, file: str):
        with open(file, "w") as f:
            chip_json = jsonpickle.dumps(self)
            f.write(chip_json)
