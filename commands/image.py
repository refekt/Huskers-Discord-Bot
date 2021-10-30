import io
import random

import discord
import markovify
import requests
import validators
from PIL import Image
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option

import utilities.fryer as fryer
from utilities.constants import (
    CommandError,
    HEADERS,
    ROLE_ADMIN_PROD,
    UserError,
    guild_id_list,
    make_slowking,
)
from utilities.embed import build_embed
from utilities.mysql import (
    Process_MySQL,
    sqlCreateImageCommand,
    sqlDeleteImageCommand,
    sqlSelectAllImageCommand,
    sqlSelectImageCommand,
)

image_formats = (".jpg", ".jpeg", ".png", ".gif", ".gifv", ".mp4")


def create_img(author: int, image_name: str, image_url: str):
    if not validators.url(image_url):
        raise UserError(
            "Invalid image URL format. The URL must begin with 'http' or 'https'."
        )

    if not any(sub_str in image_url for sub_str in image_formats):
        raise UserError(
            f"Invalid image URL format. The URL must end with a [{', '.join(image_formats)}] extension."
        )

    try:
        Process_MySQL(
            query=sqlCreateImageCommand, values=[author, image_name, image_url]
        )
    except:
        raise CommandError("Unable to create image command in MySQL database!")


def retrieve_img(image_name: str):
    try:
        return Process_MySQL(
            query=sqlSelectImageCommand, values=image_name, fetch="one"
        )
    except:
        raise UserError(f"Unable to locate an image command named [{image_name}].")


def retrieve_all_img():
    try:
        return Process_MySQL(query=sqlSelectAllImageCommand, fetch="all")
    except:
        raise CommandError(f"Unable to retrieve image commands.")


all_imgs = retrieve_all_img()

image_options = []
for img in all_imgs:
    image_options.append(
        create_option(
            name=img["img_name"],
            description="Custom image command",
            required=False,
            option_type=1,
        )
    )


def is_valid(image):
    if image is None:
        return False
    else:
        return True


class ImageCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name="imgcreate",
        description="Create an image command",
        guild_ids=guild_id_list(),
    )
    async def _imgcreate(self, ctx: SlashContext, image_name: str, image_url: str):
        if is_valid(retrieve_img(image_name)):
            raise UserError("An image with that name already exists. Try again!")

        image_name = image_name.replace(" ", "")

        create_img(ctx.author_id, image_name, image_url)

        embed = build_embed(
            title="Create an Image Command",
            image=image_url,
            fields=[
                [
                    "Image Created!",
                    f"Congratulations, [{ctx.author.mention}] created the [{image_name}] command!",
                ]
            ],
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="imgdelete",
        description="Delete image commands you've created",
        guild_ids=guild_id_list(),
    )
    async def _imgdelete(self, ctx: SlashContext, image_name: str):
        try:
            img_author = int(retrieve_img(image_name)["author"])
        except TypeError:
            raise UserError(f"Unable to locate image [{image_name}]")

        if not is_valid(img_author):
            raise UserError(f"Unable to locate image [{image_name}]")

        admin = ctx.guild.get_role(ROLE_ADMIN_PROD)
        admin_delete = False

        if admin in ctx.author.roles:
            admin_delete = True
        elif not ctx.author_id == img_author:
            raise UserError(
                f"This command was created by [{ctx.guild.get_member(img_author).mention}] and can only be deleted by them"
            )

        try:
            if admin_delete:
                Process_MySQL(
                    query=sqlDeleteImageCommand, values=[image_name, str(img_author)]
                )
            else:
                Process_MySQL(
                    query=sqlDeleteImageCommand, values=[image_name, str(ctx.author_id)]
                )
        except:
            raise CommandError("Unable to delete this image command!")

        embed = build_embed(
            title="Delete Image Command",
            fields=[["Deleted", f"You have deleted the image command [{image_name}]."]],
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="imglist",
        description="Show a list of all available image commands",
        guild_ids=guild_id_list(),
    )
    async def _imglist(self, ctx: SlashContext):
        global all_imgs
        all_imgs = retrieve_all_img()

        img_list = []
        for img in all_imgs:
            img_list.append(img["img_name"])

        img_list.sort()

        await ctx.send(", ".join(img_list), hidden=True)

        # pages = []
        #
        # for image in all_imgs:
        #     try:
        #         author = ctx.guild.get_member(user_id=int(image["author"])).mention
        #     except:
        #         author = "N/A"
        #
        #     created_at = image["created_at"]
        #
        #     pages.append(
        #         build_embed(
        #             title=f"Image: {image['img_name']}",
        #             inline=False,
        #             image=image["img_url"],
        #             fields=[
        #                 ["Command Name", f"`/img img_name:{image['img_name']}`"],
        #                 ["Image URL", f"[URL]({image['img_url']})"],
        #                 ["Author", f"{author}"],
        #                 ["Created At", f"{created_at.strftime(DT_OBJ_FORMAT)}"],
        #             ],
        #         )
        #     )
        #
        # await Paginator(
        #     bot=ctx.bot,
        #     ctx=ctx,
        #     pages=pages,
        #     useIndexButton=True,
        #     useSelect=False,
        #     firstStyle=ButtonStyle.gray,
        #     nextStyle=ButtonStyle.gray,
        #     prevStyle=ButtonStyle.gray,
        #     lastStyle=ButtonStyle.gray,
        #     indexStyle=ButtonStyle.gray,
        #     hidden=True,
        # ).run()

    @cog_ext.cog_slash(
        name="imgrandom",
        description="Show a random image",
        guild_ids=guild_id_list(),
    )
    async def _imgrandom(self, ctx: SlashContext):
        global all_imgs
        all_imgs = retrieve_all_img()
        image = random.choice(all_imgs)

        author = ctx.guild.get_member(user_id=int(image["author"]))
        if author is None:
            author = "Unknown"

        await ctx.send(content=f"{image['img_url']}")

        del image

    @cog_ext.cog_slash(
        name="img", description="Use an image command", guild_ids=guild_id_list()
    )
    async def _img(self, ctx: SlashContext, image_name: str):
        # TODO Attempt to download image files upon creation in a way that Discord plays nicely

        image = retrieve_img(image_name)

        if not is_valid(image):
            raise UserError(f"Unable to locate an image command named [{image_name}].")

        author = ctx.guild.get_member(user_id=int(image["author"]))
        if author is None:
            author = "Unknown"

        await ctx.send(content=f"{image['img_url']}")

    @cog_ext.cog_slash(
        name="slowking",
        description="Turn a user into Slow King",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="user",
                description="User you want to turn into Slow King",
                option_type=6,
                required=True,
            )
        ],
    )
    async def _slowking(self, ctx: SlashContext, user: discord.Member):
        await ctx.defer()

        await ctx.send(file=make_slowking(user))

    @cog_ext.cog_slash(
        name="deepfry",
        description="Deep fry an image",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="url",
                description="The URL of the image you want to deep fry.",
                option_type=3,
                required=False,
            ),
            create_option(
                name="avatar",
                description="The avatar you want to deep fry.",
                option_type=6,
                required=False,
            ),
        ],
    )
    async def _deepfry(
        self, ctx: SlashContext, url: str = None, avatar: discord.Member = None
    ):
        if url == avatar:
            raise UserError("You must provide either a URL or an avatar!")

        if (
            url is not None
            and not validators.url(url)
            and not any(sub_str in url for sub_str in image_formats)
        ):
            raise UserError("You must provide a valid URL!")

        await ctx.defer()

        def load(url):
            image_response = requests.get(url=url, stream=True, headers=HEADERS)
            return Image.open(io.BytesIO(image_response.content)).convert("RGBA")

        emote_amount = random.randrange(1, 6)
        noise = random.uniform(0.4, 0.65)
        contrast = random.randrange(1, 99)
        layers = random.randrange(1, 3)

        image = None

        if url:
            image = load(url)
        elif avatar:
            image = load(avatar.avatar_url)

        if image is None:
            raise CommandError("Unable to load image")

        try:
            fried = fryer.fry(image, emote_amount, noise, contrast)

            for layer in range(layers):
                emote_amount = random.randrange(1, 6)
                noise = random.uniform(0.4, 0.65)
                contrast = random.randrange(1, 99)

                fried = fryer.fry(fried, emote_amount, noise, contrast)

            with io.BytesIO() as image_binary:
                fried.save(image_binary, "PNG")
                if image_binary.tell() > 8000000:
                    image_binary = io.BytesIO()
                    fried.convert("RGB").save(
                        image_binary, "JPEG", quality=90, optimize=True
                    )
                image_binary.seek(0)

                await ctx.send(
                    file=discord.File(fp=image_binary, filename="deepfry.png")
                )
        except Exception:
            raise CommandError("Something went wrong. Blame my creators.")

    @cog_ext.cog_slash(
        name="inspireme",
        description="The bot will send you an inspirational message",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="person",
                description="Person you want to inspire",
                required=False,
                option_type=6,
            )
        ],
    )
    async def _inspireme(self, ctx: SlashContext, person: discord.Member = None):
        image = requests.get("https://inspirobot.me/api?generate=true")

        if person:
            try:
                await ctx.send(
                    f"{ctx.author.mention} wants to inspire {person.mention}\n{image.text}"
                )
            except:
                await ctx.send(f"{ctx.author} wants to inspire {person}")
        else:
            await ctx.send(image.text)

    @cog_ext.cog_slash(
        name="hypeme",
        description="Husk's wise words of wisdom in meme format",
        guild_ids=guild_id_list(),
    )
    async def _hypeme(self, ctx: SlashContext):
        await ctx.defer()
        with open("resources/husk_messages.txt", encoding="UTF-8") as f:
            source_data = f.read()

        text_model = markovify.NewlineText(source_data)

        output = (
            str(text_model.make_short_sentence(min_chars=20, max_chars=50))
            .lower()
            .capitalize()
        )

        if not output == "None":
            await ctx.send(f'_"{output}"_ - Husk')
        else:
            await ctx.send("Unable to generate a Markov chain")


def setup(bot):
    bot.add_cog(ImageCommands(bot))
