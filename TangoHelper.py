"""
helper classes to use with PyTango
"""

import sys


class StoreStdOut(object):
    """Helper Class to store last stdout message"""

    def __init__(self):
        self.terminal = sys.stdout
        self.last_message = ''

    def write(self, message):
        self.terminal.write(message)
        if message != '\n':
            self.last_message = message

    def read(self):
        return self.last_message
