from matplotlib import patheffects
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches
import jsonpickle
import copy
import logging

from eda_tree import EDANode
from technology import Technology

PIN_SIZE = (2, 2)
STDCELL_SIZE = (8, 8)


def __print_arr__(arr):
    print('\n'.join(' '.join(f"{x:02d}" for x in row) for row in arr))


def __find_min_neighbor__(arr: list[list[int]], i: int, j: int):
    minimum = -1
    neighbor = (-1, -1)

    if i+1 < len(arr) and arr[i+1][j] > 0 and (arr[i+1][j] < minimum or minimum == -1):
        minimum = arr[i+1][j]
        neighbor = (i+1, j)
    if i-1 >= 0 and arr[i-1][j] > 0 and (arr[i-1][j] < minimum or minimum == -1):
        minimum = arr[i-1][j]
        neighbor = (i-1, j)
    if j+1 < len(arr[0]) and arr[i][j+1] > 0 and (arr[i][j+1] < minimum or minimum == -1):
        minimum = arr[i][j+1]
        neighbor = (i, j+1)
    if j-1 >= 0 and arr[i][j-1] > 0 and (arr[i][j-1] < minimum or minimum == -1):
        minimum = arr[i][j-1]
        neighbor = (i, j-1)

    return neighbor


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


class Chip():
    def __init__(self, width, height, inputs, outputs):
        self.width = width
        self.height = height
        self.cells: list[ChipCell] = []

        # -1 is an unroutable obstacle (aka pin)
        self.obstacles = [[0] * width for _ in range(height)]

        self.pin_x0 = PIN_SIZE[0] * 0.5
        self.pin_y0 = PIN_SIZE[1] * 0.5

        self.cell_x0 = PIN_SIZE[0]
        self.cell_y0 = PIN_SIZE[1] * 2

        self.dropped_routes = 0

        for pin in inputs:
            self.cells.append(ChipCell(
                pin,
                Position(self.pin_x0,
                         self.pin_y0,
                         self.pin_x0 + PIN_SIZE[0],
                         self.pin_y0 + PIN_SIZE[1]),
                "pin",
                "Input_" + pin))

            for i in range(int(self.pin_x0), int(self.pin_x0 + PIN_SIZE[0])):
                for j in range(int(self.pin_y0), int(self.pin_y0 + PIN_SIZE[1])):
                    self.obstacles[i][j] = -1

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

            for i in range(int(self.pin_x0), int(self.pin_x0 + PIN_SIZE[0])):
                for j in range(int(self.pin_y0), int(self.pin_y0 + PIN_SIZE[1])):
                    self.obstacles[i][j] = -1

            self.pin_x0 += PIN_SIZE[0] * 2

    # add_stdcell(tree) recursively adds all the standard cells from tree into tree
    def add_tree(self, tree: EDANode, tech: Technology):
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

        std_cell = [cell for cell in tech.cells if cell.name ==
                    tree.behavior.name][0]

        for pin in std_cell.pins:
            self.obstacles[self.cell_x0 + pin.x][self.cell_y0 + pin.y] = -1

        self.cell_x0 += STDCELL_SIZE[1]

        for child in tree.children:
            self.add_tree(child, tech)

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

        for x in range(len(self.obstacles)):
            for y in range(len(self.obstacles[0])):
                if self.obstacles[x][y] == -1:
                    self.__plot_rectangle__(ax, x, y, x+1, y+1, "orange", "")
                elif self.obstacles[x][y] == -2:
                    self.__plot_rectangle__(ax, x, y, x+1, y+1, "blue", "")

        plt.savefig(path)

    def route(self, tree: EDANode, tech: Technology, route_to: None | tuple[int, int] = None):
        if route_to == None:
            output_cell = [
                cell for cell in self.cells if cell.id.startswith("Output_")][0]

            self.route(
                tree,
                tech,
                route_to=(int(output_cell.position.x0),
                          int(output_cell.position.y1 - 1)))

            logging.info(
                f"Routing complete. Dropped {self.dropped_routes} routes."
            )
            return

        obs_map = copy.deepcopy(self.obstacles)

        std_cell = None
        pos_data = None
        (start_x, start_y) = (-1, -1)
        if tree.behavior.name != "Input":
            std_cell = [cell for cell in tech.cells if cell.name ==
                        tree.behavior.name][0]

            pos_data = [c for c in self.cells if c.id ==
                        tree.uuid.hex][0].position

            (start_x, start_y) = (int(pos_data.x0 + std_cell.output_pin.x),
                                  int(pos_data.y0 + std_cell.output_pin.y))
        else:
            position = [
                c for c in self.cells if c.id == "Input_" + tree.children[0]
            ][0].position
            (start_x, start_y) = (int(position.x0), int(position.y1 - 1))

        obs_map[start_x][start_y] = 1

        iteration = 0
        routing_failed = False

        # ripple out
        while not routing_failed and obs_map[route_to[0]][route_to[1]] < 1:
            iteration += 1
            if iteration > self.height * self.width:
                # We have literally tried ev erything
                logging.error(
                    "Could not route. Voiding attempt, dropping route")
                routing_failed = True
                self.dropped_routes += 1

            for i in range(0, len(obs_map)):
                for j in range(0, len(obs_map[0])):
                    if obs_map[i][j] == 0 or (i, j) == (route_to[0], route_to[1]):
                        if (i, j) == (route_to[0], route_to[1]):
                            (x, y) = __find_min_neighbor__(obs_map, i, j)
                        (x, y) = __find_min_neighbor__(obs_map, i, j)
                        if x >= 0 and y >= 0 and obs_map[x][y] > 0:
                            obs_map[i][j] = obs_map[x][y] + 1

        current_x, current_y = (route_to[0], route_to[1])

        # backtrack
        while (current_x, current_y) != (start_x, start_y) and not routing_failed:
            self.obstacles[current_x][current_y] = -2
            (current_x, current_y) = __find_min_neighbor__(
                obs_map, current_x, current_y)

        self.obstacles[start_x][start_y] = -1
        self.obstacles[route_to[0]][route_to[1]] = -1

        if tree.behavior.name != "Input":
            for i in range(len(tree.children)):
                pin = (pos_data.x0 + std_cell.pins[i].x,
                       pos_data.y0 + std_cell.pins[i].y)
                self.route(tree.children[i], tech, route_to=pin)

    def dump_json(self, file: str):
        with open(file, "w") as f:
            chip_json = jsonpickle.dumps(self)
            f.write(chip_json)
