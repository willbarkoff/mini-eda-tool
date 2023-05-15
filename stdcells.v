module nand(input a, input b, output logic z);
    assign z = ~(a & b);
endmodule

module nor(input a, input b, output logic z);
    assign z = ~a & ~b;
endmodule

module not(input a, output logic z);
    assign z = ~a;
endmodule