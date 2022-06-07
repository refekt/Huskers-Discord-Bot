import logging
import pathlib
import platform
from typing import Optional, Any, Union

import discord.ext.commands
import requests
import validators
from PIL import Image, ImageOps
from discord import app_commands
from discord.ext import commands

from helpers.constants import GUILD_PROD, ROLE_ADMIN_PROD
from helpers.embed import buildEmbed
from helpers.mysql import (
    processMySQL,
    sqlSelectImageCommand,
    sqlSelectAllImageCommand,
    sqlCreateImageCommand,
    sqlDeleteImageCommand,
)
from objects.Exceptions import ImageException

logger = logging.getLogger(__name__)

image_formats = (".jpg", ".jpeg", ".png", ".gif", ".gifv", ".mp4")

__all__ = ["ImageCog"]


def retrieve_all_img():
    try:
        return processMySQL(query=sqlSelectAllImageCommand, fetch="all")
    except:  # noqa
        raise ImageException(f"Unable to retrieve image commands.")


all_imgs = retrieve_all_img()


def retrieve_img(image_name: str) -> Union[None, Any]:
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
        logger.info(f"Image {image_name} sucessfully created!")
        return True
    except:  # noqa
        raise ImageException("Unable to create image command in MySQL database!")


def retrieve_all_img() -> None:
    try:
        return processMySQL(query=sqlSelectAllImageCommand, fetch="all")
    except:  # noqa
        raise ImageException(f"Unable to retrieve image commands.")


class ImageCog(commands.Cog, name="Image Commands"):
    group_img = app_commands.Group(
        name="img",
        description="Get creative with images",
        guild_ids=[GUILD_PROD],
    )

    @commands.command()
    async def deepfry(self, interaction: discord.Interaction) -> None:
        ...

    @app_commands.command(
        name="inspire-me",
        description="Get random inspiration",
    )
    @app_commands.describe(person="Person you want to inspire")
    @app_commands.guilds(GUILD_PROD)
    async def inspireme(
        self, interaction: discord.Interaction, person: Optional[discord.Member] = None
    ) -> None:
        image = requests.get("https://inspirobot.me/api?generate=true")

        if person:
            await interaction.response.send_message(
                f"{interaction.user.mention} wants to inspire {person.mention}\n"
                f"{image.text}"
            )
        else:
            await interaction.response.send_message(image.text)

    @app_commands.command(
        name="slowking",
        description="Crown someone as a Slowking",
    )
    @app_commands.describe(person="Person you want to inspire")
    @app_commands.guilds(GUILD_PROD)
    async def slowking(
        self, interaction: discord.Interaction, person: discord.Member
    ) -> None:
        await interaction.response.defer()

        try:
            avatar_thumbnail = Image.open(
                requests.get(person.avatar.url, stream=True).raw
            ).convert("RGBA")
        except IOError:
            logger.exception("Unable to create a Slow King avatar for user!")
            raise ImageException("Unable to create a Slow King avatar for user!")

        base_mask = Image.open("resources/images/mask.png").convert("L")
        avatar_thumbnail = ImageOps.fit(
            avatar_thumbnail, base_mask.size, centering=(0.5, 0.5)
        )
        avatar_thumbnail.putalpha(base_mask)

        paste_pos = (265, 250)
        slowking_filename = "make_slowking.png"

        base_img = Image.open("resources/images/slowking.png").convert("RGBA")
        base_img.paste(avatar_thumbnail, paste_pos, avatar_thumbnail)

        base_img.save(f"resources/images/{slowking_filename}", "PNG")

        if "Windows" in platform.platform():
            slowking_path = f"{pathlib.Path(__file__).parent.parent.resolve()}\\resources\\images\\{slowking_filename}"
        else:
            slowking_path = f"{pathlib.Path(__file__).parent.parent.resolve()}/resources/images/{slowking_filename}"

        with open(slowking_path, "rb") as f:
            file = discord.File(f)

        await interaction.followup.send(content=person.mention, file=file)

        file.close()

    @group_img.command(name="create", description="Create a server image")
    async def img_create(
        self, interaction: discord.Interaction, image_name: str, image_url: str
    ) -> None:
        logger.info(f"Attempting to create new server image '{image_name}'")
        await interaction.response.defer(ephemeral=True)

        assert not retrieve_img(image_name), ImageException(
            "An image with that name already exists. Try again!"
        )

        image_name = image_name.replace(" ", "_")  # Replace spaces with undescores

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
    async def img_delete(
        self, interaction: discord.Interaction, image_name: str
    ) -> None:
        logger.info(f"Attempting to delete '{image_name}'!")
        await interaction.response.defer(ephemeral=True)

        try:
            img_author = int(retrieve_img(image_name)["author"])
        except TypeError:
            raise ImageException(f"Unable to locate image [{image_name}]")

        assert img_author, ImageException(f"Unable to locate image [{image_name}]")

        admin = interaction.guild.get_role(ROLE_ADMIN_PROD)
        admin_delete = False

        if admin in interaction.user.roles:
            admin_delete = True
        elif not interaction.user.id == img_author:
            raise ImageException(  # TODO Verify img_author works here...
                f"This command was created by [{interaction.guild.get_member(img_author).mention}] and can only be deleted by them"
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

        embed = buildEmbed(
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
    async def img_random(
        self, interaction: discord.Interaction, image_url: str
    ) -> None:
        ...


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ImageCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
