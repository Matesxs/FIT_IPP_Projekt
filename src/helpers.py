import os
import sys
from errors import ErrorCodes, handle_error

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