""" enum for message types """
from enum import Enum


class MessageType(Enum):
    """ enum for slack message types """
    success = 0
    error = 1
    cached = 2
