"""Helper functions for the VM Translator. Requires Python 3.

Copyright 2022 Pavel Urusov.
Licensed under the terms of the General Public License v3 or later.

If you're taking the Nand2Tetris course, you're welcome to borrow ideas from this program,
but I strongly encourage you not to submit it as your own code. After all, the core idea
of the course is learning by doing."""

import enum

class MessageType(enum.Enum):
    GENERAL = 0,
    INFO = 1,
    ERROR = 2

def fancy_message(message: str, type: MessageType) -> str:
    prefix = ""
    if type == MessageType.INFO:
        prefix = "[i] "
    if type == MessageType.ERROR:
        prefix = "[!] "
    if type == MessageType.GENERAL:
        prefix = "[*] "
    return prefix + message

def new_file_name(filename: str, extension: str) -> str:
    return remove_ext(filename) + '.' + extension

def remove_ext(filename: str) -> str:
    last_dot = filename.rfind('.')
    if last_dot == -1:
        return filename
    return filename[:last_dot]