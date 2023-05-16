# Mini EDA Tool
```
usage: edatool.py [-h] [-m] [-v] [-w WIDTH] [-l HEIGHT] filename standard_cells
```

This Mini EDA tool takes verilog, lexes and parses it, then technology maps it to a standard cell library, places standard cells, and routes the chip (likely dropping some routes).

For a simple example, you can use this verilog file. Save it as `test.v`:

```verilog
module adder(input a, input b, input c, output logic y);
    assign y = ((~a & ~b) & c) | (((~a & b) & ~c) | (((a & ~b) & ~c) | (a & b) & c));
endmodule
```

Next, you can setup a python `venv` with these commands:
```sh
$ python3 -m venv ./venv
$ source ./venv/bin/activate
$ pip3 install -r requirements.txt
```

<details>
<summary>Additional ECELinux details.</summary> 
Unfortuantly, the code doesn't run on ECELinux beccause the version of python is too old. Multiple dependencies (pyparsing, matplotlib) are unsupported, but it can be run with Python 3.11+.
</details>


And finally, generate the chip:
```sh
$ python3 edatool.py test.v stdcells.json -m -w 50 -l 50
```

This will create a `50` x `50` chip using the standard cell library described in `stdcells.json`, which is included in this repository. The output, `chip.json`, will describe the completed chip. Additionally, a `mermaid/` directory is created with [mermaid](https://mermaid.js.org/) diagrams of the chip, and png images of the generated design.

## Detailed Usage
```
usage: edatool.py [-h] [-m] [-v] [-w WIDTH] [-l HEIGHT]
                  filename standard_cells

edatool.py is a simple EDA tool for generating standard-cell based designs
implemented in Python.

positional arguments:
  filename              The verilog file to produce a chip for.
  standard_cells        The JSON standard cell description file.

options:
  -h, --help            show this help message and exit
  -m, --mermaid         Whether to dump mermaid files for each step for
                        debugging or presentation.
  -v, --verbose         Whether to include verbose information.
  -w WIDTH, --width WIDTH
                        Width of the chip.
  -l HEIGHT, --height HEIGHT
                        Height of the chip.

(c) 2023 William Barkoff
```