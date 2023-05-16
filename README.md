# Mini EDA Tool

This Mini EDA tool takes verilog, lexes and parses it, then technology maps it to a standard cell library, places standard cells, and routes the chip (likely dropping some routes).

For a simple example, you can use this verilog file. Save it as `test.v`:

```verilog
module adder(input a, input b, input c, output logic y);
    assign y = ((~a & ~b) & c) | (((~a & b) & ~c) | (((a & ~b) & ~c) | (a & b) & c));
endmodule
```

Next, you can setup a python `venv` with these commands:
```sh
$ mkdir mermaid
$ python3 -m venv ./venv
$ source ./venv/bin/activate
$ pip3 install -r requirements.txt
```

And finally, generate the chip:
```sh
$ python3 edatool.py test.v stdcells.json -m -w 50 -l 50
```

This will create a `50` x `50` chip using the standard cell library described in `stdcells.json`, which is included in this repository. The output, `chip.json`, will describe the completed chip. Additionally, a `mermaid/` directory is created with [mermaid](https://mermaid.js.org/) diagrams of the chip, and png images of the generated design.