import sys
import eda_tree
import pyparsing as pp
import logging

ppt = pp.testing


# A VerilogModule reporesents a module implemented in verilog
class VerilogModule:
    def __init__(self, inputs: list[str], outputs: list[str], name: str, eda_tree: eda_tree.EDANode):
        self.name = name
        self.eda_tree = eda_tree
        self.inputs = inputs
        self.outputs = outputs


# lexparse(file) lexes and parses a file. It returns an array of VerilogModules that represent the modules defined in that file.
def lexparse(file) -> list[VerilogModule]:
    module_name = pp.Word(pp.alphanums)("module_name")
    module_keyword = pp.Keyword("module")
    endmodule_keyword = pp.Keyword("endmodule")
    semi = ";"

    varname = pp.Word(pp.alphanums+"_")
    vartype = pp.Keyword("wire") | pp.Keyword("logic")

    input_stmt = "input" + varname
    output_stmt = "output" + vartype + varname

    module_decl = pp.Group(module_keyword + module_name("name") +
                           "(" + pp.delimited_list(pp.Group(input_stmt("input") | output_stmt("output")), ",")("params") + ")" + semi)
    endmoudle_decl = endmodule_keyword

    andop, orop, notop, xorop = map(
        lambda x: pp.Group(pp.Literal(x)("operator")), "&|~^")
    lpar, rpar = map(pp.Suppress, "()")

    stmt = pp.Forward()

    valexpr = pp.infix_notation(
        pp.Group(varname("value")),
        [
            (notop, 1, pp.OpAssoc.RIGHT),
            (andop, 2, pp.OpAssoc.LEFT),
            (xorop, 2, pp.OpAssoc.LEFT),
            (orop, 2, pp.OpAssoc.LEFT),
        ]
    )

    assign_stmt = "assign" + varname("varname") + "=" + valexpr("expr") + ";"

    stmt <<= assign_stmt("assign_stmt")

    module_body = pp.Group(stmt)[...]("assigns")

    module = module_decl("module_decl") + \
        module_body("module_body") + endmoudle_decl

    grammar = pp.Group(module)[...]("modules")

    parse_results = grammar.parse_file(file)

    results: list[VerilogModule] = []

    for module in parse_results.modules:
        name = module.module_decl.name
        logging.debug(f"Parsing module {name}")
        inputs = []
        outputs = []
        for param in module.module_decl.params:
            match param:
                case ['input', n]: inputs += n
                case ['output', t, n]: outputs += n
                case _: raise TypeError("Invalid parameter", param)

        tree: eda_tree.EDANode
        for assign_stmt in module.module_body:
            if (not (assign_stmt.varname in outputs)):
                raise NotImplemented("Not implemented: assign to non-output")

            expr = assign_stmt.expr
            tree = parse_operator(expr, inputs)

        results.append(VerilogModule(inputs, outputs, name, tree))

    return results


# infix_to_prefix converts parser output in infix notation to parser output in prefix notation.
def infix_to_prefix(infix):
    if ("Operator" in infix[0]):
        return infix
    return [infix[1], infix[0], infix[2]]


# get_block_for_operator(operator) returns the cooresponding NodeBehavior for a verilog operator.
def get_block_for_operator(operator: str) -> eda_tree.NodeBehavior:
    match operator:
        case "&": return eda_tree.AND
        case "|": return eda_tree.OR
        case "^": return eda_tree.XOR
        case "~": return eda_tree.NOT
        case _: raise TypeError("Invalid operator", operator)


def parse_operator(op, inputs):
    if (type(op) is str):
        tree = eda_tree.EDANode(eda_tree.INPUT, eda_tree.UNSPECIFIED_POS)
        tree.add_child(op)
        return tree

    if (len(op) == 1):
        if not (op.value in inputs):
            raise TypeError("Assign statement funciton of",
                            op.value, "which isn't an input.")
        tree = eda_tree.EDANode(eda_tree.INPUT, eda_tree.UNSPECIFIED_POS)
        tree.add_child(op.value)
        return tree

    if (op[0].operator):
        block = get_block_for_operator(op[0].operator)
        tree = eda_tree.EDANode(block, eda_tree.UNSPECIFIED_POS)
        tree.add_child(parse_operator(op[1], inputs))
        return tree

    block = get_block_for_operator(op[1].operator)
    tree = eda_tree.EDANode(block, eda_tree.UNSPECIFIED_POS)
    tree.add_child(parse_operator(op[0], inputs))
    tree.add_child(parse_operator(op[2], inputs))
    return tree
