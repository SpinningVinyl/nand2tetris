# nand2tetris

This project contains the code I have written for the [nand2tetris](https://www.nand2tetris.org/) course.

### hw

This folder contains my implementations of various hardware parts, including the Hack CPU.

### Asm2Hack

This is my implementation of Hack assembler which translates programs written in Hack symbolic assembly language into machine code.

Usage:

```
python asm2hack.py path/to/source/file.asm
```

### VM Translator

Translates programs written in the VM language into Hack symbolic assembly. This is a full implementation that supports all Hack VM commands: push/pop, arithmetic instructions, program flow and function calls/returns. Passes all tests, including FibonacciElements.

Usage:

```
python vmtranslator.py path/to/source/directory
python vmtranslator.py path/to/source/file.vm
```

## License

Asm2Hack and VMTranslator are licensed under the terms of GNU GPL 3 or later.

The hardware description files are © Pavel Urusov and partially © Noam Nisan and Simon Shocken.