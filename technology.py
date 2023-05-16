import json
import lexparse
import eda_tree
import logging
import copy


class Pin:
    def __init__(self, x: int, y: int, name: str):
        self.x = x
        self.y = y
        self.name = name


class StandardCell:
    def __init__(self, name: str, tree: eda_tree.EDANode, inputs: list[str], pins: list[Pin], price: int, dump_mermaid=False):
        self.name = name
        self.inputs = inputs
        self.price = price
        self.behavior = eda_tree.NodeBehavior(name, len(inputs), tree.simulate)
        self.pins = pins
        self.output_pin = [p for p in pins if not p.name in inputs][0]

        if dump_mermaid:
            file = f"mermaid/stdcell-{name}.mmd"
            logging.info(f"Writing file {file}")
            tree.dump_mermaid(open(file, "w"))

        logging.debug(f"Cannonicalizing {name}")
        self.tree = tree.cannonicalize()

        if dump_mermaid:
            file = f"mermaid/stdcell-{name}-cannonical.mmd"
            logging.info(f"Writing file {file}")
            self.tree.dump_mermaid(open(file, "w"))

        logging.debug(f"Simplifying {name}")
        self.tree = self.tree.simplify()

        if dump_mermaid:
            file = f"mermaid/stdcell-{name}-simplified.mmd"
            logging.info(f"Writing file {file}")
            self.tree.dump_mermaid(open(file, "w"))

    def generateNode(self, children):
        node = eda_tree.EDANode.with_children(
            self.behavior, eda_tree.Position(), children)
        node.set_type("stdcell")
        return node

    def match(self, other: eda_tree.EDANode) -> None | tuple[list[eda_tree.EDANode], int]:
        result = other.match(self.tree)
        if result == None:
            return None

        return (result, self.price)


class Technology:
    def __init__(self, json_file: str, dump_stdcell_mermaid=False):
        json_spec: str
        with open(json_file) as f:
            json_spec = json.load(f)

        self.name: str = json_spec["name"]
        self.description: str = json_spec["description"]
        self.verilog: str = json_spec["verilog"]
        self.cells: list[StandardCell] = []

        logging.debug(f"Standard cell library {self.name}")
        logging.debug(f"Reading Verilog descriptions at {self.verilog}")

        modules = lexparse.lexparse(self.verilog)

        for stdcell in json_spec["cells"]:
            logging.debug(
                f"Finding cell {stdcell['name']} (verilog {self.verilog}:{stdcell['verilog_module']})")
            spec = next(cell for cell in modules if cell.name ==
                        stdcell["verilog_module"])
            logging.debug(
                f"Matched stdcell {stdcell['name']} -> {self.verilog}:{spec.name}")

            pins: list[Pin] = []
            for pin in stdcell["pins"]:
                pins.append(
                    Pin(pin["position"][0], pin["position"][1], pin["name"]))

            self.cells.append(StandardCell(
                stdcell["name"],
                spec.eda_tree,
                spec.inputs,
                pins,
                stdcell["price"],
                dump_mermaid=dump_stdcell_mermaid))

    # map(tree) covers tree with standard cells
    def map(self, tree: eda_tree.EDANode) -> tuple[eda_tree.EDANode, int]:
        if tree.behavior.name == "Input":
            return (tree, 0)

        min_cost_mapping = (None, -1)
        for cell in self.cells:
            logging.debug(f"Attempting to match {cell.name}")
            child_result = cell.match(tree)
            if child_result != None:
                cost = child_result[1]
                children: eda_tree.EDANode = []
                for child in child_result[0]:
                    (new_child, addtl_cost) = self.map(child)
                    cost += addtl_cost
                    children += [new_child]

                if min_cost_mapping[1] == -1 or cost < min_cost_mapping[1]:
                    min_cost_mapping = (cell.generateNode(children), cost)

        assert (min_cost_mapping[0] != None)
        return min_cost_mapping
