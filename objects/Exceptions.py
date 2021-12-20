# Global Errors
class CommandException(Exception):
    def __init__(self, message):
        self.message = message


class UserInputException(Exception):
    def __init__(self, message):
        self.message = message
