# -*- coding: utf-8 -*-

################################################################################
# Super TN3270 - stn3270 - is a thin layer on top of py3270 that 
# enables a simpler navigation over virtual 3270 connections.
# Copyright (C) 2012 Alexandre Drummond
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
################################################################################

"""
**********************
Super TN3270 Navigator
**********************

Super TN3270 Navigator - stn3270.navigator - implements the core
funcitonality of stn3270, which is retrieving data from and
posting data to a 3270 terminal emulator. 
"""

from py3270 import EmulatorBase
import re
from field import *

class Emulator(EmulatorBase):
    """Represents a virtual 3270 terminal and its operations.
    
    Create an Emulator with:
    
    :param visible: Defines if the virtual 3270 terminal must be visible or run in background.
    :type visible: Boolean
    
    .. IMPORTANT::
       It needs x3270 and s3270 command line tools installed to work.
    """
    x3270_executable = '/usr/bin/x3270'
    s3270_executable = '/usr/bin/s3270'

class Navigator:
    """Automates the navigation between screens, fills text fields, get
    field contents from screen.
    
    To create a Navigator you need:
    
    :param emulator: an Emulator instance
    :param host: host IP or name
    :param label_pattern: a regular expression to identify a label from a
        text field. The label field must be identified by LABELNEXT*id* when
        the label comes after the field or identified by LABELPREV*id* when
        the label comes before the field. Use @ character to identify a
        visible field or _ to identify an invisible one.
    :type emulator: Emulator
    :type host: string
    :type label_pattern: string
    """    
    def __init__(self, emulator, host='10.3.10.3', 
                 label_pattern=r'(\(?\s*(_|@)\s*\)?\s+(?P<LABELNEXT1>.*))|((?P<LABELPREV2>.*?)\s*(:|-->|==>)@)'):
        self.emulator = emulator
        if not self.emulator.status.connection_state:
            self.emulator.connect(host)
        self.rows = int(self.emulator.status.row_number)
        self.cols = int(self.emulator.status.col_number)
        self.label_pattern = label_pattern

    def send(self, command):
        self.emulator.exec_command(command)
        self.emulator.wait_for_field()
        self.screen = self.emulator.exec_command('Ascii').data
        self.buffer = self.emulator.exec_command('ReadBuffer(Ascii)').data
        fields = self._process_fields(self.buffer)
        self.screen_map = self._process_labels(fields, self.label_pattern)
        ## retornar array de campos editáveis com o filter

    def _process_fields(self, input_buffer):
        buffer = [line.split() for line in input_buffer]
        fields = []
        field = None
        for row in range(self.rows):
            for col in range(self.cols):
                if self._is_start_of_field(buffer[row][col]):
                    if field is not None:
                        field.set_text(self.text_from_screen(field.row, field.col, *self._end_of_field_position(row,col)))
                        fields.append(field)
                    field = Field(buffer[row][col], *self._start_of_field_position(row,col))
        return fields

    def _is_start_of_field(self, char):
        return char[:2] == 'SF'

    def _start_of_field_position(self, sf_row, sf_col):
        if sf_col == self.cols - 1:
            result_row = sf_row + 1
            result_col = 0
        else:
            result_row = sf_row
            result_col = sf_col + 1
        return result_row, result_col

    def _end_of_field_position(self, sf_row, sf_col):
        if sf_col == 0:
            result_row = sf_row - 1
            result_col = self.cols - 1
        else:
            result_row = sf_row
            result_col = sf_col - 1
        return result_row, result_col
    
    def text_from_screen(self, start_row, start_col, end_row, end_col):
        if end_col < self.cols and end_row < self.rows and \
                (start_row < end_row or (start_row == end_row and start_col <= end_col)):
            row = start_row
            col = start_col
            text = ""
            while row <= end_row:
                if row == end_row:
                    text += self.screen[row][col:end_col+1]
                else:
                    text += self.screen[row][col:self.cols]
                col = 0
                row += 1
            return text
        else:
            return None

    def _process_labels(self, fields, label_pattern):
        label_re = re.compile(label_pattern)
        num_fields = len(fields)
        re_label_text = re.compile(r'(\w+(\s+\w+)*)')
        for cur_field in range(num_fields):
            text = self._format_fields_for_re(fields, cur_field)
            search_result = label_re.search(text).groupdict()
            for result in search_result:
                if search_result[result] is not None:
                    label_field = cur_field + 1 if "NEXT" in result else cur_field - 1
                    fields[cur_field].label = re_label_text.search(fields[label_field].data).groups()[0]
                    
    def _format_fields_for_re(self, fields, cur_field):
        num_fields = len(fields)
        if cur_field > 0 and fields[cur_field-1].row == fields[cur_field].row:
            previous_field = self._format_for_label_match(fields[cur_field-1])
        else:
            previous_field = ""
        if cur_field < num_fields - 1 and fields[cur_field+1].row == fields[cur_field].row:
            next_field = self._format_for_label_match(fields[cur_field+1])
        else:
            next_field = ""
        field_type_char = "@" if fields[cur_field].is_visible else "_"
        return previous_field + field_type_char + next_field
        
    def _format_for_label_match(self, str):
        return str.strip().replace("@","ø").replace("_","ø")
