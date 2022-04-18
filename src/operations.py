from typing import List, Optional

from errors import ErrorCodes, handle_error
from interpreter_objects import Argument, Frame, InstructionKey, ArgumentTypeKey, ArgumentTypeToVariableType, VariableTypeKey
from helpers import get_value_from_frames, set_value_in_frames, is_numerical

def binary_operation(operation:InstructionKey, argument1:Argument, argument2:Argument, argument3:Argument, global_frame:Frame, local_frame_stack:List[Frame], temporary_frame:Optional[Frame]):
  # Load first operand
  if argument2.type == ArgumentTypeKey.VAR:
    frame_type, label = argument2.value
    src_val_type1, src_val1 = get_value_from_frames(frame_type, label, global_frame, local_frame_stack, temporary_frame)
    if src_val_type1 is None:
      handle_error(ErrorCodes.MISSING_VALUE, f"First operand of {operation} is uninitialized variable")
  elif argument2.type != ArgumentTypeKey.LABEL:
    src_val1 = argument2.value
    try:
      src_val_type1 = ArgumentTypeToVariableType[argument2.type]
    except:
      handle_error(ErrorCodes.INTERN, "Invalid argument type for binary operation")
      raise
  else:
    handle_error(ErrorCodes.INTERN, "Label as argument for binary operation")
    raise

  # Load second operand
  if argument3.type == ArgumentTypeKey.VAR:
    frame_type, label = argument3.value
    src_val_type2, src_val2 = get_value_from_frames(frame_type, label, global_frame, local_frame_stack, temporary_frame)
    if src_val_type2 is None:
      handle_error(ErrorCodes.MISSING_VALUE, f"Second operand of {operation} is uninitialized variable")
  elif argument3.type != ArgumentTypeKey.LABEL:
    src_val2 = argument3.value
    try:
      src_val_type2 = ArgumentTypeToVariableType[argument3.type]
    except:
      handle_error(ErrorCodes.INTERN, "Invalid argument type for binary operation")
      raise
  else:
    handle_error(ErrorCodes.INTERN, "Label as argument for binary operation")
    raise

  # Perform operation
  if operation == InstructionKey.ADD:
    if not (is_numerical(src_val_type1) and is_numerical(src_val_type2)):
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "AND need 2 numerical type operands")

    src_val = src_val1 + src_val2
  elif operation == InstructionKey.SUB:
    if not (is_numerical(src_val_type1) and is_numerical(src_val_type2)):
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "SUB need 2 numerical type operands")

    src_val = src_val1 - src_val2
  elif operation == InstructionKey.MUL:
    if not (is_numerical(src_val_type1) and is_numerical(src_val_type2)):
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "MUL need 2 numerical type operands")

    src_val = src_val1 * src_val2
  elif operation == InstructionKey.DIV:
    if not (is_numerical(src_val_type1) and is_numerical(src_val_type2)):
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "DIV need 2 numerical type operands")

    if src_val2 == 0:
      handle_error(ErrorCodes.BAD_OPERAND_VALUE, "Division by 0 is prohibited")
    src_val = src_val1 / src_val2
  elif operation == InstructionKey.IDIV:
    if not (is_numerical(src_val_type1) and is_numerical(src_val_type2)):
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "IDIV need 2 numerical type operands")

    if src_val2 == 0:
      handle_error(ErrorCodes.BAD_OPERAND_VALUE, "Division by 0 is prohibited")
    src_val = int(src_val1 // src_val2)
  elif operation == InstructionKey.LT:
    if src_val_type1 == VariableTypeKey.NIL or src_val_type2 == VariableTypeKey.NIL:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "LT can't be perform with operand nil")

    src_val = src_val1 < src_val2
  elif operation == InstructionKey.GT:
    if src_val_type1 == VariableTypeKey.NIL or src_val_type2 == VariableTypeKey.NIL:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "GT can't be perform with operand nil")

    src_val = src_val1 > src_val2
  elif operation == InstructionKey.EQ:
    src_val = src_val1 == src_val2
  elif operation == InstructionKey.AND:
    if src_val_type1 != VariableTypeKey.BOOL or src_val_type2 != VariableTypeKey.BOOL:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "AND operation can be performed only on bool operands")

    src_val = src_val1 and src_val2
  elif operation == InstructionKey.OR:
    if src_val_type1 != VariableTypeKey.BOOL or src_val_type2 != VariableTypeKey.BOOL:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "OR operation can be performed only on bool operands")

    src_val = src_val1 or src_val2
  elif operation == InstructionKey.STRI2INT:
    if src_val_type1 != VariableTypeKey.STRING:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "First operand of STRI2INT must be string")

    if src_val_type2 != VariableTypeKey.INT:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "Second operand of STRI2INT must be int")

    if 0 > src_val2 >= len(src_val1):
      handle_error(ErrorCodes.BAD_STRING_OPERATION, "STRI2INT invalid character index")

    src_val = src_val1[src_val2]
  else:
    handle_error(ErrorCodes.INTERN, "Unknown binary operation")
    raise

  # Set destination variable
  if argument1.type != ArgumentTypeKey.VAR:
    handle_error(ErrorCodes.INTERN, f"Destination for instruction {operation} must be type VAR")

  frame_type, label = argument1.value
  set_value_in_frames(frame_type, label, src_val, global_frame, local_frame_stack, temporary_frame)

def unary_operation(operation:InstructionKey, argument1:Argument, argument2:Argument, global_frame:Frame, local_frame_stack:List[Frame], temporary_frame:Frame):
  # Load operand
  if argument2.type == ArgumentTypeKey.VAR:
    frame_type, label = argument2.value
    src_val_type, src_val = get_value_from_frames(frame_type, label, global_frame, local_frame_stack, temporary_frame)
    if src_val_type is None:
      handle_error(ErrorCodes.MISSING_VALUE, f"Operand of {operation} is uninitialized variable")
  elif argument2.type != ArgumentTypeKey.LABEL:
    src_val = argument2.value
    try:
      src_val_type = ArgumentTypeToVariableType[argument2.type]
    except:
      handle_error(ErrorCodes.INTERN, "Invalid argument type for unary operation")
      raise
  else:
    handle_error(ErrorCodes.INTERN, "Label as argument for unary operation")
    raise

  # Perform operation
  if operation == InstructionKey.NOT:
    if src_val_type != VariableTypeKey.BOOL:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "NOT operation can be performed only on bool operand")
    src_val = not src_val
  elif operation == InstructionKey.INT2CHAR:
    if src_val_type != VariableTypeKey.INT:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "INT2CHAR operation can be performed only on int operand")

    if not (0 <= src_val <= 0x10ffff):
      handle_error(ErrorCodes.BAD_STRING_OPERATION, "Invalid value for INT2CHAR operation")

    src_val = chr(src_val)
  elif operation == InstructionKey.INT2FLOAT:
    if src_val_type != VariableTypeKey.INT:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "INT2FLOAT operation can be performed only on int operand")

    try:
      src_val = float(src_val)
    except:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"Failed to convert value {src_val} to float")
  elif operation == InstructionKey.FLOAT2INT:
    if src_val_type != VariableTypeKey.FLOAT:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, "FLOAT2INT operation can be performed only on float operand")

    try:
      src_val = int(src_val)
    except:
      handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"Failed to convert value {src_val} to int")
  else:
    handle_error(ErrorCodes.INTERN, "Unknown unary operation")

  # Set destination variable
  if argument1.type != ArgumentTypeKey.VAR:
    handle_error(ErrorCodes.INTERN, f"Destination for instruction {operation} must be type VAR")

  frame_type, label = argument1.value
  set_value_in_frames(frame_type, label, src_val, global_frame, local_frame_stack, temporary_frame)