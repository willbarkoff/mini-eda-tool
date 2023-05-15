import json
import lexparse
import eda_tree
import logging


class StandardCell:
    def __init__(self, name: str, tree: eda_tree.EDANode, dump_mermaid=False):
        self.name = name
        self.tree = tree.cannonicalize().simplify()

        if dump_mermaid:
            file = f"mermaid/stdcell-{name}.mmd"
            logging.info(f"Writing file {file}")
            self.tree.dump_mermaid(open(file, "w"))


class Technology:
    def __init__(self, json_file: str, dump_mermaid=False):
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
            spec = next(cell for cell in modules if cell.name ==
                        stdcell["verilog_module"])
            logging.debug(
                f"Matched stdcell {stdcell['name']} -> {self.verilog}:{spec.name}")

            self.cells.append(StandardCell(
                stdcell["name"], spec.eda_tree, dump_mermaid=dump_mermaid))
