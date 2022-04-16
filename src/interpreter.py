import os.path
import sys

from interpreter_objects import *
from helpers import InputFile

# Check if instructions don't have duplicit order values
def check_duplicit_instruction_order_value(instructions):
  used_order_values = []
  for instruction in instructions:
    if instruction.order in used_order_values:
      sys.exit(32)
    used_order_values.append(instruction.order)

def get_value_from_frames(frame_type: FrameTypeKey, label:str, global_frame:Frame, local_frame_stack:List[Frame], temporary_frame:Optional[Frame]) -> Tuple[VariableTypeKey, Any]:
  if frame_type == FrameTypeKey.GLOBAL:
    val_type, src_val = global_frame.get_value(label)
  elif frame_type == FrameTypeKey.LOCAL:
    if len(local_frame_stack) == 0:
      raise FrameError("Local frame doesn't exist")
    val_type, src_val = local_frame_stack[-1].get_value(label)
  elif frame_type == FrameTypeKey.TEMPORARY:
    if temporary_frame is None:
      raise FrameError("Temporary frame doesn't exist")
    val_type, src_val = temporary_frame.get_value(label)
  else:
    raise InternalError("Invalid frame indentifier")

  return val_type, src_val

def set_value_in_frames(frame_type: FrameTypeKey, label:str, value:Any, global_frame:Frame, local_frame_stack:List[Frame], temporary_frame:Optional[Frame]):
  if frame_type == FrameTypeKey.GLOBAL:
    global_frame.set_value(label, value)
  elif frame_type == FrameTypeKey.LOCAL:
    if len(local_frame_stack) == 0:
      raise FrameError("Local frame doesn't exist")
    local_frame_stack[-1].set_value(label, value)
  elif frame_type == FrameTypeKey.TEMPORARY:
    if temporary_frame is None:
      raise FrameError("Temporary frame doesn't exist")
    temporary_frame.set_value(label, value)
  else:
    raise InternalError("Invalid frame indentifier")

def is_numerical(t: VariableTypeKey):
  return t in (VariableTypeKey.INT, VariableTypeKey.FLOAT)

def binary_operation(operation:InstructionKey, argument1:Argument, argument2:Argument, argument3:Argument, global_frame:Frame, local_frame_stack:List[Frame], temporary_frame:Optional[Frame]):
  # Load first operand
  if argument2.type == ArgumentTypeKey.VAR:
    frame_type, label = argument2.value
    src_val_type1, src_val1 = get_value_from_frames(frame_type, label, global_frame, local_frame_stack, temporary_frame)
    if src_val_type1 is None:
      raise UninitializedVariable(f"First operand of {operation} is uninitialized variable")
  elif argument2.type != ArgumentTypeKey.LABEL:
    src_val1 = argument2.value
    try:
      src_val_type1 = ArgumentTypeToVariableType[argument2.type]
    except:
      raise InternalError("Invalid argument type for binary operation")
  else:
    raise InternalError("Label as argument for binary operation")

  # Load second operand
  if argument3.type == ArgumentTypeKey.VAR:
    frame_type, label = argument3.value
    src_val_type2, src_val2 = get_value_from_frames(frame_type, label, global_frame, local_frame_stack, temporary_frame)
    if src_val_type2 is None:
      raise UninitializedVariable(f"Second operand of {operation} is uninitialized variable")
  elif argument3.type != ArgumentTypeKey.LABEL:
    src_val2 = argument3.value
    try:
      src_val_type2 = ArgumentTypeToVariableType[argument3.type]
    except:
      raise InternalError("Invalid argument type for binary operation")
  else:
    raise InternalError("Label as argument for binary operation")

  # Perform operation
  if operation == InstructionKey.ADD:
    if not (is_numerical(src_val_type1) and is_numerical(src_val_type2)):
      raise BadOperandType("AND need 2 numerical type operands")

    src_val = src_val1 + src_val2
  elif operation == InstructionKey.SUB:
    if not (is_numerical(src_val_type1) and is_numerical(src_val_type2)):
      raise BadOperandType("SUB need 2 numerical type operands")

    src_val = src_val1 - src_val2
  elif operation == InstructionKey.MUL:
    if not (is_numerical(src_val_type1) and is_numerical(src_val_type2)):
      raise BadOperandType("MUL need 2 numerical type operands")

    src_val = src_val1 * src_val2
  elif operation == InstructionKey.DIV:
    if not (is_numerical(src_val_type1) and is_numerical(src_val_type2)):
      raise BadOperandType("DIV need 2 numerical type operands")

    if src_val2 == 0:
      raise BadOperation("Division by 0 is prohibited")
    src_val = src_val1 / src_val2
  elif operation == InstructionKey.IDIV:
    if not (is_numerical(src_val_type1) and is_numerical(src_val_type2)):
      raise BadOperandType("IDIV need 2 numerical type operands")

    if src_val2 == 0:
      raise BadOperation("Division by 0 is prohibited")
    src_val = int(src_val1 // src_val2)
  elif operation == InstructionKey.LT:
    if src_val_type1 == VariableTypeKey.NIL or src_val_type2 == VariableTypeKey.NIL:
      raise BadOperandType("LT can't be perform with operand nil")

    src_val = src_val1 < src_val2
  elif operation == InstructionKey.GT:
    if src_val_type1 == VariableTypeKey.NIL or src_val_type2 == VariableTypeKey.NIL:
      raise BadOperandType("GT can't be perform with operand nil")

    src_val = src_val1 > src_val2
  elif operation == InstructionKey.EQ:
    src_val = src_val1 == src_val2
  elif operation == InstructionKey.AND:
    if src_val_type1 != VariableTypeKey.BOOL or src_val_type2 != VariableTypeKey.BOOL:
      raise BadOperandType("AND operation can be performed only on bool operands")

    src_val = src_val1 and src_val2
  elif operation == InstructionKey.OR:
    if src_val_type1 != VariableTypeKey.BOOL or src_val_type2 != VariableTypeKey.BOOL:
      raise BadOperandType("OR operation can be performed only on bool operands")

    src_val = src_val1 or src_val2
  elif operation == InstructionKey.STRI2INT:
    if src_val_type1 != VariableTypeKey.STRING:
      raise BadOperandType("First operand of STRI2INT must be string")

    if src_val_type2 != VariableTypeKey.INT:
      raise BadOperandType("Second operand of STRI2INT must be int")

    if 0 > src_val2 >= len(src_val1):
      raise BadStringOperation("STRI2INT invalid character index")

    src_val = src_val1[src_val2]
  else:
    raise InternalError("Unknown binary operation")

  # Set destination variable
  if argument1.type != ArgumentTypeKey.VAR:
    raise InternalError(f"Destination for instruction {operation} must be type VAR")

  frame_type, label = argument1.value
  set_value_in_frames(frame_type, label, src_val, global_frame, local_frame_stack, temporary_frame)

def unary_operation(operation:InstructionKey, argument1:Argument, argument2:Argument, global_frame:Frame, local_frame_stack:List[Frame], temporary_frame:Frame):
  # Load operand
  if argument2.type == ArgumentTypeKey.VAR:
    frame_type, label = argument2.value
    src_val_type, src_val = get_value_from_frames(frame_type, label, global_frame, local_frame_stack, temporary_frame)
    if src_val_type is None:
      raise UninitializedVariable(f"Operand of {operation} is uninitialized variable")
  elif argument2.type != ArgumentTypeKey.LABEL:
    src_val = argument2.value
    try:
      src_val_type = ArgumentTypeToVariableType[argument2.type]
    except:
      raise InternalError("Invalid argument type for unary operation")
  else:
    raise InternalError("Label as argument for unary operation")

  # Perform operation
  if operation == InstructionKey.NOT:
    if src_val_type != VariableTypeKey.BOOL:
      raise BadOperandType("NOT operation can be performed only on bool operand")
    src_val = not src_val
  elif operation == InstructionKey.INT2CHAR:
    if src_val_type != VariableTypeKey.INT:
      raise BadOperandType("INT2CHAR operation can be performed only on int operand")

    if not (0 <= src_val <= 0x10ffff):
      raise BadStringOperation("Invalid value for INT2CHAR operation")

    src_val = chr(src_val)
  elif operation == InstructionKey.INT2FLOAT:
    if src_val_type in (VariableTypeKey.INT, VariableTypeKey.FLOAT):
      raise BadOperandType("INT2FLOAT operation can be performed only on int or float operand")

    src_val = float(src_val)
  elif operation == InstructionKey.FLOAT2INT:
    if src_val_type in (VariableTypeKey.INT, VariableTypeKey.FLOAT):
      raise BadOperandType("FLOAT2INT operation can be performed only on int or float operand")

    src_val = int(src_val)
  else:
    raise InternalError("Unknown unary operation")

  # Set destination variable
  if argument1.type != ArgumentTypeKey.VAR:
    raise InternalError(f"Destination for instruction {operation} must be type VAR")

  frame_type, label = argument1.value
  set_value_in_frames(frame_type, label, src_val, global_frame, local_frame_stack, temporary_frame)

def print_help():
  print("Print some help")

if __name__ == '__main__':
  if (len(sys.argv) == 1) or (len(sys.argv) > 3):
    sys.exit(10)

  source_data = None
  input_file = None

  for arg in sys.argv[1:]:
    if arg == "--help":
      if len(sys.argv) > 2:
        sys.exit(10)

      print_help()
      sys.exit(0)

    elif arg.startswith("--source=") and arg != "--source=":
      filepath = arg[arg.find("=") + 1:]
      if not os.path.exists(filepath) or not os.path.isfile(filepath):
        sys.exit(11)

      with open(filepath, "r", encoding="utf-8") as f:
        data = f.read()

        try:
          source_data = XML.fromstring(data)
        except:
          sys.exit(31)

    elif arg.startswith("--input=") and arg != "--input=":
      filepath = arg[arg.find("=") + 1:]
      input_file = InputFile(filepath)
    else:
      sys.exit(10)

  if source_data is None and input_file is None:
    sys.exit(11)

  if source_data is None:
    try:
      source_data = XML.fromstring(input())
    except:
      sys.exit(31)

  # If there is no input file then create empty one (connected to stdin)
  if input_file is None:
    input_file = InputFile()

  # Check program header
  if source_data.tag != "program" or not "language" in source_data.keys() or source_data.attrib["language"] != "IPPcode22":
    sys.exit(32)

  instructions:List[Instruction] = []
  labels = {}

  # Iterate over instructions in source data
  for data in source_data:
    if data.tag != "instruction":
      sys.exit(32)

    # Create new instruction from element data
    instructions.append(Instruction.from_element(data))

  # It's pointless to continue when there are no instructions
  if not instructions: sys.exit(0)

  check_duplicit_instruction_order_value(instructions)

  # Sort instructions by order value
  instructions.sort(key=lambda x: x.order)

  # Extract labels
  for idx, ins in enumerate(instructions):
    if ins.instruction == InstructionKey.LABEL:
      labels[ins.arguments[0].value] = idx

  last_instruction_index = len(instructions) - 1
  current_instruction_index = 0

  data_stack = []
  call_stack = []
  global_frame = Frame(FrameTypeKey.GLOBAL)
  local_frame_stack:List[Frame] = []
  temporary_frame:Optional[Frame] = None

  while current_instruction_index <= last_instruction_index:
    current_instruction:Instruction = instructions[current_instruction_index]
    current_instruction_index += 1

    # Labels are handles seperately so skip them
    if current_instruction.instruction == InstructionKey.LABEL:
      continue

    ################################## CREATE FRAME ####################################
    if current_instruction.instruction == InstructionKey.CREATEFRAME:
      temporary_frame = Frame(FrameTypeKey.TEMPORARY)

    ################################### PUSH FRAME #####################################
    elif current_instruction.instruction == InstructionKey.PUSHFRAME:
      if temporary_frame is None:
        raise FrameError("Temporary frame doesn't exist and can't be pushed")

      temporary_frame.type = FrameTypeKey.LOCAL
      local_frame_stack.append(temporary_frame)
      temporary_frame = None

    #################################### POP FRAME #####################################
    elif current_instruction.instruction == InstructionKey.POPFRAME:
      if len(local_frame_stack) == 0:
        raise FrameError("Can't pop frames from epty frame stack")
      temporary_frame = local_frame_stack.pop()

    ##################################### DEFVAR #######################################
    elif current_instruction.instruction == InstructionKey.DEFVAR:
      frame_type, label = current_instruction.arguments[0].value

      if frame_type == FrameTypeKey.GLOBAL:
        global_frame.create_variable(label)
      elif frame_type == FrameTypeKey.LOCAL:
        if len(local_frame_stack) == 0:
          raise FrameError("Local frame doesn't exist")
        local_frame_stack[-1].create_variable(label)
      elif frame_type == FrameTypeKey.TEMPORARY:
        if temporary_frame is None:
          raise FrameError("Temporary frame doesn't exist")
        temporary_frame.create_variable(label)
      else:
        raise InternalError("Invalid frame indentifier")

    ###################################### MOVE ########################################
    elif current_instruction.instruction == InstructionKey.MOVE:
      dest = current_instruction.arguments[0]
      src = current_instruction.arguments[1]

      if dest.type != ArgumentTypeKey.VAR:
        raise InternalError("Destination for instruction MOVE must be type VAR")

      # Get source value
      if src.type == ArgumentTypeKey.VAR:
        frame_type, label = src.value
        _, src_val = get_value_from_frames(frame_type, label, global_frame, local_frame_stack, temporary_frame)
      else:
        src_val = src.value

      # Locate destination variable
      frame_type, label = dest.value
      set_value_in_frames(frame_type, label, src_val, global_frame, local_frame_stack, temporary_frame)

    ###################################### CALL ########################################
    elif current_instruction.instruction == InstructionKey.CALL:
      dest = current_instruction.arguments[0]

      if dest.type != ArgumentTypeKey.LABEL:
        raise InternalError("Invalid value type in CALL argument")

      if dest.value not in labels.keys():
        raise UndefinedLabel(f"Label '{dest.value}' is not defined")

      call_stack.append(current_instruction_index)
      current_instruction_index = labels[dest.value]

    ##################################### RETURN #######################################
    elif current_instruction.instruction == InstructionKey.RETURN:
      if len(call_stack) == 0:
        raise CallstackError("Called RETURN on empty callstack")

      current_instruction_index = call_stack.pop()

    ###################################### PUSHS #######################################
    elif current_instruction.instruction == InstructionKey.PUSHS:
      src = current_instruction.arguments[0]

      if src.type == ArgumentTypeKey.VAR:
        frame_type, label = src.value

        if frame_type == FrameTypeKey.GLOBAL:
          _, src_val = global_frame.get_value(label)
        elif frame_type == FrameTypeKey.LOCAL:
          if len(local_frame_stack) == 0:
            raise FrameError("Local frame doesn't exist")
          _, src_val = local_frame_stack[-1].get_value(label)
        elif frame_type == FrameTypeKey.TEMPORARY:
          if temporary_frame is None:
            raise FrameError("Temporary frame doesn't exist")
          _, src_val = temporary_frame.get_value(label)
        else:
          raise InternalError("Invalid frame indentifier")
      else:
        src_val = src.value

      data_stack.append(src_val)

    ###################################### POPS ########################################
    elif current_instruction.instruction == InstructionKey.POPS:
      if len(data_stack) == 0:
        raise DatastackError("Called POPS on empty data stack")

      src_val = data_stack.pop()

      dest = current_instruction.arguments[0]
      if dest.type != ArgumentTypeKey.VAR:
        raise InternalError("Destination for instruction POPS must be type VAR")

      frame_type, label = dest.value

      if frame_type == FrameTypeKey.GLOBAL:
        global_frame.set_value(label, src_val)
      elif frame_type == FrameTypeKey.LOCAL:
        if len(local_frame_stack) == 0:
          raise FrameError("Local frame doesn't exist")
        local_frame_stack[-1].set_value(label, src_val)
      elif frame_type == FrameTypeKey.TEMPORARY:
        if temporary_frame is None:
          raise FrameError("Temporary frame doesn't exist")
        temporary_frame.set_value(label, src_val)
      else:
        raise InternalError("Invalid frame indentifier")

    ################################### Binary ops #####################################
    elif current_instruction.instruction == InstructionKey.ADD or \
        current_instruction.instruction == InstructionKey.SUB or \
        current_instruction.instruction == InstructionKey.MUL or \
        current_instruction.instruction == InstructionKey.DIV or \
        current_instruction.instruction == InstructionKey.IDIV or \
        current_instruction.instruction == InstructionKey.LT or \
        current_instruction.instruction == InstructionKey.GT or \
        current_instruction.instruction == InstructionKey.EQ or \
        current_instruction.instruction == InstructionKey.AND or \
        current_instruction.instruction == InstructionKey.OR or \
        current_instruction.instruction == InstructionKey.STRI2INT:
      binary_operation(current_instruction.instruction,
                       current_instruction.arguments[0], current_instruction.arguments[1], current_instruction.arguments[2],
                       global_frame, local_frame_stack, temporary_frame)

    ################################### Unary ops ######################################
    elif current_instruction.instruction == InstructionKey.NOT or \
        current_instruction.instruction == InstructionKey.INT2CHAR or \
        current_instruction.instruction == InstructionKey.INT2FLOAT or \
        current_instruction.instruction == InstructionKey.FLOAT2INT:
      unary_operation(current_instruction.instruction,
                      current_instruction.arguments[0], current_instruction.arguments[1],
                      global_frame, local_frame_stack, temporary_frame)

    elif current_instruction.instruction == InstructionKey.READ:
      frame_type, label = current_instruction.arguments[0].value
      input_type = current_instruction.arguments[1].value
      if input_type == ArgumentTypeKey.NIL:
        raise TypeError("Conversion type can't be nil")


    else:
      #raise InternalError(f"Invalid instruction '{current_instruction.instruction}'")
      pass

  ############## DEBUG ###################
  print("Global frame")
  print(global_frame)

  print("Local frames")
  if local_frame_stack:
    local_frame_stack.reverse()
    for frame in local_frame_stack:
      print(frame)
  else:
    print("None")

  print("Temporary frame")
  print(temporary_frame)

  print("Call stack")
  print(call_stack)

  print("Data stack")
  print(data_stack)
