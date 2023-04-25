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

    varname = pp.Word(pp.alphanums)
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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: lexparse.py [verilog file]", file=sys.stderr)
        sys.exit(1)

    result = parselex(sys.argv[1])
    print(result.dump())

    print("Parsing module", result.module_decl.name)
    inputs = []
    outputs = []
    for param in result.module_decl.params:
        match param:
            case ['input', n]: inputs += n
            case ['output', t, n]: outputs += n
            case _: raise TypeError("Invlaid parameter", param)

    print("Module has inputs", inputs)
    print("Module has outputs", outputs)

    for assign_stmt in result.module_body:
        if (not (assign_stmt.varname in outputs)):
            raise NotImplemented("Not implemented: assign to non-output")

        if (assign_stmt.expr[0][0].operator):
            print('unary')
        elif (assign_stmt.expr[0][0].value):
            print("binary")
