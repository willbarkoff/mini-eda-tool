import lexparse
import argparse
import technology
import logging
import chip
import os

step = 1


def log_step(name):
    global step
    logging.info(
        "\n---------------------------------------------------------------")
    logging.info(f"{step}. {name}")
    logging.info(
        "---------------------------------------------------------------")
    step += 1


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

parser.add_argument('-w', '--width', type=int,
                    help="Width of the chip.", default=40)
parser.add_argument('-l', '--height', type=int,
                    help="Height of the chip.", default=40)

args = parser.parse_args()

logging.basicConfig(format='%(message)s',
                    level=logging.DEBUG if args.verbose else logging.INFO)

logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

if args.mermaid:
    if not os.path.exists("mermaid"):
        os.makedirs("mermaid")

# First, we parse the standard cell library
log_step("Parsing standard cell library")

tech = technology.Technology(
    args.standard_cells, dump_stdcell_mermaid=args.mermaid)
logging.info(f"Success!")

log_step("Parsing the verilog input")

verilog_ast = lexparse.lexparse(args.filename)[0]
logging.info(f"Success!")
if args.mermaid:
    file = f"mermaid/{verilog_ast.name}-ast.mmd"
    logging.info(f"Writing file {file}")
    verilog_ast.eda_tree.dump_mermaid(open(file, "w"))

log_step("Cannonicalizing design")

cannonicalized = verilog_ast.eda_tree.cannonicalize()
logging.info(f"Success!")
if args.mermaid:
    file = f"mermaid/{verilog_ast.name}-cannonicalized.mmd"
    logging.info(f"Writing file {file}")
    cannonicalized.dump_mermaid(open(file, "w"))

log_step("Simplifying logic")

simplified = cannonicalized.simplify()
logging.info(f"Success!")
if args.mermaid:
    file = f"mermaid/{verilog_ast.name}-simplified.mmd"
    logging.info(f"Writing file {file}")
    simplified.dump_mermaid(open(file, "w"))

log_step("Mapping technology")
(mapped, price) = tech.map(simplified)
logging.info(f"Success! Mapping price is {price}")
if args.mermaid:
    file = f"mermaid/{verilog_ast.name}-mapped.mmd"
    logging.info(f"Writing file {file}")
    mapped.dump_mermaid(open(file, "w"))

log_step("Placing standard cells")

c = chip.Chip(args.width, args.height, verilog_ast.inputs, verilog_ast.outputs)
c.add_tree(mapped, tech)
if args.mermaid:
    file = f"mermaid/chip-placement.png"
    logging.info(f"Writing file {file}")
    c.dump_image(file)

log_step("Routing chip")
c.route(mapped, tech)
if args.mermaid:
    file = f"mermaid/chip-routed.png"
    logging.info(f"Writing file {file}")
    c.dump_image(file)

logging.info(f"Writing file chip.jso")
c.dump_json("chip.json")
