from interpreter_objects import *

if __name__ == '__main__':
  arg1 = Argument.from_string("float@0x1.2000000p+0")
  arg2 = Argument.from_string("float@1.2222222222")
  arg3 = Argument.from_string("int@12")
  arg4 = Argument.from_string("int@-15")
  arg5 = Argument.from_string("float@-1.2222222222")
  arg6 = Argument.from_string("string@some test string")
  arg7 = Argument.from_string("bool@true")
  arg8 = Argument.from_string("nil@nil")
  arg9 = Argument.from_string("string@Proměnná\\032GF@counter\\032obsahuje\\032")
  print(arg1)
  print(arg2)
  print(arg3)
  print(arg4)
  print(arg5)
  print(arg6)
  print(arg7)
  print(arg8)
  print(arg9)

  ins1 = Instruction(InstructionKey.CREATEFRAME)
  ins2 = Instruction(InstructionKey.MOVE, [arg1, arg2, arg3])

  print(ins1)
  print(ins2)
