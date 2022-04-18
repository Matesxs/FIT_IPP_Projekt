import sys

from interpreter_objects import Instruction, InstructionKey
from errors import ErrorCodes, handle_error

max_number_of_init_vars = 0
all_instruction_calls = 0
instruction_calls = {}

def aggregate_stats(instr: Instruction, number_of_init_variables:int):
  global all_instruction_calls
  global max_number_of_init_vars

  if number_of_init_variables > max_number_of_init_vars:
    max_number_of_init_vars = number_of_init_variables

  if instr.instruction in (InstructionKey.LABEL, InstructionKey.DPRINT, InstructionKey.BREAK):
    return

  if instr.order not in instruction_calls.keys():
    instruction_calls[instr.order] = 0
  else:
    instruction_calls[instr.order] += 1

  all_instruction_calls += 1

def get_inst_counter():
  return all_instruction_calls

def save_stats(stats_path:str):
  args = []

  for arg in sys.argv:
    if arg in ("--hot", "--insts", "--vars"):
      args.append(arg)

  # Get instruction order with most calls
  instr_order_with_max_calls = None
  max_calls = 0
  for key in instruction_calls.keys():
    val = instruction_calls.get(key)
    if val >= max_calls:
      if instr_order_with_max_calls is None or instr_order_with_max_calls > key:
        max_calls = val
        instr_order_with_max_calls = key

  try:
    with open(stats_path, "w") as f:
      for arg in args:
        if arg == "--insts":
          f.write(f"{all_instruction_calls}\n")
        elif arg == "--hot":
          if instr_order_with_max_calls is not None:
            f.write(f"{instr_order_with_max_calls}\n")
        elif arg == "--vars":
          f.write(f"{max_number_of_init_vars}\n")
  except:
    handle_error(ErrorCodes.OUTPUT_FILE, "Failed to open output file")