import io
import pathlib
import platform
import random
from asyncio import Task
from os import listdir
from os.path import isfile, join
from typing import Optional, Any, Union

import discord.ext.commands
import requests
import validators
from PIL import Image
from discord import app_commands
from discord.ext import commands

from helpers.constants import (
    GUILD_PROD,
    HEADERS,
    ROLE_ADMIN_PROD,
)
from helpers.embed import buildEmbed
from helpers.fryer import fry_image
from helpers.mysql import (
    processMySQL,
    sqlCreateImageCommand,
    sqlDeleteImageCommand,
    sqlSelectAllImageCommand,
    sqlSelectImageCommand,
)
from helpers.slowking import makeSlowking
from objects.Exceptions import ImageException
from objects.Logger import discordLogger

logger = discordLogger(__name__)

image_formats = (".jpg", ".jpeg", ".png", ".gif", ".gifv", ".mp4")

__all__: list[str] = ["ImageCog"]


def retrieve_all_img() -> Union[dict, list[dict], None]:
    try:
        return processMySQL(query=sqlSelectAllImageCommand, fetch="all")
    except:  # noqa
        raise ImageException(f"Unable to retrieve image commands.")


all_imgs: Union[dict, list[dict], None] = retrieve_all_img()


def retrieve_img(image_name: str) -> Union[dict, list[dict], None]:
    try:
        return processMySQL(query=sqlSelectImageCommand, values=image_name, fetch="one")
    except:  # noqa
        raise ImageException(f"Unable to locate an image command named [{image_name}].")


def create_img(author: int, image_name: str, image_url: str) -> Union[bool, Any]:
    assert validators.url(image_url), ImageException(
        "Invalid image URL format. The URL must begin with 'http' or 'https'."
    )
    assert any(sub_str in image_url for sub_str in image_formats), ImageException(
        f"Invalid image URL format. The URL must end with a [{', '.join(image_formats)}] extension."
    )

    try:
        processMySQL(
            query=sqlCreateImageCommand, values=[author, image_name, image_url]
        )
        logger.info(f"Image {image_name} successfully created!")
        return True
    except:  # noqa
        raise ImageException("Unable to create image command in MySQL database!")


def retrieve_all_img() -> None:
    try:
        return processMySQL(query=sqlSelectAllImageCommand, fetch="all")
    except:  # noqa
        raise ImageException(f"Unable to retrieve image commands.")


# Depreciated
# def gatherAiImageResults(_prompt: str) -> Response:
#     request_url: str = "https://backend.craiyon.com/generate"
#     headers: dict[str] = {
#         "Accept": "application/json",
#         "Content-Type": "application/json",
#         "Host": "backend.craiyon.com",
#     }
#     json_input: dict[str] = {"prompt": _prompt}
#
#     logger.info("Loading results...")
#     results: Response = requests.post(url=request_url, headers=headers, json=json_input)
#     logger.info("Images loaded!")
#
#     if results.status_code == 200:
#         return results
#     else:
#         raise ImageException(f"API Returned {results.status_code}: {results.reason}")


# def decodeImagesToBytes(_images: dict[str]) -> list[bytes]:
#     logger.info("Decoding images")
#     decoded = []
#     for image in _images["images"]:
#         decoded.append(
#             base64.decodebytes(bytes(image, encoding="utf-8")) + b"=="
#         )  # Added b"==" for padding, but I had `images` instead of `images["images"]` so may not need
#     return decoded


# def convertBytesToImages(_decoded_images: list[bytes]) -> list[Image]:
#     logger.info("Converting decoded images to image object")
#     files: list[Image] = []
#
#     for dec in _decoded_images:
#         files.append(Image.open(io.BytesIO(dec)))
#     return files


# def createCollageImage(_converted_files: list[Image]) -> Image:
#     logger.info("Creating photo collage")
#     columns = 3
#     rows = 3
#     width = height = 256 * 3
#
#     thumbnail_width = width // columns
#     thumbnail_height = height // rows
#
#     size = thumbnail_width, thumbnail_height
#     collage_image = Image.new("RGB", (width, height))
#
#     imgs = []
#     for file in _converted_files:
#         file.thumbnail(size)
#         imgs.append(file)
#
#     i = x = y = 0
#     for col in range(columns):
#         for row in range(rows):
#             collage_image.paste(imgs[i], (x, y))
#             i += 1
#             y += thumbnail_height
#         x += thumbnail_width
#         y = 0
#
#     return collage_image


def getBuffer(_buffer: Image) -> io.BytesIO:
    buffer: io.BytesIO = io.BytesIO()
    _buffer.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


# async def sendAiImage(_prompt: str, _author: discord.Member, _channel: Any) -> None:
#     api_results: Response = gatherAiImageResults(_prompt)
#     api_results_images: dict = api_results.json()
#     decoded_images: list[bytes] = decodeImagesToBytes(api_results_images)
#     converted_files: list[Image] = convertBytesToImages(decoded_images)
#     collage_image: Image = createCollageImage(converted_files)
#     buffer: io.BytesIO = getBuffer(collage_image)
#
#     await _channel.send(
#         content=f"An AI generated image was created by {_author.mention} with the following prompt: {_prompt}",
#         file=discord.File(fp=buffer, filename="ai-image.jpg"),
#     )


class ImageCog(commands.Cog, name="Image Commands"):
    def __init__(self, loop) -> None:
        super(ImageCog, self).__init__()
        self.tasks: list[Task] = []

    group_img: app_commands.Group = app_commands.Group(
        name="img",
        description="Get creative with images",
        guild_ids=[GUILD_PROD],
    )

    @app_commands.command(
        name="deep-fry",
        description="Deep fry a picture into a unique creation",
    )
    @app_commands.describe(
        source_url="URL of an image you want to deepfry",
        source_avatar="Avatar of member you want to deepfry",
    )
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def deepfry(
        self,
        interaction: discord.Interaction,
        source_url: str = None,
        source_avatar: discord.Member = None,
    ) -> None:
        logger.info("Attempting to create a deep fried image!")
        await interaction.response.defer()

        if source_url is not None and source_avatar is not None:
            raise ImageException("You can only provide one source!")

        if source_url is not None:
            assert validators.url(source_url) and any(
                sub_str in source_url for sub_str in image_formats
            ), ImageException("You must provide a valid URL!")

        def load_image_from_url(url: str) -> Image:
            image_response: requests.Response = requests.get(
                url=url, stream=True, headers=HEADERS
            )
            return Image.open(io.BytesIO(image_response.content)).convert("RGBA")

        emote_amount: int = random.randrange(1, 6)
        noise: float = random.uniform(0.4, 0.65)
        contrast: int = random.randrange(1, 99)
        layers: int = random.randrange(1, 3)

        image: Optional[Image] = None

        if source_url:
            logger.info("Loading image from URL")
            image = load_image_from_url(source_url)
        elif source_avatar:
            logger.info("Loading image from member avatar")
            image = load_image_from_url(source_avatar.avatar.url)
        else:
            ImageException("Unknown source used!")

        assert image, ImageException("Unable to load image")

        try:
            logger.info("Frying loaded image")
            fried: Image = fry_image(image, emote_amount, noise, contrast)

            logger.info("Adding emotes, noise, and contrast")
            for layer in range(layers):
                emote_amount = random.randrange(1, 6)
                noise = random.uniform(0.4, 0.65)
                contrast = random.randrange(1, 99)

                fried = fry_image(fried, emote_amount, noise, contrast)

            logger.info("Saving file")
            with io.BytesIO() as image_binary:
                fried.save(image_binary, "PNG")
                if image_binary.tell() > 8000000:
                    image_binary: io.BytesIO = io.BytesIO()
                    fried.convert("RGB").save(
                        image_binary, "JPEG", quality=90, optimize=True
                    )
                image_binary.seek(0)

                logger.info("Sending deep fried image")
                await interaction.followup.send(
                    file=discord.File(fp=image_binary, filename="deepfry.png")
                )
            image_binary.close()
        except Exception:
            raise ImageException("Something went wrong. Blame my creators.")

    @app_commands.command(
        name="inspire-me",
        description="Get random inspiration",
    )
    @app_commands.describe(person="Person you want to inspire")
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def inspireme(
        self, interaction: discord.Interaction, person: Optional[discord.Member] = None
    ) -> None:
        image: requests.Response = requests.get(
            "https://inspirobot.me/api?generate=true"
        )

        if person:
            await interaction.response.send_message(
                f"{interaction.user.mention} wants to inspire {person.mention}\n"
                f"{image.text}"
            )
        else:
            await interaction.response.send_message(image.text)

    @app_commands.command(
        name="slow-king",
        description="Crown someone as a Slowking",
    )
    @app_commands.describe(person="Person you want to inspire")
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def slowking(
        self, interaction: discord.Interaction, person: discord.Member
    ) -> None:
        await interaction.response.defer()
        await interaction.followup.send(
            content=person.mention, file=makeSlowking(person)
        )

    @group_img.command(name="show", description="Show a server image")
    @app_commands.describe(image_name="A keyword for the new image")
    async def img_show(self, interaction: discord.Interaction, image_name: str) -> None:
        await interaction.response.defer()

        image = retrieve_img(image_name)

        assert image, ImageException(
            f"Unable to locate an image command named [{image_name}]."
        )

        author = interaction.guild.get_member(int(image["author"]))
        if author is None:
            author = "Unknown"

        await interaction.followup.send(
            content=f"{interaction.user.mention} used [{image_name}]: \n{image['img_url']}"
        )

    @group_img.command(name="create", description="Create a server image")
    @app_commands.describe(
        image_name="A keyword for the new image", image_url="A valid URL for the image"
    )
    async def img_create(
        self, interaction: discord.Interaction, image_name: str, image_url: str
    ) -> None:
        logger.info(f"Attempting to create new server image '{image_name}'")
        await interaction.response.defer(ephemeral=True)

        assert not retrieve_img(image_name), ImageException(
            "An image with that name already exists. Try again!"
        )

        image_name = image_name.replace(" ", "_")  # Replace spaces with underscores

        if not create_img(interaction.user.id, image_name, image_url):
            raise ImageException("Unable to create the image in the MySQL database!")

        embed = buildEmbed(
            title="Create an Image Command",
            image=image_url,
            fields=[
                dict(
                    name="Image Created!",
                    value=f"Congratulations, [{interaction.user.mention}] created the [{image_name}] command!",
                )
            ],
        )
        await interaction.followup.send(embed=embed)

    @group_img.command(name="list", description="List all the server images")
    async def img_list(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        global all_imgs
        all_imgs = retrieve_all_img()
        img_list = [img["img_name"] for img in all_imgs]
        img_list.sort()

        await interaction.followup.send(
            f"There are {len(img_list)} images listed below:\n{', '.join(img_list)}"
        )

    @group_img.command(name="delete", description="Delete a server image")
    @app_commands.describe(image_name="A keyword for the new image")
    async def img_delete(
        self, interaction: discord.Interaction, image_name: str
    ) -> None:
        logger.info(f"Attempting to delete '{image_name}'!")
        await interaction.response.defer(ephemeral=True)

        try:
            img_author: int = int(retrieve_img(image_name)["author"])
        except TypeError:
            raise ImageException(f"Unable to locate image [{image_name}]")

        assert img_author, ImageException(f"Unable to locate image [{image_name}]")

        admin: discord.Role = interaction.guild.get_role(ROLE_ADMIN_PROD)
        admin_delete: bool = False

        if admin in interaction.user.roles:
            admin_delete = True
        elif not interaction.user.id == img_author:
            raise ImageException(  # TODO Verify img_author works here...
                f"This command was created by [{interaction.guild.get_member(int(img_author)).mention}] and can only be deleted by them"
            )

        try:
            if admin_delete:
                processMySQL(
                    query=sqlDeleteImageCommand, values=[image_name, str(img_author)]
                )
            else:
                processMySQL(
                    query=sqlDeleteImageCommand,
                    values=[image_name, str(interaction.user.id)],
                )
        except:  # noqa
            raise ImageException("Unable to delete this image command!")

        embed: discord.Embed = buildEmbed(
            title="Delete Image Command",
            fields=[
                dict(
                    name="Deleted",
                    value=f"You have deleted the image command [{image_name}].",
                )
            ],
        )
        await interaction.followup.send(embed=embed)

    @group_img.command(name="random", description="Send a random a server image")
    async def img_random(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        global all_imgs
        all_imgs = retrieve_all_img()
        image: dict = random.choice(all_imgs)

        author: Optional[str] = interaction.guild.get_member(int(image["author"]))
        if author is None:
            author = "Unknown"

        await interaction.followup.send(content=f"{image['img_url']}")

        del image

    @app_commands.command(name="twos", description="Random Tunnel Walk of Shame image")
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def tunnel_walk(self, interaction: discord.Interaction) -> None:
        logger.info("Grabbing a random TWOS image")
        await interaction.response.defer()

        if "Windows" in platform.platform():
            twos_path: str = f"{pathlib.Path(__file__).parent.parent.resolve()}\\resources\\images\\TWOS\\"
        else:
            twos_path = f"{pathlib.Path(__file__).parent.parent.resolve()}/resources/images/TWOS/"

        twos_files: list[str] = [
            file for file in listdir(twos_path) if isfile(join(twos_path, file))
        ]

        random.shuffle(twos_files)

        with open(f"{twos_path}{random.choice(twos_files)}", "rb") as f:
            file = discord.File(f)  # noqa

        await interaction.followup.send(file=file)

    @app_commands.command(
        name="ai-image",
        description="Use craiyon services to generate an AI generated image.",
    )
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def ai_image(self, interaction: discord.Interaction, prompt: str) -> None:
        await interaction.response.send_message(
            "This was a fun command to make, but it's really taxing on the bot and I need to turn it off.",
            ephemeral=True,
        )
        # await interaction.response.send_message(
        #     "This may take up to 3 minutes to process. Your message will be sent when ready.",
        #     ephemeral=True,
        # )
        # alert = asyncio.Event()
        # alert.last_event = None
        # self.tasks.append(
        #     asyncio.create_task(
        #         sendAiImage(
        #             _prompt=prompt,
        #             _author=interaction.user,
        #             _channel=interaction.channel,
        #         )
        #     )
        # )
        # await asyncio.gather(*self.tasks)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ImageCog(bot), guilds=[discord.Object(id=GUILD_PROD)])


logger.info(f"{str(__name__).title()} module loaded!")
