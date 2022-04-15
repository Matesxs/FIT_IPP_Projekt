# Raised when value conversion failed
class ConversionException(Exception):
  pass

# Raised when invalid format of string is passed and can't continue parsing it
class InvalidFormatException(Exception):
  pass