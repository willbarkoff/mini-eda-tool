import lexparse
import argparse
import technology
import logging

parser = argparse.ArgumentParser(
    prog="edatool.py",
    description="edatool.py is a simple EDA tool for generating standard-cell based designs implemented in Python.",
    epilog="(c) 2023 William Barkoff")

parser.add_argument('filename', help="The verilog file to produce a chip for.")
parser.add_argument(
    'standard_cells', help="The JSON standard cell description file.")
parser.add_argument('-m', '--mermaid', action="store_true",
                    help="Whether to dump mermaid files for each step for debugging or presentation.")
parser.add_argument('-v', '--verbose', action="store_true",
                    help="Whether to include verbose information.")

args = parser.parse_args()

logging.basicConfig(format='%(message)s',
                    level=logging.DEBUG if args.verbose else logging.INFO)

# First, we parse the standard cell library
logging.debug("--------------------------------------------")
logging.debug("Parsing standard cell library")
logging.debug("--------------------------------------------")

std_cells = technology.Technology(
    args.standard_cells, dump_mermaid=args.mermaid)

logging.debug("--------------------------------------------")
logging.debug("Parsing the verilog input")
logging.debug("--------------------------------------------")

verilog_ast = lexparse.lexparse(args.filename)[0]
if args.mermaid:
    file = f"mermaid/{verilog_ast.name}-ast.mmd"
    logging.info(f"Writing file {file}")
    verilog_ast.eda_tree.dump_mermaid(open(file, "w"))

cannonicalized = verilog_ast.eda_tree.cannonicalize()
if args.mermaid:
    file = f"mermaid/{verilog_ast.name}-cannonicalized.mmd"
    logging.info(f"Writing file {file}")
    verilog_ast.eda_tree.dump_mermaid(open(file, "w"))

simplified = verilog_ast.eda_tree.simplify()
if args.mermaid:
    file = f"mermaid/{verilog_ast.name}-simplified.mmd"
    logging.info(f"Writing file {file}")
    verilog_ast.eda_tree.dump_mermaid(open(file, "w"))
