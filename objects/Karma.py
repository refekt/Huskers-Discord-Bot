# TODO
# This is for server karma
# TODO
import logging

logger = logging.getLogger(__name__)
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
#     def update(self, msg: bool = False, react: bool = False):
#
#         if msg and not react:
#             value = self.weight_msg
#         elif react and not msg:
#             value = self.weight_react
#         else:
#             raise CommandException("Unable to update karma.")
#
#         Process_MySQL(query=sqlUpdateKarma, values=value)
