from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option
from utilities.constants import command_error
from utilities.embed import build_embed
from utilities.mysql import Process_MySQL
from utilities.mysql import sqlCreateImageCommand, sqlSelectImageCommand, sqlDeleteImageCommand, sqlSelectAllImageCommand
from utilities.server_detection import which_guild
from utilities.constants import DT_OBJ_FORMAT


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
        name="imglist",
        description="Show a list of all available image commands",
        guild_ids=[which_guild()]
    )
    async def _imglist(self, ctx: SlashContext):

        all_imgs = retrieve_all_img()
        fields = []

        for img in all_imgs:
            try:
                author = ctx.guild.get_member(user_id=int(img['author'])).mention
            except:
                author = "N/A"

            created_at = img['created_at']
            fields.append([img["img_name"], f"Image URL: {img['img_url']}\n"
                                            f"Author: {author}\n"
                                            f"Created At: {created_at.strftime(DT_OBJ_FORMAT)}"])

        embed = build_embed(
            title="List of Image Commands",
            inline=False,
            fields=fields
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="img",
        description="Use an image command",
        guild_ids=[which_guild()]
    )
    async def _doesitmatter(self, ctx: SlashContext, image_name: str):
        image = retrieve_img(image_name)

        author = ctx.guild.get_member(user_id=int(image["author"]))

        embed = build_embed(
            title=image["img_name"],
            image=image["img_url"],
            description=f"This command was created by [{author.mention}]."
        )
        await ctx.send(embed=embed)

    # Testing dynamically created sub commands
    # @commands.Cog.listener()
    # async def on_slash_command(self, ctx: SlashContext):
    #     print("somethingsdfasfas")


def setup(bot):
    bot.add_cog(ImageCommands(bot))
