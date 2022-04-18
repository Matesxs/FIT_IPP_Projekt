from enum import Enum, auto
import re
from typing import List, Optional, Any, Tuple
import xml.etree.ElementTree as XML

from errors import ErrorCodes, handle_error

escapes=re.compile(r"\\[0-9]{3}")

class InstructionKey(Enum):
  MOVE = auto()#

  CREATEFRAME = auto()#
  PUSHFRAME = auto()#
  POPFRAME = auto()#

  DEFVAR = auto()#
  CALL = auto()#
  RETURN = auto()#
  PUSHS = auto()#
  POPS = auto()#

  ADD = auto()#
  SUB = auto()#
  MUL = auto()#
  DIV = auto()#
  IDIV = auto()#

  LT = auto()#
  GT = auto()#
  EQ = auto()#

  AND = auto()#
  OR = auto()#
  NOT = auto()#

  INT2CHAR = auto()#
  STRI2INT = auto()#
  INT2FLOAT = auto()#
  FLOAT2INT = auto()#

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

  # Stack operations
  CLEARS = auto()

  ADDS = auto()
  SUBS = auto()
  MULS = auto()
  DIVS = auto()
  IDIVS = auto()

  LTS = auto()
  GTS = auto()
  EQS = auto()

  ANDS = auto()
  ORS = auto()
  NOTS = auto()

  INT2CHARS = auto()
  STRI2INTS = auto()
  INT2FLOATS = auto()
  FLOAT2INTS = auto()

  JUMPIFEQS = auto()
  JUMPIFNEQS = auto()

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
  "BREAK": InstructionKey.BREAK,

  # Stack operations
  "CLEARS": InstructionKey.CLEARS,

  "ADDS": InstructionKey.ADDS,
  "SUBS": InstructionKey.SUBS,
  "MULS": InstructionKey.MULS,
  "DIVS": InstructionKey.DIVS,
  "IDIVS": InstructionKey.IDIVS,

  "LTS": InstructionKey.LTS,
  "GTS": InstructionKey.GTS,
  "EQS": InstructionKey.EQS,

  "ANDS": InstructionKey.ANDS,
  "ORS": InstructionKey.ORS,
  "NOTS": InstructionKey.NOTS,

  "INT2CHARS": InstructionKey.INT2CHARS,
  "STRI2INTS": InstructionKey.STRI2INTS,
  "INT2FLOATS": InstructionKey.INT2FLOATS,
  "FLOAT2INTS": InstructionKey.FLOAT2INTS,

  "JUMPIFEQS": InstructionKey.JUMPIFEQS,
  "JUMPIFNEQS": InstructionKey.JUMPIFNEQS
}

class ArgumentTypeKey(Enum):
  TYPE = auto()
  LABEL = auto()
  VAR = auto()
  INT = auto()
  FLOAT = auto()
  BOOL = auto()
  STRING = auto()
  NIL = auto()

STRING_TO_ARGUMENT_TYPE = {
  "type": ArgumentTypeKey.TYPE,
  "label": ArgumentTypeKey.LABEL,
  "var": ArgumentTypeKey.VAR,
  "int": ArgumentTypeKey.INT,
  "float": ArgumentTypeKey.FLOAT,
  "bool": ArgumentTypeKey.BOOL,
  "string": ArgumentTypeKey.STRING,
  "nil": ArgumentTypeKey.NIL
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
  def __init__(self, t:ArgumentTypeKey, value:str, idx:int):
    self.idx = idx
    self.type = t
    if value is None:
      value = ""

    if self.type == ArgumentTypeKey.NIL and value == "nil":
      self.value = None
    elif self.type == ArgumentTypeKey.INT:
      try:
        self.value = int(value)
      except:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Failed to convert value '{value}' to int")
    elif self.type == ArgumentTypeKey.FLOAT:
      try:
        self.value = float(value)
      except:
        try:
          self.value = float.fromhex(value)
        except:
          handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Failed to convert value '{value}' to float")
    elif self.type == ArgumentTypeKey.BOOL and (value == "true" or value == "false"):
      if value == "true":
        self.value = True
      else:
        self.value = False
    elif self.type == ArgumentTypeKey.STRING:
      self.value = escapes.sub(dec2char, value)
    elif self.type == ArgumentTypeKey.LABEL:
      self.value = value
    elif self.type == ArgumentTypeKey.TYPE:
      if value not in ("float", "int", "bool", "string", "nil"):
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Argument type can't have value '{value}'")
      self.value = STRING_TO_ARGUMENT_TYPE[value]
    elif self.type == ArgumentTypeKey.VAR and len(value) != 0:
      amp_pos = value.find("@")
      if amp_pos == -1:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Can't parse string '{value}' as variable type")

      if value[:amp_pos] not in STRING_TO_FRAME_TYPE.keys():
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Value '{value[:amp_pos]}' is not valid identificator of frame")

      frame_type = STRING_TO_FRAME_TYPE[value[:amp_pos]]

      variable_name = value[amp_pos + 1:]
      if not variable_name:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"String '{value}' missing variable name for parsing as variable")

      self.value = (frame_type, variable_name)
    else:
      handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Type '{self.type}' and value '{value}' is not valid combination of values")

  def __repr__(self):
    return f"Argument(Type: {self.type}, Value: '{self.value}')"

class Instruction:
  def __init__(self, instruction: InstructionKey, order:int, arguments: Optional[List[Argument]] = None):
    self.order = order
    self.instruction = instruction
    self.arguments = arguments if arguments else []

  @classmethod
  def from_element(cls, element: XML.Element):
    if "opcode" not in element.keys() or "order" not in element.keys():
      handle_error(ErrorCodes.XML_BAD_STRUCTURE, "Missing 'opcode' or 'order' instruction attribute")

    instruction_name = element.attrib["opcode"].upper()
    if instruction_name not in STRING_TO_INSTRUCTION.keys():
      handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"'{instruction_name}' is not valid instruction")

    argument_name_list = [arg.tag for arg in element]
    if argument_name_list.count("arg1") > 1 or argument_name_list.count("arg2") > 1 or argument_name_list.count("arg3") > 1:
      handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"'{instruction_name}' have multiple arguments with same name")

    order = element.attrib["order"]
    if not order.isdecimal():
      handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"'{instruction_name}' have invalid order attribute")

    arguments = []
    used_argument_indexes = []
    for argument in element:
      if argument.tag not in ("arg1", "arg2", "arg3"):
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"'{argument.tag}' in instruction '{instruction_name}' is not valid argument of instruction")

      if "type" not in argument.keys():
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"'{argument.tag}' in instruction '{instruction_name}' don't have type attribute")

      type_string = argument.attrib["type"]
      if type_string not in STRING_TO_ARGUMENT_TYPE:
        handle_error(ErrorCodes.INTERN, f"'{type_string}' is not valid type")

      idx = int(argument.tag[3:])
      if idx in used_argument_indexes:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"'{argument.tag}' in instruction '{instruction_name}' is already present")

      used_argument_indexes.append(idx)
      arguments.append(Argument(STRING_TO_ARGUMENT_TYPE[type_string], argument.text, idx))

    # Check if there are no arg3 without arg2 or arg1 or arg2 without arg1
    if (3 in used_argument_indexes and (2 not in used_argument_indexes or 1 not in used_argument_indexes)) or \
      (2 in used_argument_indexes and 1 not in used_argument_indexes):
      handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"'{instruction_name}' have invalid argument indexes")

    arguments.sort(key=lambda x: x.idx)
    return cls(STRING_TO_INSTRUCTION[instruction_name], int(order), arguments)

  def __repr__(self):
    arguments_string = (", ".join([str(arg) for arg in self.arguments])) if self.arguments else ""
    return f"Instruction({self.order}, {self.instruction}, [{arguments_string}])"

class VariableTypeKey(Enum):
  INT = auto()
  FLOAT = auto()
  BOOL = auto()
  STRING = auto()
  NIL = auto()

ArgumentTypeToVariableType = {
  ArgumentTypeKey.INT: VariableTypeKey.INT,
  ArgumentTypeKey.FLOAT: VariableTypeKey.FLOAT,
  ArgumentTypeKey.BOOL: VariableTypeKey.BOOL,
  ArgumentTypeKey.STRING: VariableTypeKey.STRING,
  ArgumentTypeKey.NIL: VariableTypeKey.NIL
}

class Variable:
  def __init__(self, label:str):
    self.__label = label

    self.__type:Optional[VariableTypeKey] = None
    self.__value = None

  def is_initialized(self):
    return self.__type is not None

  def set_value(self, value):
    if isinstance(value, int):
      self.__type = VariableTypeKey.INT
    elif isinstance(value, float):
      self.__type = VariableTypeKey.FLOAT
    elif isinstance(value, bool):
      self.__type = VariableTypeKey.BOOL
    elif isinstance(value, str):
      self.__type = VariableTypeKey.STRING
    elif value is None:
      self.__type = VariableTypeKey.NIL
    else:
      handle_error(ErrorCodes.INTERN, f"Invalid datatype '{type(value)}' passed to variable")
    self.__value = value

  def get_label(self):
    return self.__label

  def get_value(self) -> Tuple[VariableTypeKey, Any]:
    return self.__type, self.__value

  def __repr__(self):
    return f"[{self.__label}:{self.__type}='{self.__value}']"

class Frame:
  def __init__(self, frame_type: FrameTypeKey):
    self.type = frame_type # only for debug

    self.variable_storage:List[Variable] = []

  def __get_by_name(self, label:str):
    for var in self.variable_storage:
      if var.get_label() == label:
        return var
    return None

  def __variable_exist(self, label:str) -> bool:
    if self.__get_by_name(label) is not None: return True
    return False

  def create_variable(self, label:str):
    if self.__variable_exist(label):
      handle_error(ErrorCodes.SEMANTIC_ERROR, f"Variable with name '{label}' already exists in frame of type '{self.type}'")
    self.variable_storage.append(Variable(label))

  def set_value(self, label:str, value):
    variable = self.__get_by_name(label)
    if variable is None:
      handle_error(ErrorCodes.VARIABLE_DONT_EXIST, f"Variable with name '{label}' doesn't exists in frame of type '{self.type}'")

    variable.set_value(value)

  def get_value(self, label:str) -> Tuple[VariableTypeKey, Any]:
    variable = self.__get_by_name(label)
    if variable is None:
      handle_error(ErrorCodes.VARIABLE_DONT_EXIST, f"Variable with name '{label}' doesn't exists in frame of type '{self.type}'")

    return variable.get_value()

  def __repr__(self):
    variables = "\n\t".join([str(var) for var in self.variable_storage])
    return f"Frame({self.type}:\n\t{variables})"
