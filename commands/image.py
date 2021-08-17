import discord
from dinteractions_Paginator import Paginator
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_commands import create_option

from utilities.constants import DT_OBJ_FORMAT
from utilities.constants import ROLE_ADMIN_PROD
from utilities.constants import command_error
from utilities.constants import guild_id_list
from utilities.embed import build_embed
from utilities.mysql import Process_MySQL
from utilities.mysql import sqlCreateImageCommand, sqlSelectImageCommand, sqlDeleteImageCommand, sqlSelectAllImageCommand


def create_img(author: int, image_name: str, image_url: str):
    import validators
    if not validators.url(image_url):
        raise command_error("Invalid iamge URL format. The URL must begin with 'http' or 'https'.")

    image_formats = (".jpg", ".jpeg", ".png", ".gif", ".gifv", ".mp4")

    if not any(sub_str in image_url for sub_str in image_formats):
        raise command_error(f"Invalid image URL format. The URL must end with a [{', '.join(image_formats)}] extension.")

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


def retrieve_all_img():
    try:
        return Process_MySQL(
            query=sqlSelectAllImageCommand,
            fetch="all"
        )
    except:
        raise command_error(f"Unable to retrieve image commands.")


image_options = []
for img in retrieve_all_img():
    image_options.append(
        create_option(
            name=img["img_name"],
            description="Image command",
            required=False,
            option_type=1
        )
    )


class ImageCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name="imgcreate",
        description="Create an image command",
        guild_ids=guild_id_list()
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

    def is_valid(self, image):
        if image is None:
            return False
        else:
            return True

    @cog_ext.cog_slash(
        name="imgdelete",
        description="Delete image commands you've created",
        guild_ids=guild_id_list()
    )
    async def _imgdelete(self, ctx: SlashContext, image_name: str):
        try:
            img_author = int(retrieve_img(image_name)["source"])
        except TypeError:
            raise command_error(f"Unable to locate image [{image_name}]")

        admin = ctx.guild.get_role(ROLE_ADMIN_PROD)
        admin_delete = False
        if admin in ctx.author.roles:
            admin_delete = True
        elif not ctx.author_id == img_author:
            raise command_error(f"This command was created by [{ctx.guild.get_member(img_author).mention}] and can only be deleted by them")

        try:
            if admin_delete:
                Process_MySQL(
                    query=sqlDeleteImageCommand,
                    values=[image_name, str(img_author)]
                )
            else:
                Process_MySQL(
                    query=sqlDeleteImageCommand,
                    values=[image_name, str(ctx.author_id)]
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
        name="imglist",
        description="Show a list of all available image commands",
        guild_ids=guild_id_list()
    )
    async def _imglist(self, ctx: SlashContext):
        all_imgs = retrieve_all_img()
        pages = []

        for image in all_imgs:
            try:
                author = ctx.guild.get_member(user_id=int(image['author'])).mention
            except:
                author = "N/A"

            created_at = image['created_at']

            pages.append(build_embed(
                title=f"Image: {image['img_name']}",
                inline=False,
                image=image["img_url"],
                fields=[
                    ["Command Name", f"`/img img_name:{image['img_name']}`"],
                    ["Image URL", f"[URL]({image['img_url']})"],
                    ["Author", f"{author}"],
                    ["Created At", f"{created_at.strftime(DT_OBJ_FORMAT)}"]
                ]
            ))

        await Paginator(
            bot=ctx.bot,
            ctx=ctx,
            pages=pages,
            useIndexButton=True,
            useSelect=False,
            firstStyle=ButtonStyle.gray,
            nextStyle=ButtonStyle.gray,
            prevStyle=ButtonStyle.gray,
            lastStyle=ButtonStyle.gray,
            indexStyle=ButtonStyle.gray
        )

    @cog_ext.cog_slash(
        name="img",
        description="Use an image command",
        guild_ids=guild_id_list()
    )
    async def _img(self, ctx: SlashContext, image_name: str):
        image = retrieve_img(image_name)

        if not self.is_valid(image):
            await ctx.send(f"Unable to find an image command [{image_name}]", hidden=True)

        author = ctx.guild.get_member(user_id=int(image["author"]))
        if author is None:
            author = "Unknown"

        if ".gifv" in image["img_url"]:
            gifv = True
        else:
            gifv = False

        embed = build_embed(
            title=image["img_name"],
            image=image["img_url"],
            type="gifv" if gifv else "image",
            description=f"This command was created by [{author.mention if type(author) == discord.Member else author}]."
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(ImageCommands(bot))
