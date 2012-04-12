# -*- coding: utf-8 -*-
"""
******************
Super TN3270 Field
******************

Super TN3270 Field - stn3270.field - implements the field
manipulation on a 3270 virtual screen: read, write, verify
and find fields. 
"""

class Field:
    """It's a representation of a 3270 field, with a *start of field* sequence, 
    its position (*row* and *column*), raw *text* and its ASCII *data* representation
    
    :param start_of_field: a 3270 SF sequence
    :param row: starting row of the field
    :param col: starting column of the field
    :param text: raw text of the field
    :param filler: ASCII character used to fill empty editable field
    :type start_of_field: string
    :type row: int
    :type col: int
    :type text: string
    :type filler: string
    """ 
    def __init__(self, start_of_field, row=None, col=None, text="", filler="_"):
        self.filler = filler
        self.start_of_field = self._SF(start_of_field)
        self.row = row
        self.col = col
        self.set_text(text)
        self.is_visible = ("c0=cd" not in start_of_field)
        self.is_editable = False
        for sf in self.start_of_field:
            self.is_editable = self.is_editable or sf in ("c0=c1","c0=cd")

    def set_text(self, text):
        """Sets the text of the field and the filtered data (text without filler characters)
        
        :param text: raw text of field
        :type text: string
        """
        self.text = text
        self.length = len(text)
        self.data = text.replace(self.filler," ").rstrip()
        return self.data

    def _SF(self, char):
        return char[3:-1].split(',')
