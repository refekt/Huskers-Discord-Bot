# TODO
# * Everything
# TODO

# def make_slowking(user: discord.Member) -> discord.File:
#     resize = (225, 225)
#
#     try:
#         avatar_thumbnail = Image.open(
#             requests.get(user.avatar_url, stream=True).raw
#         ).convert("RGBA")
#         avatar_thumbnail.thumbnail(resize, Image.ANTIALIAS)
#         # avatar_thumbnail.save("resources/images/avatar_thumbnail.png", "PNG")
#     except IOError:
#         raise CommandError("Unable to create a Slow King avatar for user!")
#
#     paste_pos = (250, 250)
#     make_slowking_filename = "make_slowking.png"
#
#     base_img = Image.open("resources/images/slowking.png").convert("RGBA")
#     base_img.paste(avatar_thumbnail, paste_pos, avatar_thumbnail)
#     base_img.save(f"resources/images/{make_slowking_filename}", "PNG")
#
#     if "Windows" in platform.platform():
#         slowking_path = f"{pathlib.Path(__file__).parent.parent.resolve()}\\resources\\images\\{make_slowking_filename}"
#     else:
#         slowking_path = f"{pathlib.Path(__file__).parent.parent.resolve()}/resources/images/{make_slowking_filename}"
#
#     with open(slowking_path, "rb") as f:
#         file = discord.File(f)
#
#     return file
