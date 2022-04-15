from enum import Enum, auto
import re
from typing import List, Optional

from exceptions import ConversionException, InvalidFormatException

escapes=re.compile(r"\\[0-9]{3}")

class InstructionKey(Enum):
  MOVE = auto()
  CREATEFRAME = auto()
  PUSHFRAME = auto()
  POPFRAME = auto()
  DEFVAR = auto()
  CALL = auto()
  RETURN = auto()
  PUSHS = auto()
  POPS = auto()
  ADD = auto()
  SUB = auto()
  MUL = auto()
  DIV = auto()
  IDIV = auto()
  LT = auto()
  GT = auto()
  EQ = auto()
  AND = auto()
  OR = auto()
  NOT = auto()
  INT2CHAR = auto()
  STRI2INT = auto()
  INT2FLOAT = auto()
  FLOAT2INT = auto()
  READ = auto()
  WRITE = auto()
  CONCAT = auto()
  STRLEN = auto()
  GETCHAR = auto()
  SETCHAR = auto()
  TYPE = auto()
  LABEL = auto()
  JUMP = auto()
  JUMPIFEQ = auto()
  JUMPIFNEQ = auto()
  EXIT = auto()
  DPRINT = auto()
  BREAK = auto()

STRING_TO_INSTRUCTION = {
  "MOVE": InstructionKey.MOVE,
  "CREATEFRAME": InstructionKey.CREATEFRAME,
  "PUSHFRAME": InstructionKey.PUSHFRAME,
  "POPFRAME": InstructionKey.POPFRAME,
  "DEFVAR": InstructionKey.DEFVAR,
  "CALL": InstructionKey.CALL,
  "RETURN": InstructionKey.RETURN,
  "PUSHS": InstructionKey.PUSHS,
  "POPS": InstructionKey.POPS,
  "ADD": InstructionKey.ADD,
  "SUB": InstructionKey.SUB,
  "MUL": InstructionKey.MUL,
  "DIV": InstructionKey.DIV,
  "IDIV": InstructionKey.IDIV,
  "LT": InstructionKey.LT,
  "GT": InstructionKey.GT,
  "EQ": InstructionKey.EQ,
  "AND": InstructionKey.AND,
  "OR": InstructionKey.OR,
  "NOT": InstructionKey.NOT,
  "INT2CHAR": InstructionKey.INT2CHAR,
  "STRI2INT": InstructionKey.STRI2INT,
  "INT2FLOAT": InstructionKey.INT2FLOAT,
  "FLOAT2INT": InstructionKey.FLOAT2INT,
  "READ": InstructionKey.READ,
  "WRITE": InstructionKey.WRITE,
  "CONCAT": InstructionKey.CONCAT,
  "STRLEN": InstructionKey.STRLEN,
  "GETCHAR": InstructionKey.GETCHAR,
  "SETCHAR": InstructionKey.SETCHAR,
  "TYPE": InstructionKey.TYPE,
  "LABEL": InstructionKey.LABEL,
  "JUMP": InstructionKey.JUMP,
  "JUMPIFEQ": InstructionKey.JUMPIFEQ,
  "EXIT": InstructionKey.EXIT,
  "DPRINT": InstructionKey.DPRINT,
  "BREAK": InstructionKey.BREAK
}

class TypeKey(Enum):
  VAR = auto()
  INT = auto()
  FLOAT = auto()
  BOOL = auto()
  STRING = auto()
  NIL = auto()

STRING_TO_TYPE = {
  "var": TypeKey.VAR,
  "int": TypeKey.INT,
  "float": TypeKey.FLOAT,
  "bool": TypeKey.BOOL,
  "string": TypeKey.STRING,
  "nil": TypeKey.NIL
}

class FrameTypeKey(Enum):
  GLOBAL = auto()
  LOCAL = auto()
  TEMPORARY = auto()

STRING_TO_FRAME_TYPE = {
  "GF": FrameTypeKey.GLOBAL,
  "LF": FrameTypeKey.LOCAL,
  "TF": FrameTypeKey.TEMPORARY
}


def dec2char(matchobj):
  dec = matchobj.group(0)
  dec = int(dec[1:])
  return chr(dec)

class Argument:
  def __init__(self, type:TypeKey, value:str):
    self.type = type

    if self.type == TypeKey.NIL and value == "nil":
      self.value = None
    elif self.type == TypeKey.INT:
      try:
        self.value = int(value)
      except:
        raise ConversionException(f"Failed to convert value '{value}' to int")
    elif self.type == TypeKey.FLOAT:
      try:
        self.value = float(value)
      except:
        try:
          self.value = float.fromhex(value)
        except:
          raise ConversionException(f"Failed to convert value '{value}' to float")
    elif self.type == TypeKey.BOOL and (value == "true" or value == "false"):
      if value == "true":
        self.value = True
      else:
        self.value = False
    elif self.type == TypeKey.STRING:
      self.value = escapes.sub(dec2char, value)
    elif self.type == TypeKey.VAR and len(value) != 0:
      amp_pos = value.find("@")
      if amp_pos == -1:
        raise InvalidFormatException(f"Can't parse string '{value}' as variable type")

      if value[:amp_pos] not in STRING_TO_FRAME_TYPE.keys():
        raise ConversionException(f"Value '{value[:amp_pos]}' is not valid identificator of frame")

      frame_type = STRING_TO_FRAME_TYPE[value[:amp_pos]]

      variable_name = value[amp_pos + 1:]
      if not variable_name:
        raise InvalidFormatException(f"String '{value}' missing variable name for parsing as variable")

      self.value = (frame_type, variable_name)
    else:
      raise InvalidFormatException(f"Type '{self.type}' and value '{value}' is not valid combination of values")

  @classmethod
  def from_string(cls, string:str):
    amp_pos = string.find("@")
    if amp_pos == -1:
      raise InvalidFormatException(f"Can't parse string '{string}' as argument")

    try:
      prefix = string[:amp_pos]
      value = string[amp_pos + 1:]
    except:
      raise InvalidFormatException(f"Can't parse string '{string}' as argument")

    if prefix in STRING_TO_FRAME_TYPE.keys():
      return cls(TypeKey.VAR, string)
    else:
      if prefix not in STRING_TO_TYPE.keys():
        raise ConversionException(f"'{prefix}' is not valid type of argument")
      value_type = STRING_TO_TYPE[prefix]

      return cls(value_type, value)

  def __repr__(self):
    return f"Argument(Type: {self.type}, Value: '{self.value}')"

class Instruction:
  __index = 0

  def __init__(self, instruction: InstructionKey, arguments: Optional[List[Argument]] = None):
    self.instruction = instruction
    self.arguments = arguments if arguments else []
    self.index = Instruction.__index

    Instruction.__index += 1

  def __repr__(self):
    arguments_string = (", ".join([str(arg) for arg in self.arguments])) if self.arguments else ""
    return f"Instruction({self.index}, {self.instruction}, [{arguments_string}])"


