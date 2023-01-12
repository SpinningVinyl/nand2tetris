"""Hack VM to assembly translator implemented in Python 3. Requires Python 3.10+.
This is a full implementation that supports all Hack VM commands: push/pop, arithmetic
instructions, program flow and function calls/returns. Passes all tests, including
FibonacciElements.

Copyright 2022 Pavel Urusov.
Licensed under the terms of the General Public License v3 or later.

If you're taking the Nand2Tetris course, you're welcome to borrow ideas from this program,
but I strongly encourage you not to submit it as your own code. After all, the core idea
of the course is learning by doing."""

import enum
import ntpath
import os
import sys
import re

import helper as H
from helper import MessageType as MT

math_instructions = {
    "add": "D+M",
    "sub": "M-D",
    "and": "D&M",
    "or" : "D|M",
    "not": "!M",
    "neg": "-M",
    "eq" : "JEQ",
    "lt" : "JLT",
    "gt" : "JGT"
}

segments = {
    "local"     : "LCL",
    "argument"  : "ARG",
    "this"      : "THIS",
    "that"      : "THAT",
    "temp"      : "R5",
    "pointer"   : "R3",
    "R0"        : "R0",
    "R1"        : "R1",
    "R2"        : "R2",
    "R3"        : "R3",
    "R4"        : "R4",
    "R5"        : "R5",
    "R6"        : "R6",
    "R7"        : "R7",
    "R8"        : "R8",
    "R9"        : "R9",
    "R10"       : "R10",
    "R11"       : "R11",
    "R12"       : "R12",
    "R13"       : "R13",
    "R14"       : "R14",
    "R15"       : "R15"
}

non_pointer_seg = ['R0', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7',
               'R8', 'R9', 'R10', 'R11', 'R12', 'R13', 'R14', 'R15']

class C(enum.Enum):
    ARITHMETIC = 0,
    PUSH = 1,
    POP = 2,
    LABEL = 3,
    GOTO = 4,
    IF = 5,
    FUNCTION = 6,
    RETURN = 7
    CALL = 8

instructions = {
    "add"       : C.ARITHMETIC,
    "sub"       : C.ARITHMETIC,
    "neg"       : C.ARITHMETIC,
    "eq"        : C.ARITHMETIC,
    "gt"        : C.ARITHMETIC,
    "lt"        : C.ARITHMETIC,
    "and"       : C.ARITHMETIC,
    "or"        : C.ARITHMETIC,
    "not"       : C.ARITHMETIC,
    "push"      : C.PUSH,
    "pop"       : C.POP,
    "label"     : C.LABEL,
    "goto"      : C.GOTO,
    "if-goto"   : C.IF,
    "function"  : C.FUNCTION,
    "call"      : C.CALL,
    "return"    : C.RETURN
}

class VmParser:
    def __init__(self, filename: str):
        self.current = 0
        # initialize the list
        self.code = []
        pattern = re.compile(r'\s+')
        try:
            message = H.fancy_message(f"Opening file {filename} for reading", MT.INFO)
            print(message)
            input_file = open(filename, mode='r')
            while True:
                line = input_file.readline()
                if not line: # EOF
                    break
                # ignore empty lines and full line comments
                line = line.strip()
                if line == "" or line[:2] == "//":
                    continue
                # sanitize spaces, remove trailing comments and add line to the list
                line = pattern.sub(' ', line)
                self.code.append(line.split("//")[0].strip())
            self.command = self.code[0]

        except:
            message = H.fancy_message(f"There was an error reading file {filename}", MT.ERROR)
            print(message)
            sys.exit(2)

    def has_next(self) -> bool:
        """Returns `True` if there are more lines of code to translate"""
        if self.current < (len(self.code) - 1):
            return True
        return False 

    def advance(self):
        """Moves to the next line of code"""
        self.current += 1
        self.command = self.code[self.current]
        
    def instruction_type(self) -> C:
        """Returns the type of the current command"""
        return instructions[self.command.split()[0]]

    def arg1(self) -> str:
        """Returns the first argument of the current command"""
        match self.instruction_type():
            case C.ARITHMETIC:
                return self.command.split()[0]
            case C.RETURN:
                return ""
            case _:
                return self.command.split()[1]

    def arg2(self) -> str:
        """Returns the second argument of the current command"""
        match self.instruction_type():
            case C.ARITHMETIC | C.LABEL | C.GOTO | C.IF | C.RETURN:
                return ""    
            case _:
                return self.command.split()[2]


class AsmWriter:
    def __init__(self, output_filename: str):
        self._jumps = 0
        self._returns = 0
        self._current_file = ''
        self._current_func = ''
        try:
            message = H.fancy_message(f"Opening file {output_filename} for writing", MT.INFO)
            print(message)
            self._output_file = open(output_filename, mode='w')
        except:
            message = H.fancy_message(f"There was an error opening file {output_filename}", MT.ERROR)
            print(message)
            sys.exit(2)

    def set_file_name(self, filename: str):
        self._current_file  = H.remove_ext(filename)
        self._current_func  = self._current_file # temporarily -- until we encounter a function
        pass

    def _write(self, output: str):
        try:
            self._output_file.write(output)
        except:
            message = H.fancy_message(f"Error writing to file {self._output_file}", MT.ERROR)
            print(message)
            sys.exit(2)

    def dispatch(self, command_type: C, arg1: str, arg2: str):
        asm = ""
        match command_type:
            case C.ARITHMETIC:
                asm = self._asm_arithmetic(arg1)
            case C.PUSH | C.POP:
                asm = self._asm_push_pop(command_type, arg1, arg2)
            case C.LABEL:
                asm = self._asm_label(arg1)
            case C.GOTO:
                asm = self._asm_goto(arg1)
            case C.IF:
                asm = self._asm_if(arg1)
            case C.FUNCTION:
                asm = self._asm_function(arg1, arg2)
            case C.CALL:
                asm = self._asm_call(arg1, arg2)
            case C.RETURN:
                asm = self._asm_return()
        self._write(asm)

    def bootstrap(self):
        """Generates bootstrap code for the VM and writes it to `self._output_file`"""
        # set SP to 256
        asm = '''@256
        D=A
        @SP
        M=D
        '''
        # call Sys.init
        asm += self._asm_call('Sys.init', '0')
        self._write(asm.replace(' ', ''))


    def _asm_function(self, func_name: str, local_vars: str) -> str:
        """Generates assembly code for the function command"""
        self._current_func = func_name
        comment = f"// function {func_name} {local_vars}\n"
        asm = self._asm_label(func_name, True)
        for i in range(int(local_vars)):
            asm += self._asm_push_pop(C.PUSH, 'constant', '0')
        return comment + asm

    def _asm_call(self, func_name: str, num_args: str) -> str:
        """Generates assembly code for the call command"""
        comment = f"// call {func_name} {num_args}\n"
        asm = ""
        return_label = func_name + "$Ret." + str(self._returns) # create the return label
        asm += self._asm_push_pop(C.PUSH, 'constant', return_label) # push the label to the stack
        asm += self._asm_push_pop(C.PUSH, 'R1', '0') # push LCL
        asm += self._asm_push_pop(C.PUSH, 'R2', '0') # push ARG
        asm += self._asm_push_pop(C.PUSH, 'R3', '0') # push THIS
        asm += self._asm_push_pop(C.PUSH, 'R4', '0') # push THAT
        # ARG = SP - (5 + num_args), LCL = SP
        asm += '''@SP
        D=M
        '''
        offset = 5 + int(num_args)
        asm += '''@{offset}
        D=D-A
        @ARG
        M=D
        @SP
        D=M
        @LCL
        M=D
        '''.format(offset=offset)
        asm += self._asm_goto(func_name, True)
        asm += self._asm_label(return_label, True)
        self._returns += 1
        return comment + asm.replace(' ', '')

    def _asm_return(self) -> str:
        """generates assembly code for the return command"""
        comment = f"// return from {self._current_func}\n"
        # end of frame
        asm = '''@LCL
        D=M
        @R14
        M=D
        '''
        # return address = end of frame - 5
        asm += '''@5
        D=D-A
        A=D
        D=M
        @R15
        M=D
        '''
        # overwrite the first argument with the return value
        asm += self._asm_push_pop(C.POP, 'argument', "0")
        # SP = ARG + 1
        asm += '''@ARG
        D=M+1
        @SP
        M=D
        '''
        # restore THAT
        asm += '''@R14
        AM=M-1
        D=M
        @THAT
        M=D
        '''
        # restore THIS
        asm += '''@R14
        AM=M-1
        D=M
        @THIS
        M=D
        '''
        # restore ARG
        asm += '''@R14
        AM=M-1
        D=M
        @ARG
        M=D
        ''' 
        # restore LCL
        asm += '''@R14
        AM=M-1
        D=M
        @LCL
        M=D
        '''
        # jump to the return address
        asm += self._asm_goto('R15', True)
        return comment + asm.replace(' ', '')
        pass

    def _asm_label(self, label: str, fnret = False) -> str:
        """Generates assembly code for the label command"""
        # if not calling or returning from a function, 
        # format `label` according to the spec
        label_string = f"{label}" if fnret else f"{self._current_func}.{label}"
        asm = f"// label {label_string}\n"
        asm += f"({label_string})\n"
        return asm

    def _asm_goto(self, label: str, fnret = False) -> str:
        """Generates assembly code for the goto command"""
        # if not calling or returning from a function, 
        # format `label` according to the spec
        label_string = f"{label}" if fnret else f"{self._current_func}.{label}"
        asm = f"// goto {label_string}\n"
        asm += f"@{label_string}\n"
        # if label points to a temp variable, take the address from the variable
        if label_string in ["R13", "R14", "R15"]:
            asm += "A=M\n"
        asm += "0;JMP\n"
        return asm
    
    def _asm_if(self, label: str, fnret = False) -> str:
        """Generates assembly code for the if command"""
        # if not calling or returning from a function, 
        # format `label` according to the spec
        label_string = f"{label}" if fnret else f"{self._current_func}.{label}"
        comment = f"// if-goto {label_string}\n"
        asm = '''@SP
        M=M-1
        A=M
        D=M
        @{label}
        D;JNE
        '''.format(label=label_string)
        return comment + asm.replace(' ', '')

    def _asm_arithmetic(self, command: str) -> str:
        """Generates assembly code for arithmetic commands"""
        comment = f"// {command}\n"
        asm = ""
        mathc = math_instructions[command] 
        match command:
            case "add" | "sub" | "and" | "or":
                asm += '''@SP 
                AM=M-1
                D=M
                A=A-1
                M={mathc}
                '''.format(mathc=mathc)
            case "neg" | "not":
                asm += '''@SP
                A=M-1
                M={mathc}
                '''.format(mathc=mathc)
            case "eq" | "gt" | "lt":
                jmp = self._current_func + '$JMP.' + str(self._jumps)
                asm += '''@SP
                AM=M-1
                D=M
                A=A-1
                D=M-D
                M=-1
                @{jmp}
                D;{mathc}
                @SP
                A=M-1
                M=0
                ({jmp})
                '''.format(jmp=jmp, mathc=mathc)
                self._jumps += 1
        return comment + asm.replace(' ', '')

    def _asm_push_pop(self, command_type: C, arg1: str, arg2: str) -> str:
        """Generates assembly code for pop and push commands"""
        static_prefix = self._current_file
        comment = ""
        asm = ""
        # generate assembly code for the push instruction
        if command_type == C.PUSH:
            comment += f"// push {arg1} {arg2}\n"
            if arg1 == "constant":
                asm += '''@{offset}
                D=A
                '''.format(offset=arg2)
            elif arg1 == "static":
                asm += '''@{prefix}.{index}
                D=M
                '''.format(prefix=static_prefix, index=arg2)
            else:
                segment = segments[arg1]
                asm += '''@{offset}
                D=A
                '''.format(offset=arg2)
                asm +='''@{segment}
                '''.format(segment=segment)
                if segment in non_pointer_seg:
                    asm += 'A=D+A\n'
                else:
                    asm += 'A=D+M\n'
                asm += 'D=M\n'
            asm += '''@SP
            A=M
            M=D
            @SP
            M=M+1
            '''
        # generate assembly code for the pop instruction
        else:
            comment += f"// pop {arg1} {arg2}\n"
            if arg1 == "static":
                asm += '@{prefix}.{index}\nD=A\n'.format(prefix=static_prefix, index=arg2)
            else:
                # calculate the memory address for storing the value 
                segment = segments[arg1]
                asm += '''@{offset}
                D=A
                @{segment}
                '''.format(offset=arg2, segment=segment)
                if segment in non_pointer_seg:
                    asm += 'D=D+A\n'
                else:
                    asm += 'D=D+M\n'
            # save the address in R13
            asm += '''@R13
            M=D
            '''
            # get value from the stack and copy to address stored in R13
            asm += '''@SP
            AM=M-1
            D=M
            @R13
            A=M
            M=D
            '''
        return comment + asm.replace(' ', '')

    # close the output file when the object is destroyed    
    def __del__(self):
        self._output_file.close()

def run(path: str):
    """Drives the process of translating VM files to Hack assembly"""
    path = path.strip()
    message = H.fancy_message(f"Argument: {path}", MT.INFO)
    print(message)
    path = os.path.abspath(path)
    if not path.endswith('.vm'):
        path = os.path.join(path, '')

    directory, input_file_name = ntpath.split(path)
    input_file_name = input_file_name or ntpath.basename(directory)
    output_file_name = H.new_file_name(input_file_name, "asm")
    output_file_full_path = os.path.join(directory, output_file_name)

    writer = AsmWriter(output_file_full_path)

    # if the argument is the path to a directory, translate all files in the directory
    if os.path.isdir(path):
        # bootstrap the VM
        writer.bootstrap()
        message = H.fancy_message(f"Translating all files in directory {path}", MT.INFO)
        print(message)
        message = H.fancy_message(f"Output file: {output_file_full_path}", MT.INFO)
        for root, dirs, files in os.walk(path):
            for input_file in files:
                if input_file.lower().endswith('.vm'):
                    input_file_full_path = os.path.join(path, input_file)
                    translate(input_file, input_file_full_path, writer)
    else:
        message = H.fancy_message(f"Translating file: {input_file_name}", MT.INFO)
        print(message)
        message = H.fancy_message(f"Output file: {output_file_full_path}", MT.INFO)
        translate(input_file_name, path, writer)

    del writer
    message = H.fancy_message("All done!", MT.INFO)
    print(message)

def translate(file_name: str, file_full_path: str, writer: AsmWriter):
    """Reads `file_full_path` and translates it from VM code to Hack assembly.
    Sets the current file name of `writer` to `file_name`"""
    message = H.fancy_message(f"Current file: {file_name}", MT.INFO)
    print(message)
    writer.set_file_name(file_name)
    parser = VmParser(file_full_path)
    while True:
        writer.dispatch(parser.instruction_type(), parser.arg1(), parser.arg2())
        if parser.has_next():
            parser.advance()
        else:
            break

def main():
    # no input file name supplied -- quit
    if len(sys.argv) < 2: 
        message = H.fancy_message("No arguments provided!", MT.ERROR)
        print(message)
        sys.exit(2)

    arg = sys.argv[1]
    run(arg)

if __name__ == "__main__":
    main()
