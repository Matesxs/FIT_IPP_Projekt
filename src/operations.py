from typing import List, Optional

from errors import ErrorCodes, handle_error
from interpreter_objects import Argument, Frame, InstructionKey, ArgumentTypeKey, ArgumentTypeToVariableType, VariableTypeKey, Variable
from helpers import get_value_from_frames, set_value_in_frames, is_numerical, InputFile

def perform_binary_operation(operation: InstructionKey, src_val1, src_val_type1: VariableTypeKey, src_val2, src_val_type2: VariableTypeKey):
  if operation in (InstructionKey.ADD, InstructionKey.ADDS):
    if not (is_numerical(src_val_type1) and is_numerical(src_val_type2)):
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} need 2 numerical type operands")

    if src_val_type1 != src_val_type2:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} need operands of same type")

    src_val = src_val1 + src_val2
  elif operation in (InstructionKey.SUB, InstructionKey.SUBS):
    if not (is_numerical(src_val_type1) and is_numerical(src_val_type2)):
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} need 2 numerical type operands")

    if src_val_type1 != src_val_type2:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} need operands of same type")

    src_val = src_val1 - src_val2
  elif operation in (InstructionKey.MUL, InstructionKey.MULS):
    if not (is_numerical(src_val_type1) and is_numerical(src_val_type2)):
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} need 2 numerical type operands")

    if src_val_type1 != src_val_type2:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} need operands of same type")

    src_val = src_val1 * src_val2
  elif operation in (InstructionKey.DIV, InstructionKey.DIVS):
    if not (is_numerical(src_val_type1) and is_numerical(src_val_type2)):
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} need 2 numerical type operands")

    if src_val_type1 != src_val_type2:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} need operands of same type")

    if src_val2 == 0:
      handle_error(ErrorCodes.BAD_OPERAND_VALUE, "Division by 0 is prohibited")
    src_val = src_val1 / src_val2
  elif operation in (InstructionKey.IDIV, InstructionKey.IDIVS):
    if not (is_numerical(src_val_type1) and is_numerical(src_val_type2)):
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} need 2 numerical type operands")

    if src_val_type1 != src_val_type2:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} need operands of same type")

    if src_val2 == 0:
      handle_error(ErrorCodes.BAD_OPERAND_VALUE, "Division by 0 is prohibited")
    src_val = int(src_val1 // src_val2)
  elif operation in (InstructionKey.LT, InstructionKey.LTS):
    if src_val_type1 == VariableTypeKey.NIL or src_val_type2 == VariableTypeKey.NIL:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} can't be perform with operand nil")

    if src_val_type1 != src_val_type2:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} can't be perform on operands with different types")

    src_val = src_val1 < src_val2
  elif operation in (InstructionKey.GT, InstructionKey.GTS):
    if src_val_type1 == VariableTypeKey.NIL or src_val_type2 == VariableTypeKey.NIL:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} can't be perform with operand nil")

    if src_val_type1 != src_val_type2:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} can't be perform on operands with different types")

    src_val = src_val1 > src_val2
  elif operation in (InstructionKey.EQ, InstructionKey.EQS):
    if src_val_type1 != VariableTypeKey.NIL and src_val_type2 != VariableTypeKey.NIL:
      if src_val_type1 != src_val_type2:
        handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} can't be perform on operands with different types withou one being nil")

    src_val = src_val1 == src_val2
  elif operation in (InstructionKey.AND, InstructionKey.ANDS):
    if src_val_type1 != VariableTypeKey.BOOL or src_val_type2 != VariableTypeKey.BOOL:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} operation can be performed only on bool operands")

    src_val = src_val1 and src_val2
  elif operation in (InstructionKey.OR, InstructionKey.ORS):
    if src_val_type1 != VariableTypeKey.BOOL or src_val_type2 != VariableTypeKey.BOOL:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} operation can be performed only on bool operands")

    src_val = src_val1 or src_val2
  elif operation in (InstructionKey.STRI2INT, InstructionKey.STRI2INTS):
    if src_val_type1 != VariableTypeKey.STRING:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"First operand of {operation.name} must be string")

    if src_val_type2 != VariableTypeKey.INT:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"Second operand of {operation.name} must be int")

    if 0 > src_val2 or src_val2 >= len(src_val1):
      handle_error(ErrorCodes.BAD_STRING_OPERATION, f"{operation.name} invalid character index")

    src_val = ord(src_val1[src_val2])
  elif operation == InstructionKey.CONCAT:
    if src_val_type1 != VariableTypeKey.STRING or src_val_type2 != VariableTypeKey.STRING:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "Operands for operation CONCAT must be string")

    src_val = src_val1 + src_val2
  elif operation == InstructionKey.GETCHAR:
    if src_val_type1 != VariableTypeKey.STRING:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "First operand for operation GETCHAR must be string")

    if src_val_type2 != VariableTypeKey.INT:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "Second operand for operation GETCHAR must be int")

    try:
      length_of_string = len(src_val1)

      if 0 > int(src_val2) >= length_of_string:
        handle_error(ErrorCodes.BAD_STRING_OPERATION, "Char index is invalid")

      src_val = src_val1[int(src_val2)]
    except:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"Failed to get char on position {src_val2} in string '{src_val1}'")
      raise
  else:
    handle_error(ErrorCodes.INTERN, "Unknown binary operation")
    raise

  return src_val

def stack_binary_operation(operation:InstructionKey, data_stack:list):
  arg2 = Variable("arg2")
  arg2.set_value(data_stack.pop())
  arg1 = Variable("arg1")
  arg1.set_value(data_stack.pop())

  arg1_type, arg1_val = arg1.get_value()
  arg2_type, arg2_val = arg2.get_value()

  src_val = perform_binary_operation(operation, arg1_val, arg1_type, arg2_val, arg2_type)
  data_stack.append(src_val)

def binary_operation(operation:InstructionKey, argument1:Argument, argument2:Argument, argument3:Argument, global_frame:Frame, local_frame_stack:List[Frame], temporary_frame:Optional[Frame]):
  # Load first operand
  if argument2.type == ArgumentTypeKey.VAR:
    frame_type, label = argument2.value
    src_val_type1, src_val1 = get_value_from_frames(frame_type, label, global_frame, local_frame_stack, temporary_frame)
    if src_val_type1 is None:
      handle_error(ErrorCodes.MISSING_VALUE, f"First operand of {operation} is uninitialized variable")
  elif argument2.type not in (ArgumentTypeKey.LABEL, ArgumentTypeKey.TYPE):
    src_val1 = argument2.value
    try:
      src_val_type1 = ArgumentTypeToVariableType[argument2.type]
    except:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "Invalid argument type for binary operation")
      raise
  else:
    handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{argument2.type} as argument for binary operation")
    raise

  # Load second operand
  if argument3.type == ArgumentTypeKey.VAR:
    frame_type, label = argument3.value
    src_val_type2, src_val2 = get_value_from_frames(frame_type, label, global_frame, local_frame_stack, temporary_frame)
    if src_val_type2 is None:
      handle_error(ErrorCodes.MISSING_VALUE, f"Second operand of {operation} is uninitialized variable")
  elif argument3.type not in (ArgumentTypeKey.LABEL, ArgumentTypeKey.TYPE):
    src_val2 = argument3.value
    try:
      src_val_type2 = ArgumentTypeToVariableType[argument3.type]
    except:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "Invalid argument type for binary operation")
      raise
  else:
    handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{argument3.type} as argument for binary operation")
    raise

  # Perform operation
  if operation == InstructionKey.SETCHAR:
    frame_type, label = argument1.value
    input_value_type, input_value = get_value_from_frames(frame_type, label, global_frame, local_frame_stack, temporary_frame)

    if input_value_type != VariableTypeKey.STRING:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "Input value for SETCHAR must be string")

    if src_val_type1 != VariableTypeKey.INT:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "First operand for operation SETCHAR must be int")

    if src_val_type2 != VariableTypeKey.STRING:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "Second operand for operation SETCHAR must be string")

    try:
      if len(src_val2) == 0:
        handle_error(ErrorCodes.BAD_STRING_OPERATION, "String with replace character is empty")

      length_of_input = len(input_value)

      if 0 > int(src_val1) >= length_of_input:
        handle_error(ErrorCodes.BAD_STRING_OPERATION, "Char index is invalid")

      input_value[int(src_val1)] = src_val2[0]
      src_val = input_value
    except:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"Failed to set char on position {src_val1} in string '{input_value}' by first character of '{src_val2}'")
      raise
  else:
    src_val = perform_binary_operation(operation, src_val1, src_val_type1, src_val2, src_val_type2)

  # Set destination variable
  if argument1.type != ArgumentTypeKey.VAR:
    handle_error(ErrorCodes.INTERN, f"Destination for instruction {operation} must be type VAR")

  frame_type, label = argument1.value
  set_value_in_frames(frame_type, label, src_val, global_frame, local_frame_stack, temporary_frame)

def perform_unary_operation(operation: InstructionKey, src_val, src_val_type: VariableTypeKey):
  if operation in (InstructionKey.NOT, InstructionKey.NOTS):
    if src_val_type != VariableTypeKey.BOOL:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} operation can be performed only on bool operand")
    src_val = not src_val
  elif operation in (InstructionKey.INT2CHAR, InstructionKey.INT2CHARS):
    if src_val_type != VariableTypeKey.INT:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} operation can be performed only on int operand")

    if not (0 <= src_val <= 0x10ffff):
      handle_error(ErrorCodes.BAD_STRING_OPERATION, f"Invalid value for {operation.name} operation")

    src_val = chr(src_val)
  elif operation in (InstructionKey.INT2FLOAT, InstructionKey.INT2FLOATS):
    if src_val_type != VariableTypeKey.INT:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} operation can be performed only on int operand")

    try:
      src_val = float(src_val)
    except:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"Failed to convert value {src_val} to float")
  elif operation in (InstructionKey.FLOAT2INT, InstructionKey.FLOAT2INTS):
    if src_val_type != VariableTypeKey.FLOAT:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{operation.name} operation can be performed only on float operand")

    try:
      src_val = int(src_val)
    except:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"Failed to convert value {src_val} to int")
  elif operation == InstructionKey.STRLEN:
    if src_val_type != VariableTypeKey.STRING:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "STRLEN operation can be performed only on string operand")

    try:
      src_val = len(src_val)
    except:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"Failed to get length of value {src_val}")
  elif operation == InstructionKey.TYPE:
    if src_val_type is None:
      src_val = ""
    else:
      try:
        src_val = src_val_type.name.lower()
      except:
        handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"Invalid type '{src_val_type}' in TYPE operation")
  else:
    handle_error(ErrorCodes.INTERN, "Unknown unary operation")

  return src_val

def stack_unary_operation(operation:InstructionKey, data_stack:list):
  arg = Variable("arg")
  arg.set_value(data_stack.pop())

  arg_type, arg_val = arg.get_value()

  src_val = perform_unary_operation(operation, arg_val, arg_type)
  data_stack.append(src_val)

def unary_operation(operation:InstructionKey, argument1:Argument, argument2:Argument, global_frame:Frame, local_frame_stack:List[Frame], temporary_frame:Frame):
  # Load operand
  if argument2.type == ArgumentTypeKey.VAR:
    frame_type, label = argument2.value
    src_val_type, src_val = get_value_from_frames(frame_type, label, global_frame, local_frame_stack, temporary_frame)
    if src_val_type is None and operation is not InstructionKey.TYPE:
      handle_error(ErrorCodes.MISSING_VALUE, f"Operand of {operation} is uninitialized variable")
  elif argument2.type not in (ArgumentTypeKey.LABEL, ArgumentTypeKey.TYPE):
    src_val = argument2.value
    try:
      src_val_type = ArgumentTypeToVariableType[argument2.type]
    except:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "Invalid argument type for unary operation")
      raise
  else:
    handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{argument2.type} as argument for unary operation")
    raise

  # Perform operation
  src_val = perform_unary_operation(operation, src_val, src_val_type)

  # Set destination variable
  if argument1.type != ArgumentTypeKey.VAR:
    handle_error(ErrorCodes.INTERN, f"Destination for instruction {operation} must be type VAR")

  frame_type, label = argument1.value
  set_value_in_frames(frame_type, label, src_val, global_frame, local_frame_stack, temporary_frame)

def handle_read_operation(input_file: InputFile, target_type: VariableTypeKey):
  input_value = input_file.get_line()

  if input_value is None: return None
  if target_type == VariableTypeKey.NIL: return None

  if target_type == VariableTypeKey.BOOL:
    input_value = input_value.lower()
    if input_value == "true":
      return True
    else:
      return False
  elif target_type == VariableTypeKey.INT:
    try:
      return int(input_value)
    except:
      return None
  elif target_type == VariableTypeKey.FLOAT:
    try:
      return float(input_value)
    except:
      return None
  elif target_type == VariableTypeKey.STRING:
    return input_value
  else:
    handle_error(ErrorCodes.INTERN, f"Invalid type '{target_type}' for READ instruction")
    raise
