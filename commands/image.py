from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext

from utilities.constants import command_error
from utilities.embed import build_embed
from utilities.mysql import Process_MySQL
from utilities.mysql import sqlCreateImageCommand, sqlSelectImageCommand
from utilities.server_detection import which_guild


def create_img(author: int, image_name: str, image_url: str):
    import validators
    if not validators.url(image_url):
        raise command_error("Invalid iamge URL format. The URL must begin with 'http' or 'https'.")

    image_formats = (".jpg", ".jpeg", ".png", ".gif", ".gifv")

    if not any(sub_str in image_url for sub_str in image_formats):
        raise command_error(f"Invalid image URL fomrat. The URL must end with a [{', '.join(image_formats)}] extension.")

    try:
        Process_MySQL(
            query=sqlCreateImageCommand,
            values=[author, image_name, image_url]
        )
    except:
        raise command_error("Unable to create image command in MySQL database!")


def retrieve_img(image_name: str):
    try:
        image = Process_MySQL(
            query=sqlSelectImageCommand,
            fetch="one",
            values=[image_name]
        )
    except:
        raise command_error(f"Unable to locate an image command named [{image_name}].")

    return image


class ImageCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name="imgcreate",
        description="Create an image command",
        guild_ids=[which_guild()]
    )
    async def _imgcreate(self, ctx: SlashContext, image_name: str, image_url: str):
        create_img(ctx.author_id, image_name, image_url)

        embed = build_embed(
            title="Create an Image Command",
            image=image_url,
            fields=[
                ["Image Created!", f"Congratulations, [{ctx.author.mention}] created the [{image_name}] command!"]
            ]
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="img",
        description="Use an image command",
        guild_ids=[which_guild()]
    )
    async def _img(self, ctx: SlashContext, image_name: str):
        image = retrieve_img(image_name)
        print()


def setup(bot):
    bot.add_cog(ImageCommands(bot))
