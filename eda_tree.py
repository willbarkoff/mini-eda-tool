from enum import Enum
from typing import Self
from io import TextIOWrapper
from uuid import uuid4
import logging

BlockType = Enum(
    'BlockType',
    ['INPUT', 'OUTPUT', 'ID', 'AND', 'OR', 'XOR', 'NOT']
)

# End of weekend:
# - DAG covering

# - Sketch of some of the algorithms
# - Pymetal simulation for verillog
# - research def to gds conversion, then gds merge


# A block represents the behavioral specification of an item in the tree.
# block -> behavioral specificaiton
class NodeBehavior:
    def __init__(self, name, arg_count, behavior):
        self.name = name
        self.arg_count = arg_count
        self.behavior = behavior


INPUT_NAME = "Input"
OUTPUT_NAME: str = "Output"


INPUT = NodeBehavior(INPUT_NAME, 1, lambda simdata, arr: simdata[arr[0]])
OUTPUT = NodeBehavior(OUTPUT_NAME, 1, lambda _, arr: arr[0])
WIRE = NodeBehavior("-", 1, lambda _, arr: arr[0])
AND = NodeBehavior("&", 2, lambda _, arr: arr[0] and arr[1])
OR = NodeBehavior("|", 2, lambda _, arr: arr[0] or arr[1])
XOR = NodeBehavior("^", 2, lambda _, arr: arr[0] != arr[1])
NOT = NodeBehavior("~", 1, lambda _, arr: not arr[0])
NAND = NodeBehavior("NAND", 2, lambda _, arr: not (arr[0] and arr[1]))
NOR = NodeBehavior("NOR", 2, lambda _, arr: not (arr[0] or arr[1]))


class Position:
    def __init__(self):
        self.unspecified = True


UNSPECIFIED_POS = Position()


# tree -> node
class EDANode:
    __match_args__ = ("children",)

    def __init__(self, behavior: NodeBehavior, position: Position):
        self.behavior = behavior
        self.position = None
        self.technology_details = None
        self.children: list[EDANode] = []
        self.uuid = uuid4()
        self.__type__ = "verilog"

    def with_children(behavior: NodeBehavior, position: Position, children: list):
        node = EDANode(behavior, position)
        node.children = children
        if len(children) != 1:
            children.sort(key=lambda child: child.behavior.name)
        return node

    def set_technology_details(self, technology_details):
        self.technology_details = technology_details

    def children(self):
        return self.children

    def add_child(self, new_child):
        self.children.append(new_child)
        if len(self.children) != 1:
            self.children.sort(key=lambda child: child.behavior.name)

    def set_children(self, new_children):
        self.children = new_children
        if len(self.children) != 1:
            self.children.sort(key=lambda child: child.behavior.name)

    def check(self):
        if (len(self.children) != self.behavior.arg_count):
            raise TypeError("Incorrect child count.")

    def simulate(self, simdata):
        if self.behavior.name == INPUT_NAME:
            return simdata[self.children[0]]
        return self.behavior.behavior(simdata, [child.simulate(simdata) for child in self.children])

    def dump_mermaid(self, file: TextIOWrapper):
        file.write("flowchart TD\n")
        self.__dump_mermaid__(file, [])

    def __dump_mermaid__(self, file: TextIOWrapper, visited_list: list[str]):
        if (self.uuid.hex in visited_list):
            return

        if (self.behavior.name == "Input" or self.behavior.name == "Output"):
            file.write(
                f"\tnode{self.uuid.hex}[/{self.behavior.name} {self.children[0]}\\]\n")
        else:
            if self.behavior.name == "Input":
                file.write(
                    f"\tnode{self.uuid.hex}[/\"{self.behavior.name}\"\\]\n")
            elif self.__type__ == "verilog":
                file.write(
                    f"\tnode{self.uuid.hex}[\"{self.behavior.name}\"]\n")
            elif self.__type__ == "stdcell":
                file.write(
                    f"\tnode{self.uuid.hex}{'{{'}\"{self.behavior.name}\"{'}}'}\n")

            for child in self.children:
                child.__dump_mermaid__(file, visited_list + [self.uuid.hex])
                file.write(f"\tnode{self.uuid.hex}-->node{child.uuid.hex}\n")

    def cannonicalize(self):
        match self.behavior.name:
            case ("NAND" | "NOT" | "Input" | "Output"): return self
            case "&":
                newChild = EDANode.with_children(
                    NAND, Position(), [c.cannonicalize() for c in self.children])
                return EDANode.with_children(NOT, Position(), [newChild])
            case "|":
                a_inv = EDANode.with_children(
                    NOT, Position(), [self.children[0].cannonicalize()])
                b_inv = EDANode.with_children(
                    NOT, Position(), [self.children[1].cannonicalize()])
                return EDANode.with_children(NAND, Position(), [a_inv, b_inv])
            case "~": return EDANode.with_children(NOT, Position, [self.children[0].cannonicalize()])

    def simplify(self):
        if self.behavior.name == "~" and self.children[0].behavior.name == "~":
            return self.children[0].children[0].simplify()
        else:
            return EDANode.with_children(self.behavior,
                                         self.position,
                                         [c.simplify() for c in self.children] if self.behavior.name != "Input" else self.children)

    def set_type(self, type: str):
        self.__type__ = type

    # match(other) checks if other matches the pattern presented at the root of self. If it does, it returns the children replacement. If not, it returns None.
    def match(self, other: Self, thing=0) -> None | list[Self]:
        logging.debug(
            f"Step {thing}: comparing {self.behavior.name} to {other.behavior.name}")
        if other.behavior.name == "Input":
            logging.debug(
                f"Found input. Partial match.")
            return [self]

        if other.behavior.name != self.behavior.name:
            logging.debug(
                f"Mismatch {other.behavior.name} to {self.behavior.name}. No match.")
            return None

        logging.debug(
            f"Match {other.behavior.name} to {self.behavior.name}.")

        results: list[Self] = []
        for i in range(len(self.children)):
            res = self.children[i].match(other.children[i], thing=thing + 1)
            if res == None:
                return None
            results += res

        return results
