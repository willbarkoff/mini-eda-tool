# Lexparse.py
# Simple parser for verilog files
#
#
# Limitations:
# - Only parses assign, input, output, module, and endmodule statments
# - Only suppors operators &, |, ~, and ^

import sys
import eda_tree
import pyparsing as pp

ppt = pp.testing


def parselex(file):
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

    grammar = module_decl("module_decl") + \
        module_body("module_body") + endmoudle_decl

    return grammar.parse_file(file)


def infix_to_prefix(infix):
    if ("Operator" in infix[0]):
        return infix
    return [infix[1], infix[0], infix[2]]


def get_block_for_operator(operator):
    match operator:
        case "&": return eda_tree.AND
        case "|": return eda_tree.OR
        case "^": return eda_tree.XOR
        case "~": return eda_tree.NOT
        case _: raise TypeError("Invalid operator", operator)


def parse_operator(op, inputs):
    if (type(op) is str):
        print("h", op)
        tree = eda_tree.Tree(eda_tree.INPUT, eda_tree.UNSPECIFIED_POS)
        tree.add_child(op)
        return tree

    if (len(op) == 1):
        if not (op.value in inputs):
            raise TypeError("Assign statement funciton of",
                            op.value, "which isn't an input.")
        tree = eda_tree.Tree(eda_tree.INPUT, eda_tree.UNSPECIFIED_POS)
        tree.add_child(op.value)
        return tree

    if (op[0].operator):
        block = get_block_for_operator(op[0].operator)
        tree = eda_tree.Tree(block, eda_tree.UNSPECIFIED_POS)
        tree.add_child(parse_operator(op[1], inputs))
        return tree

    block = get_block_for_operator(op[1].operator)
    tree = eda_tree.Tree(block, eda_tree.UNSPECIFIED_POS)
    tree.add_child(parse_operator(op[0], inputs))
    tree.add_child(parse_operator(op[2], inputs))
    return tree


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: lexparse.py [verilog file] [output file]", file=sys.stderr)
        sys.exit(1)

    file = open(sys.argv[2], mode='wb')
    result = parselex(sys.argv[1])

    print("Parsing module", result.module_decl.name)
    inputs = []
    outputs = []
    for param in result.module_decl.params:
        match param:
            case ['input', n]: inputs += n
            case ['output', t, n]: outputs += n
            case _: raise TypeError("Invalid parameter", param)

    print("Module has inputs", inputs)
    print("Module has outputs", outputs)

    for assign_stmt in result.module_body:
        if (not (assign_stmt.varname in outputs)):
            raise NotImplemented("Not implemented: assign to non-output")

        expr = assign_stmt.expr
        tree = parse_operator(expr, inputs)

        print(tree.simulate({
            "a": True,
            "b": False
        }))

        tree.dump(file)
        file.close()
        print("written to", sys.argv[2])
