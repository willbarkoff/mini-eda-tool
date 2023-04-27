from enum import Enum
import dill as pickle

pickle.settings["recurse"] = True

BlockType = Enum(
    'BlockType',
    ['INPUT', 'OUTPUT', 'ID', 'AND', 'OR', 'XOR', 'NOT']
)


# A block represents the behavioral specification of an item in the tree.
class Block:
    def __init__(self, name, arg_count, behavior):
        self.name = name
        self.arg_count = arg_count
        self.behavior = behavior


INPUT = Block("Input", 1, lambda simdata, arr: simdata[arr[0]])
OUTPUT = Block("Output", 1, lambda _, arr: arr[0])
WIRE = Block("-", 1, lambda _, arr: arr[0])
AND = Block("&", 2, lambda _, arr: arr[0] and arr[1])
OR = Block("|", 2, lambda _, arr: arr[0] or arr[1])
XOR = Block("^", 2, lambda _, arr: arr[0] != arr[1])
NOT = Block("~", 1, lambda _, arr: not arr[0])


class Position:
    def __init__(self):
        self.unspecified = True


UNSPECIFIED_POS = Position()


class Tree:
    def __init__(self, block: Block, position: Position):
        self.block = block
        self.position = None
        self.children = []

    # def __init__(self, file):
    #     self = pickle.load(file)

    def children(self):
        return self.children

    def add_child(self, new_child):
        self.children.append(new_child)

    def set_children(self, new_children):
        self.children = new_children

    def check(self):
        if (len(self.children) != self.block.arg_count):
            raise TypeError("Incorrect child count.")

    def dump(self, file):
        return pickle.dump(self, file)

    def simulate(self, simdata):
        if self.block.name == "Input":
            return simdata[self.children[0]]
        return self.block.behavior(simdata, [child.simulate(simdata) for child in self.children])
