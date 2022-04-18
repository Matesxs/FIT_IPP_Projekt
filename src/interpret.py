import os.path
import sys
import xml.etree.ElementTree as XML
from typing import List, Optional
import argparse

from interpreter_objects import Instruction, InstructionKey, Frame, FrameTypeKey, ArgumentTypeKey, ArgumentTypeToVariableType, VariableTypeKey, Variable
from errors import ErrorCodes, handle_error
from helpers import InputFile, set_value_in_frames, get_value_from_frames
from operations import unary_operation, binary_operation, handle_read_operation, stack_binary_operation, stack_unary_operation
from stats import aggregate_stats, save_stats, get_inst_counter

# Check if instructions don't have duplicit order values or not zero
def check_duplicit_instruction_order_value(instructions):
  used_order_values = []
  for instruction in instructions:
    if instruction.order in used_order_values or instruction.order == 0:
      handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{instruction.instruction}' with zero order")
    used_order_values.append(instruction.order)

argument_parser = argparse.ArgumentParser(description="Program to interpret XML formated reprezentation of IPPCode22", add_help=False)
argument_parser.add_argument("--help", required=False, action="store_true", help="Print help")
argument_parser.add_argument("--source", type=str, required=False, help="Path to XML source file")
argument_parser.add_argument("--input", type=str, required=False, help="Path to file with predefined inputs")
argument_parser.add_argument("--stats", type=str, required=False, help="Path to stats file")
argument_parser.add_argument("--hot", required=False, action="store_true", help="Stats flag: print order of most called instruction")
argument_parser.add_argument("--vars", required=False, action="store_true", help="Stats flag: print maximum number of initialized variables")
argument_parser.add_argument("--insts", required=False, action="store_true", help="Stats flag: print number of instruction calls")

if __name__ == '__main__':
  arguments = argument_parser.parse_args()

  if arguments.help:
    if len(sys.argv) > 2:
      handle_error(ErrorCodes.BAD_ARG, "Incompatible combination of arguments")
    argument_parser.print_help()
    sys.exit(0)

  if not arguments.stats and arguments.hot:
    handle_error(ErrorCodes.BAD_ARG, "Incompatible combination of arguments, missing stats argument")

  source_data = None
  input_file = None

  if arguments.input:
    input_file = InputFile(arguments.input)

  if arguments.source:
    if not os.path.exists(arguments.source) or not os.path.isfile(arguments.source):
      handle_error(ErrorCodes.INPUT_FILE, f"Failed to locate input source file '{arguments.source}'")

    with open(arguments.source, "r", encoding="utf-8") as f:
      data = f.read()

      try:
        source_data = XML.fromstring(data)
      except:
        handle_error(ErrorCodes.XML_INPUT_FORMAT, "Bad format of source file")

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

  def get_num_of_init_variables():
    global_cnt = 0
    global_cnt += global_frame.get_number_of_initialized_variables()

    for local_frame in local_frame_stack:
      global_cnt += local_frame.get_number_of_initialized_variables()

    if temporary_frame is not None:
      global_cnt += temporary_frame.get_number_of_initialized_variables()

    return global_cnt

  last_instruction:Optional[Instruction] = None

  while current_instruction_index <= last_instruction_index:
    current_instruction:Instruction = instructions[current_instruction_index]
    current_instruction_index += 1

    # Labels are handles seperately so skip them
    if current_instruction.instruction == InstructionKey.LABEL:
      continue

    ################################## CREATE FRAME ####################################
    if current_instruction.instruction == InstructionKey.CREATEFRAME:
      if len(current_instruction.arguments) != 0:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      temporary_frame = Frame(FrameTypeKey.TEMPORARY)

    ################################### PUSH FRAME #####################################
    elif current_instruction.instruction == InstructionKey.PUSHFRAME:
      if len(current_instruction.arguments) != 0:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      if temporary_frame is None:
        handle_error(ErrorCodes.FRAME_DONT_EXIST, "Temporary frame doesn't exist and can't be pushed")

      temporary_frame.type = FrameTypeKey.LOCAL
      local_frame_stack.append(temporary_frame)
      temporary_frame = None

    #################################### POP FRAME #####################################
    elif current_instruction.instruction == InstructionKey.POPFRAME:
      if len(current_instruction.arguments) != 0:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

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
      if len(current_instruction.arguments) != 0:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      if len(call_stack) == 0:
        handle_error(ErrorCodes.MISSING_VALUE, "Called RETURN on empty callstack")

      current_instruction_index = call_stack.pop()

    ###################################### PUSHS #######################################
    elif current_instruction.instruction == InstructionKey.PUSHS:
      if len(current_instruction.arguments) != 1:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      src = current_instruction.arguments[0]

      src_val = None
      if src.type == ArgumentTypeKey.VAR:
        frame_type, label = src.value
        src_val_type, src_val = get_value_from_frames(frame_type, label, global_frame, local_frame_stack, temporary_frame)
        if src_val_type is None:
          handle_error(ErrorCodes.MISSING_VALUE, f"Argument of {current_instruction.instruction} is uninitialized variable")
      elif src.type not in (ArgumentTypeKey.LABEL, ArgumentTypeKey.TYPE):
        src_val = src.value
        src_val_type = ArgumentTypeToVariableType[src.type]
      else:
        handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{src.type} as argument for PUSHS instruction")

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
        current_instruction.instruction == InstructionKey.STRI2INT or \
        current_instruction.instruction == InstructionKey.CONCAT or \
        current_instruction.instruction == InstructionKey.GETCHAR or \
        current_instruction.instruction == InstructionKey.SETCHAR:
      if len(current_instruction.arguments) != 3:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      binary_operation(current_instruction.instruction,
                       current_instruction.arguments[0], current_instruction.arguments[1], current_instruction.arguments[2],
                       global_frame, local_frame_stack, temporary_frame)

    ################################### Unary ops ######################################
    elif current_instruction.instruction == InstructionKey.NOT or \
        current_instruction.instruction == InstructionKey.INT2CHAR or \
        current_instruction.instruction == InstructionKey.INT2FLOAT or \
        current_instruction.instruction == InstructionKey.FLOAT2INT or \
        current_instruction.instruction == InstructionKey.STRLEN or \
        current_instruction.instruction == InstructionKey.TYPE:
      if len(current_instruction.arguments) != 2:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      unary_operation(current_instruction.instruction,
                      current_instruction.arguments[0], current_instruction.arguments[1],
                      global_frame, local_frame_stack, temporary_frame)

    ###################################### READ ########################################
    elif current_instruction.instruction == InstructionKey.READ:
      if len(current_instruction.arguments) != 2:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      frame_type, label = current_instruction.arguments[0].value
      input_type = current_instruction.arguments[1].value

      try:
        variable_output_type = ArgumentTypeToVariableType[input_type]
      except:
        handle_error(ErrorCodes.INTERN, f"Invalid type '{input_type.name}' for instruction READ")
        raise

      src_val = handle_read_operation(input_file, variable_output_type)
      set_value_in_frames(frame_type, label, src_val, global_frame, local_frame_stack, temporary_frame)

    ##################################### WRITE ########################################
    elif current_instruction.instruction == InstructionKey.WRITE:
      if len(current_instruction.arguments) != 1:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      src = current_instruction.arguments[0]

      src_val_type = src_val = None
      if src.type == ArgumentTypeKey.VAR:
        frame_type, label = src.value
        src_val_type, src_val = get_value_from_frames(frame_type, label, global_frame, local_frame_stack, temporary_frame)
        if src_val_type is None:
          handle_error(ErrorCodes.MISSING_VALUE, f"Argument of {current_instruction.instruction} is uninitialized variable")
      elif src.type not in (ArgumentTypeKey.LABEL, ArgumentTypeKey.TYPE):
        src_val = src.value
        src_val_type = ArgumentTypeToVariableType[src.type]
      else:
        handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{src.type} as argument for WRITE instruction")

      if src_val_type == VariableTypeKey.NIL:
        print("", end="")
      elif src_val_type == VariableTypeKey.BOOL:
        print("true" if src_val else "false", end="")
      else:
        print(str(src_val), end="")

    ###################################### JUMP ########################################
    elif current_instruction.instruction == InstructionKey.JUMP:
      if len(current_instruction.arguments) != 1:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      # Check label
      src = current_instruction.arguments[0]

      if src.type != ArgumentTypeKey.LABEL:
        handle_error(ErrorCodes.BAD_OPERAND_TYPE, "Jump operation need label as first argument")

      if src.value not in labels.keys():
        handle_error(ErrorCodes.SEMANTIC_ERROR, f"Label {src.value} is undefined")

      current_instruction_index = labels[src.value]

    #################################### JUMPIFEQ ######################################
    ################################### JUMPIFNEQ ######################################
    elif current_instruction.instruction == InstructionKey.JUMPIFEQ or \
        current_instruction.instruction == InstructionKey.JUMPIFNEQ:
      if len(current_instruction.arguments) != 3:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      # Check label
      label_src = current_instruction.arguments[0]

      if label_src.type != ArgumentTypeKey.LABEL:
        handle_error(ErrorCodes.BAD_OPERAND_TYPE, "Jump operation need label as first argument")

      if label_src.value not in labels.keys():
        handle_error(ErrorCodes.SEMANTIC_ERROR, f"Label {label_src.value} is undefined")

      # Load operands
      operand1 = None
      operand2 = None
      operand1_type = None
      operand2_type = None

      if current_instruction.arguments[1].type == ArgumentTypeKey.VAR:
        frame_type, label = current_instruction.arguments[1].value
        operand1_type, operand1 = get_value_from_frames(frame_type, label, global_frame, local_frame_stack, temporary_frame)
        if operand1_type is None:
          handle_error(ErrorCodes.MISSING_VALUE, f"Argument of {current_instruction.instruction} is uninitialized variable")
      elif current_instruction.arguments[1].type not in (ArgumentTypeKey.LABEL, ArgumentTypeKey.TYPE):
        operand1 = current_instruction.arguments[1].value
        operand1_type = ArgumentTypeToVariableType[current_instruction.arguments[1].type]
      else:
        handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{current_instruction.arguments[1].type} as argument for {current_instruction.instruction.name} instruction")

      if current_instruction.arguments[2].type == ArgumentTypeKey.VAR:
        frame_type, label = current_instruction.arguments[2].value
        operand2_type, operand2 = get_value_from_frames(frame_type, label, global_frame, local_frame_stack, temporary_frame)
        if operand2_type is None:
          handle_error(ErrorCodes.MISSING_VALUE, f"Argument of {current_instruction.instruction} is uninitialized variable")
      elif current_instruction.arguments[2].type not in (ArgumentTypeKey.LABEL, ArgumentTypeKey.TYPE):
        operand2 = current_instruction.arguments[2].value
        operand2_type = ArgumentTypeToVariableType[current_instruction.arguments[2].type]
      else:
        handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{current_instruction.arguments[2].type} as argument for {current_instruction.instruction.name} instruction")

      if operand2_type != operand1_type and operand1_type != VariableTypeKey.NIL and operand2_type != VariableTypeKey.NIL:
        handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"Incompatible type {operand1_type} and {operand2_type} in operation {current_instruction.instruction.name}")

      if current_instruction.instruction == InstructionKey.JUMPIFEQ:
        if operand1 == operand2:
          current_instruction_index = labels[label_src.value]
      elif current_instruction.instruction == InstructionKey.JUMPIFNEQ:
        if operand1 != operand2:
          current_instruction_index = labels[label_src.value]
      else:
        handle_error(ErrorCodes.INTERN, "Invalid operation received, expected JUMPIFEQ/JUMPIFNEQ")

    ###################################### EXIT ########################################
    elif current_instruction.instruction == InstructionKey.EXIT:
      if len(current_instruction.arguments) != 1:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      src = current_instruction.arguments[0]

      src_val_type = src_val = None
      if src.type == ArgumentTypeKey.VAR:
        frame_type, label = src.value
        src_val_type, src_val = get_value_from_frames(frame_type, label, global_frame, local_frame_stack, temporary_frame)
        if src_val_type is None:
          handle_error(ErrorCodes.MISSING_VALUE, f"Argument of {current_instruction.instruction} is uninitialized variable")
      elif src.type not in (ArgumentTypeKey.LABEL, ArgumentTypeKey.TYPE):
        src_val = src.value
        src_val_type = ArgumentTypeToVariableType[src.type]
      else:
        handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{src.type} as argument for EXIT instruction")

      if src_val_type != VariableTypeKey.INT:
        handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{src.type} as argument for EXIT instruction")

      if 0 > src_val > 49:
        handle_error(ErrorCodes.BAD_OPERAND_VALUE, f"{src_val} is not valid value for EXIT operation, only int with value 0 <= x <= 49 are valid")

      if arguments.stats:
        save_stats(arguments.stats)
      sys.exit(int(src_val))

    ##################################### DPRINT #######################################
    elif current_instruction.instruction == InstructionKey.DPRINT:
      if len(current_instruction.arguments) != 1:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      src = current_instruction.arguments[0]

      src_val_type = src_val = None
      if src.type == ArgumentTypeKey.VAR:
        frame_type, label = src.value
        src_val_type, src_val = get_value_from_frames(frame_type, label, global_frame, local_frame_stack, temporary_frame)
        if src_val_type is None:
          handle_error(ErrorCodes.MISSING_VALUE, f"Argument of {current_instruction.instruction} is uninitialized variable")
      elif src.type not in (ArgumentTypeKey.LABEL, ArgumentTypeKey.TYPE):
        src_val = src.value
        src_val_type = ArgumentTypeToVariableType[src.type]
      else:
        handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"{src.type} as argument for EXIT instruction")

      if src_val_type == VariableTypeKey.NIL:
        sys.stderr.write("")
      elif src_val_type == VariableTypeKey.BOOL:
        if src_val:
          sys.stderr.write("true")
        else:
          sys.stderr.write("false")
      else:
        sys.stderr.write(str(src_val))

    ###################################### BREAK #######################################
    elif current_instruction.instruction == InstructionKey.BREAK:
      if len(current_instruction.arguments) != 0:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"\n\nDebug values\nInstruction '{current_instruction.instruction}' incorrect number of arguments")

      sys.stderr.write(f"Last instruction: {last_instruction}\n")
      sys.stderr.write(f"Code position: {last_instruction.order if last_instruction is not None else 0}\n")
      sys.stderr.write(f"Instructions executed: {get_inst_counter()}\n\n")
      sys.stderr.write(f"Global frame:\n{global_frame}\n\n")
      sys.stderr.write("Local frames:\n")
      for loc_frame in local_frame_stack:
        sys.stderr.write(f"{loc_frame}\n")
      sys.stderr.write("\nTemporary frame:\n")
      if temporary_frame is not None:
        sys.stderr.write(f"{temporary_frame}\n")

      sys.stderr.write(f"\nCall stack:\n{call_stack}\n")
      sys.stderr.write(f"Data stack:\n{data_stack}")

    ##################################### CLEARS #######################################
    elif current_instruction.instruction == InstructionKey.CLEARS:
      if len(current_instruction.arguments) != 0:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      data_stack.clear()

    ################################# Stack bin op #####################################
    elif current_instruction.instruction == InstructionKey.ADDS or \
        current_instruction.instruction == InstructionKey.SUBS or \
        current_instruction.instruction == InstructionKey.MULS or \
        current_instruction.instruction == InstructionKey.DIVS or \
        current_instruction.instruction == InstructionKey.IDIVS or \
        current_instruction.instruction == InstructionKey.LTS or \
        current_instruction.instruction == InstructionKey.GTS or \
        current_instruction.instruction == InstructionKey.EQS or \
        current_instruction.instruction == InstructionKey.ANDS or \
        current_instruction.instruction == InstructionKey.ORS or \
        current_instruction.instruction == InstructionKey.STRI2INTS:
      if len(data_stack) < 2:
        handle_error(ErrorCodes.MISSING_VALUE, f"Instruction '{current_instruction.instruction}' missing arguments on data stack")

      stack_binary_operation(current_instruction.instruction, data_stack)

    elif current_instruction.instruction == InstructionKey.NOTS or \
        current_instruction.instruction == InstructionKey.INT2CHARS or \
        current_instruction.instruction == InstructionKey.INT2FLOATS or \
        current_instruction.instruction == InstructionKey.FLOAT2INTS:
      if len(data_stack) < 1:
        handle_error(ErrorCodes.MISSING_VALUE, f"Instruction '{current_instruction.instruction}' missing arguments on data stack")

      stack_unary_operation(current_instruction.instruction, data_stack)

    #################################### JUMPIFEQS #####################################
    ################################### JUMPIFNEQS #####################################
    elif current_instruction.instruction == InstructionKey.JUMPIFEQS or \
        current_instruction.instruction == InstructionKey.JUMPIFNEQS:
      if len(current_instruction.arguments) != 1:
        handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Instruction '{current_instruction.instruction}' incorrect number of arguments")

      if len(data_stack) < 2:
        handle_error(ErrorCodes.MISSING_VALUE, f"Instruction '{current_instruction.instruction}' missing arguments on data stack")

      # Check label
      label_src = current_instruction.arguments[0]

      if label_src.type != ArgumentTypeKey.LABEL:
        handle_error(ErrorCodes.BAD_OPERAND_TYPE, "Jump operation need label as first argument")

      if label_src.value not in labels.keys():
        handle_error(ErrorCodes.SEMANTIC_ERROR, f"Label {label_src.value} is undefined")

      arg2 = Variable("arg2")
      arg2.set_value(data_stack.pop())
      arg1 = Variable("arg1")
      arg1.set_value(data_stack.pop())

      arg2_type, arg2_val = arg2.get_value()
      arg1_type, arg1_val = arg1.get_value()

      if arg1_type != arg2_type and arg1_type != VariableTypeKey.NIL and arg2_type != VariableTypeKey.NIL:
        handle_error(ErrorCodes.BAD_OPERAND_TYPE, f"Incompatible type {arg1_type} and {arg2_type} in operation {current_instruction.instruction.name}")

      if current_instruction.instruction == InstructionKey.JUMPIFEQS:
        if arg1_val == arg2_val:
          current_instruction_index = labels[label_src.value]
      elif current_instruction.instruction == InstructionKey.JUMPIFNEQS:
        if arg1_val != arg2_val:
          current_instruction_index = labels[label_src.value]
      else:
        handle_error(ErrorCodes.INTERN, "Invalid operation received, expected JUMPIFEQS/JUMPIFNEQS")

    else:
      handle_error(ErrorCodes.XML_BAD_STRUCTURE, f"Unknown operation '{current_instruction.instruction}'")

    last_instruction = current_instruction
    aggregate_stats(current_instruction, get_num_of_init_variables())

  if arguments.stats:
    save_stats(arguments.stats)
