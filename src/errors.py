import sys
import enum
from typing import Optional

class ErrorCodes(enum.Enum):
  BAD_ARG = 10
  INPUT_FILE = 11
  OUTPUT_FILE = 12

  XML_INPUT_FORMAT = 31
  XML_BAD_STRUCTURE = 32

  # Undefined label, redefinition of variable
  SEMANTIC_ERROR = 52
  BAD_OPERAND_TYPE = 53
  VARIABLE_DONT_EXIST = 54
  FRAME_DONT_EXIST = 55
  MISSING_VALUE = 56
  BAD_OPERAND_VALUE = 57
  BAD_STRING_OPERATION = 58

  INTERN = 99

def handle_error(error_code: ErrorCodes, message:Optional[str]=None):
  if message is not None:
    sys.stderr.write(f"[Error]({error_code.name}) {message}\n")
  sys.exit(error_code.value)