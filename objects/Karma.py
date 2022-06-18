# TODO
# This is for server karma

from objects.Logger import discordLogger

logger = discordLogger(__name__)

# __all__ = [""]

logger.info(f"{str(__name__).title()} module loaded!")

# from typing import AnyStr
#
# from objects.Exceptions import CommandException, UserInputException
# # from helpers.mysql import sqlUpdateKarma, Process_MySQL
# from helpers.mysql import processMySQL
#
# class KarmaUser:
#     weight_msg = 0.25
#     weight_react = 1
#
#     def __init__(
#         self, user_id: int, user_name: AnyStr, positive: float, negative: float
#     ):
#         self.user_id = user_id
#         self.user_name = user_name
#         self.positive = positive
#         self.negative = negative
#         self.total = positive * negative
#
#     def update(self, msg: bool = False, react: bool = False) -> None:
#
#         if msg and not react:
#             value = self.weight_msg
#         elif react and not msg:
#             value = self.weight_react
#         else:
#             logger.exception("Unable to update karma.", exc_info=True)
#
#         Process_MySQL(query=sqlUpdateKarma, values=value)
