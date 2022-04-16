# Raised when value conversion failed
class ConversionException(Exception):
  pass

# Raised when invalid format of string is passed and can't continue parsing it
class InvalidFormatException(Exception):
  pass

# Error in XML structure
class InvalidXMLStructure(Exception):
  pass

# Unknown instruction
class InvalidInstruction(Exception):
  pass

# Unknown type of variable
class InvalidType(Exception):
  pass

# Generic internal error that should never be triggered
class InternalError(Exception):
  pass

# Variable gets redefined in frame
class VariableRedefinition(Exception):
  pass

# Variable is not pressent in frame
class UnknownVariable(Exception):
  pass

class FrameError(Exception):
  pass

class UndefinedLabel(Exception):
  pass

class CallstackError(Exception):
  pass

class DatastackError(Exception):
  pass

class BadOperandType(Exception):
  pass

class BadOperation(Exception):
  pass

class UninitializedVariable(Exception):
  pass

class BadStringOperation(Exception):
  pass
