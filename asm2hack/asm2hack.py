"""Hack assembly language compiler implemented in Python 3. Requires Python 3.10+"""
# Copyright 2022 Pavel Urusov
# Licensed under the terms of the General Public License v2 or later 

import sys

import helper as H
from helper import MessageType as MT

opcodes = {
        "@"     : "0",
        "C"     : "111"
        }

destcodes = {
        "null"  : "000",
        "M"     : "001",
        "D"     : "010",
        "MD"    : "011",
        "A"     : "100",
        "AM"    : "101",
        "AD"    : "110",
        "AMD"   : "111"
        }

jumpcodes = {
        "null"  : "000",
        "JGT"   : "001",
        "JEQ"   : "010",
        "JGE"   : "011",
        "JLT"   : "100",
        "JNE"   : "101",
        "JLE"   : "110",
        "JMP"   : "111"
        }

compcodes = {
        "0"     : "0101010",
        "1"     : "0111111",
        "-1"    : "0111010",
        "D"     : "0001100",
        "A"     : "0110000",
        "!D"    : "0001101",
        "!A"    : "0110001",
        "-D"    : "0001111",
        "-A"    : "0110011",
        "D+1"   : "0011111",
        "A+1"   : "0110111",
        "D-1"   : "0001110",
        "A-1"   : "0110010",
        "D+A"   : "0000010",
        "D-A"   : "0010011",
        "A-D"   : "0000111",
        "D&A"   : "0000000",
        "D|A"   : "0010101",
        "M"     : "1110000",
        "!M"    : "1110001",
        "-M"    : "1110011",
        "M+1"   : "1110111",
        "M-1"   : "1110010",
        "D+M"   : "1000010",
        "D-M"   : "1010011",
        "M-D"   : "1000111",
        "D&M"   : "1000000",
        "D|M"   : "1010101"
        }

ST = {
        "R0"    : 0,
        "R1"    : 1,
        "R2"    : 2,
        "R3"    : 3,
        "R4"    : 4,
        "R5"    : 5,
        "R6"    : 6,
        "R7"    : 7,
        "R8"    : 8,
        "R9"    : 9,
        "R10"   : 10,
        "R11"   : 11,
        "R12"   : 12,
        "R13"   : 13,
        "R14"   : 14,
        "R15"   : 15,
        "SCREEN": 16384,
        "KBD"   : 24576,
        "SP"    : 0,
        "LCL"   : 1,
        "ARG"   : 2,
        "THIS"  : 3,
        "THAT"  : 4
        }



def save_output(filename: str, output_list: list):
    """Saves `output_list` to file `filename`"""
    try:
        print(H.fancy_message(f"Saving file {filename}...", MT.INFO),
              end=" ")
        output_file = open(filename, mode='w')
        for line in output_list:
            output_file.write(line + "\n")
        print("Done.")
    except:
        error_message = H.fancy_message("Error opening output file " + filename,
                                      MT.ERROR)
        print("\n" + error_message)
        sys.exit(2)
    finally:
        output_file.close()

def read_asm(filename: str) -> list:
    """Opens and reads the file `filename` line by line,
    discarding empty lines and comments"""
    # initialize the empty list
    asm = []
    try:
        print(H.fancy_message(f"Opening file {filename}...", MT.INFO))
        input_file = open(filename, mode='r');
        while True:
            line = input_file.readline();
            if not line: # EOF
                break
            # ignore empty lines and full-line comments
            if line.strip() == "" or line.strip()[:2] == "//":
                continue
            # remove trailing comments and add to the list
            asm.append(line.split("//")[0].strip())
    except:
        message = H.fancy_message(f"There was an error reading file {filename}",
                                MT.ERROR)
        print(message)
        sys.exit(2)
    finally:
        input_file.close()
    return asm;

def parse_line(line: str) -> tuple:
    """parses the input strings and returns a tuple
    containing components of the instruction"""
    # remove all spaces from the input string
    instruction = line.replace(" ", "")
    
    # parse the A-instruction
    if instruction[0] == '@':
        return (instruction[0], instruction[1:])
    
    # parse the C-instruction
    # dest
    dest = "null"
    if "=" in instruction:
        shards = instruction.split("=")
        dest = shards[0]
        instruction = shards[1]
    # jump & comp
    jump = "null"
    comp = "0"
    if ";" in instruction:
        shards = instruction.split(";")
        jump = shards[1]
        comp = shards[0]
    else:
        comp = instruction
    return ("C", comp, dest, jump)

def translate(instr: tuple) -> str:
    """translates the instruction tuple into binary code"""

    # A-instruction
    if instr[0] == "@":
        opcode = opcodes["@"] 
        arg = instr[1]
        if arg.isdigit(): # the argument is an integer
            argnum = int(arg)
        else: # if not, look it up in the symbol table
            argnum = ST[arg]
        addr = H.decimal_to_binary(argnum);
        addrlen = len(addr)
        if addrlen < 15: # pad the address if it's too short
            addr = "0"*(15-addrlen) + addr
        if addrlen > 15: # truncate the address in case of overflow
            addr = addr[-15:]
        return opcode + addr

    # C-instruction
    opcode = opcodes[instr[0]]
    comp = compcodes[instr[1]]
    dest = destcodes[instr[2]]
    jump = jumpcodes[instr[3]]
    return opcode + comp + dest + jump

def st_labels(source: list) -> list:
    """processes the `source`, adds labels to the symbol table
    and removes label declarations from the `source`"""
    count = 0
    for line in source[:]:
        if line[0] == "(" and line[-1] == ")":
            label = line.replace("(", "").replace(")", "")
            ST[label] = count
            source.remove(line)
            continue
        count += 1
    return source

def st_vars(source: list):
    """finds variable declarations in `source` and 
    adds them to the symbol table"""
    addr = 16
    for line in source[:]:
        instr = line.replace(" ", "")
        if instr[0] == "@":
            symbol = instr.replace("@", "")
            if not symbol.isdigit():
                if symbol in ST:
                    continue
                ST[symbol] = addr
                addr += 1

def main():
    # check that there is more than one argument 
    if len(sys.argv) < 2: 
        message = H.fancy_message("No file name provided!", MT.ERROR)
        print(message)
        sys.exit(2)

    # the first parameter is the name of the input file
    input_file_name = sys.argv[1]

    # get the assembly code from the file
    code = read_asm(input_file_name)

    # handle labels and variables
    code = st_labels(code)
    st_vars(code)

    # create the output binary
    binary = []

    for line in code:
        binary.append(translate(parse_line(line)))
    
    # write it out
    output_file_name = H.new_file_name(input_file_name, "hack")
    save_output(output_file_name, binary)

if __name__ == "__main__":
    main()
