from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext

from utilities.constants import command_error
from utilities.embed import build_embed
from utilities.mysql import Process_MySQL
from utilities.mysql import sqlCreateImageCommand, sqlSelectImageCommand, sqlDeleteImageCommand
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
        return Process_MySQL(
            query=sqlSelectImageCommand,
            values=image_name,
            fetch="one"
        )
    except:
        raise command_error(f"Unable to locate an image command named [{image_name}].")


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
        name="imgdelete",
        description="Delete image commands you've created",
        guild_ids=[which_guild()]
    )
    async def _imgdelete(self, ctx: SlashContext, image_name: str):
        try:
            Process_MySQL(
                query=sqlDeleteImageCommand,
                values=[image_name, ctx.author_id]
            )
        except:
            raise command_error("Unable to delete this image command!")

        embed = build_embed(
            title="Delete Image Command",
            fields=[
                ["Deleted", f"You have deleted the image command [{image_name}]."]
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

        author = ctx.guild.get_member(user_id=int(image["author"]))

        embed = build_embed(
            title=image["img_name"],
            image=image["img_url"],
            description=f"This command was created by [{author.mention}]."
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(ImageCommands(bot))
