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


def new_file_name(fname: str, ext: str) -> str:
    last_dot = fname.rfind('.')
    if last_dot == -1:
        return fname + "." + ext
    return fname[:last_dot] + "." + ext

def decimal_to_binary(n: int) -> str:
    return bin(n).replace("0b", "")