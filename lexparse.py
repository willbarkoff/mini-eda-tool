import pyparsing as pp

ppt = pp.testing

data = """\
module nand;

    input a;
    input b;

    output wire y;

    assign y = a & ~b | b & ~a;

endmodule
"""


module_name = pp.Word(pp.alphanums)
module_keyword = pp.Keyword("module")
endmodule_keyword = pp.Keyword("endmodule")
semi = ";"
module_decl = module_keyword + module_name + semi
endmoudle_decl = endmodule_keyword

andop, orop, notop, xorop = map(pp.Literal, "&|~^")
lpar, rpar = map(pp.Suppress, "()")

stmt = pp.Forward()

varname = pp.Word(pp.alphanums)

vartype = pp.Keyword("wire")  # for now

input_stmt = "input" + varname + ";"
output_stmt = "output" + vartype + varname + ";"

valexpr = pp.infix_notation(
    varname,
    [
        (notop, 1, pp.OpAssoc.RIGHT),
        (andop, 2, pp.OpAssoc.LEFT),
        (xorop, 2, pp.OpAssoc.LEFT),
        (orop, 2, pp.OpAssoc.LEFT),
    ]
)

assign_stmt = "assign" + varname + "=" + valexpr + ";"

stmt <<= output_stmt | input_stmt | assign_stmt

module_body = pp.Group(stmt)[...]

grammar = module_decl + module_body + endmoudle_decl

print(grammar.parse_string(data).dump())

grammar.create_diagram("grammar-diagram.html")
