import os.path
import sys
import xml.etree.ElementTree as XML
from typing import List, Optional

from interpreter_objects import Instruction, InstructionKey, Frame, FrameTypeKey, ArgumentTypeKey
from errors import ErrorCodes, handle_error
from helpers import InputFile, set_value_in_frames, get_value_from_frames
from operations import unary_operation, binary_operation

# Check if instructions don't have duplicit order values or not zero
def check_duplicit_instruction_order_value(instructions):
  used_order_values = []
  for instruction in instructions:
    if instruction.order in used_order_values or instruction.order == 0:
      handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{instruction.instruction}' with zero order")
    used_order_values.append(instruction.order)

def print_help():
  print("Print some help")

if __name__ == '__main__':
  if (len(sys.argv) == 1) or (len(sys.argv) > 3):
    handle_error(ErrorCodes.BAD_ARG, "Missing arguments")

  source_data = None
  input_file = None

  for arg in sys.argv[1:]:
    if arg == "--help":
      if len(sys.argv) > 2:
        handle_error(ErrorCodes.BAD_ARG, "Incompatible combination of arguments")

      print_help()
      sys.exit(0)

    elif arg.startswith("--source=") and arg != "--source=":
      filepath = arg[arg.find("=") + 1:]
      if not os.path.exists(filepath) or not os.path.isfile(filepath):
        handle_error(ErrorCodes.INPUT_FILE, f"Failed to locate input source file '{filepath}'")

      with open(filepath, "r", encoding="utf-8") as f:
        data = f.read()

        try:
          source_data = XML.fromstring(data)
        except:
          handle_error(ErrorCodes.XML_INPUT_FORMAT, "Bad format of source file")

    elif arg.startswith("--input=") and arg != "--input=":
      filepath = arg[arg.find("=") + 1:]
      input_file = InputFile(filepath)
    else:
      handle_error(ErrorCodes.BAD_ARG, f"Invalid argument '{arg}'")

  if source_data is None and input_file is None:
    handle_error(ErrorCodes.BAD_ARG, "Incompatible combination of arguments")

  if source_data is None:
    try:
      source_data = XML.fromstring(sys.stdin.read())
    except:
      handle_error(ErrorCodes.XML_INPUT_FORMAT, "Bad format of source data from stdin")

  # If there is no input file then create empty one (connected to stdin)
  if input_file is None:
    input_file = InputFile()

  # Check program header
  if source_data.tag != "program" or not "language" in source_data.keys() or source_data.attrib["language"] != "IPPcode22":
    handle_error(ErrorCodes.XML_BAD_STRUCTURE, "Missing program header")

  instructions:List[Instruction] = []
  labels = {}

  # Iterate over instructions in source data
  for data in source_data:
    if data.tag not in ("instruction", "name", "description"):
      handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Unexpected structure '{data.tag}' in program body")

    # Create new instruction from element data
    if data.tag == "instruction":
      instructions.append(Instruction.from_element(data))

  # It's pointless to continue when there are no instructions
  if not instructions: sys.exit(0)

  check_duplicit_instruction_order_value(instructions)

  # Sort instructions by order value
  instructions.sort(key=lambda x: x.order)

  # for ins in instructions:
  #   print(ins)

  # Extract labels
  for idx, ins in enumerate(instructions):
    if ins.instruction == InstructionKey.LABEL:
      label_val = ins.arguments[0].value
      if label_val in labels.keys():
        handle_error(ErrorCodes.SEMANTIC_ERROR, f"Label '{label_val}' is already defined")

      labels[label_val] = idx

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
        handle_error(ErrorCodes.FRAME_DONT_EXIST, "Temporary frame doesn't exist and can't be pushed")

      temporary_frame.type = FrameTypeKey.LOCAL
      local_frame_stack.append(temporary_frame)
      temporary_frame = None

    #################################### POP FRAME #####################################
    elif current_instruction.instruction == InstructionKey.POPFRAME:
      if len(local_frame_stack) == 0:
        handle_error(ErrorCodes.FRAME_DONT_EXIST, "Can't pop frames from epty frame stack")
      temporary_frame = local_frame_stack.pop()

    ##################################### DEFVAR #######################################
    elif current_instruction.instruction == InstructionKey.DEFVAR:
      if len(current_instruction.arguments) != 1:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      frame_type, label = current_instruction.arguments[0].value

      if frame_type == FrameTypeKey.GLOBAL:
        global_frame.create_variable(label)
      elif frame_type == FrameTypeKey.LOCAL:
        if len(local_frame_stack) == 0:
          handle_error(ErrorCodes.FRAME_DONT_EXIST, "Local frame doesn't exist")
        local_frame_stack[-1].create_variable(label)
      elif frame_type == FrameTypeKey.TEMPORARY:
        if temporary_frame is None:
          handle_error(ErrorCodes.FRAME_DONT_EXIST, "Temporary frame doesn't exist")
        temporary_frame.create_variable(label)
      else:
        handle_error(ErrorCodes.INTERN, "Invalid frame indentifier")

    ###################################### MOVE ########################################
    elif current_instruction.instruction == InstructionKey.MOVE:
      if len(current_instruction.arguments) != 2:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      dest = current_instruction.arguments[0]
      src = current_instruction.arguments[1]

      if dest.type != ArgumentTypeKey.VAR:
        handle_error(ErrorCodes.INTERN, "Destination for instruction MOVE must be type VAR")

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
      if len(current_instruction.arguments) != 1:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      dest = current_instruction.arguments[0]

      if dest.type != ArgumentTypeKey.LABEL:
        handle_error(ErrorCodes.INTERN, "Invalid value type in CALL argument")

      if dest.value not in labels.keys():
        handle_error(ErrorCodes.INTERN, f"Label '{dest.value}' is not defined")

      call_stack.append(current_instruction_index)
      current_instruction_index = labels[dest.value]

    ##################################### RETURN #######################################
    elif current_instruction.instruction == InstructionKey.RETURN:
      if len(call_stack) == 0:
        handle_error(ErrorCodes.MISSING_VALUE, "Called RETURN on empty callstack")

      current_instruction_index = call_stack.pop()

    ###################################### PUSHS #######################################
    elif current_instruction.instruction == InstructionKey.PUSHS:
      if len(current_instruction.arguments) != 1:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      src = current_instruction.arguments[0]

      if src.type == ArgumentTypeKey.VAR:
        frame_type, label = src.value
        _, src_val = get_value_from_frames(frame_type, label, global_frame, local_frame_stack, temporary_frame)
      else:
        src_val = src.value

      data_stack.append(src_val)

    ###################################### POPS ########################################
    elif current_instruction.instruction == InstructionKey.POPS:
      if len(current_instruction.arguments) != 1:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      if len(data_stack) == 0:
        handle_error(ErrorCodes.MISSING_VALUE, "Called POPS on empty data stack")

      src_val = data_stack.pop()

      dest = current_instruction.arguments[0]
      if dest.type != ArgumentTypeKey.VAR:
        handle_error(ErrorCodes.INTERN, "Destination for instruction POPS must be type VAR")

      frame_type, label = dest.value
      set_value_in_frames(frame_type, label, src_val, global_frame, local_frame_stack, temporary_frame)

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
      if len(current_instruction.arguments) != 3:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      binary_operation(current_instruction.instruction,
                       current_instruction.arguments[0], current_instruction.arguments[1], current_instruction.arguments[2],
                       global_frame, local_frame_stack, temporary_frame)

    ################################### Unary ops ######################################
    elif current_instruction.instruction == InstructionKey.NOT or \
        current_instruction.instruction == InstructionKey.INT2CHAR or \
        current_instruction.instruction == InstructionKey.INT2FLOAT or \
        current_instruction.instruction == InstructionKey.FLOAT2INT:
      if len(current_instruction.arguments) != 2:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      unary_operation(current_instruction.instruction,
                      current_instruction.arguments[0], current_instruction.arguments[1],
                      global_frame, local_frame_stack, temporary_frame)

    elif current_instruction.instruction == InstructionKey.READ:
      if len(current_instruction.arguments) != 2:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

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
