import os
from typing import List, Optional, Any, Tuple

from errors import ErrorCodes, handle_error
from interpreter_objects import FrameTypeKey, Frame, VariableTypeKey

def is_numerical(t: VariableTypeKey):
  return t in (VariableTypeKey.INT, VariableTypeKey.FLOAT)

class InputFile:
  def __init__(self, file_path:str = None):
    self.input_data_file_index = -1
    self.input_file_data = None

    if file_path:
      if not os.path.exists(file_path) or not os.path.isfile(file_path):
        handle_error(ErrorCodes.INPUT_FILE, "Failed to open input file")

      with open(file_path, "r", encoding="utf-8") as f:
        self.input_file_data = f.read().split("\n")

  def get_line(self):
    if self.input_file_data is None:
      return input()
    else:
      self.input_data_file_index += 1
      if self.input_data_file_index >= len(self.input_file_data):
        return None
      return self.input_file_data[self.input_data_file_index]

def get_value_from_frames(frame_type: FrameTypeKey, label:str, global_frame:Frame, local_frame_stack:List[Frame], temporary_frame:Optional[Frame]) -> Tuple[VariableTypeKey, Any]:
  if frame_type == FrameTypeKey.GLOBAL:
    val_type, src_val = global_frame.get_value(label)
  elif frame_type == FrameTypeKey.LOCAL:
    if len(local_frame_stack) == 0:
      handle_error(ErrorCodes.FRAME_DONT_EXIST, "Local frame doesn't exist")
    val_type, src_val = local_frame_stack[-1].get_value(label)
  elif frame_type == FrameTypeKey.TEMPORARY:
    if temporary_frame is None:
      handle_error(ErrorCodes.FRAME_DONT_EXIST, "Temporary frame doesn't exist")
    val_type, src_val = temporary_frame.get_value(label)
  else:
    handle_error(ErrorCodes.INTERN, "Invalid frame indentifier")
    raise

  return val_type, src_val

def set_value_in_frames(frame_type: FrameTypeKey, label:str, value:Any, global_frame:Frame, local_frame_stack:List[Frame], temporary_frame:Optional[Frame]):
  if frame_type == FrameTypeKey.GLOBAL:
    global_frame.set_value(label, value)
  elif frame_type == FrameTypeKey.LOCAL:
    if len(local_frame_stack) == 0:
      handle_error(ErrorCodes.FRAME_DONT_EXIST, "Local frame doesn't exist")
    local_frame_stack[-1].set_value(label, value)
  elif frame_type == FrameTypeKey.TEMPORARY:
    if temporary_frame is None:
      handle_error(ErrorCodes.FRAME_DONT_EXIST, "Temporary frame doesn't exist")
    temporary_frame.set_value(label, value)
  else:
    handle_error(ErrorCodes.INTERN, "Invalid frame indentifier")