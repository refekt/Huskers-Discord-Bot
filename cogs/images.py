import random
import textwrap

from PIL import Image, ImageDraw, ImageFont
from discord import File
from discord.ext import commands

from utils.consts import CD_GLOBAL_PER, CD_GLOBAL_RATE, CD_GLOBAL_TYPE
from utils.consts import CHAN_NORTH_BOTTTOMS, CHAN_POSSUMS, CHAN_SCOTTS_BOTS
from utils.consts import ROLE_ASPARAGUS, ROLE_POTATO
from utils.embed import build_image_embed


def build_quote(quote: str, author):
    max_len = 125
    if len(quote) > max_len:
        quote = quote[0:max_len] + "..."

    if author is not None:
        quote = '"' + quote.capitalize() + '"' + f" - {author.display_name.capitalize()}"

    scroll_path = "resources/scroll.png"
    scroll = Image.open(fp=scroll_path)

    img_size = (640, 533)
    img = Image.new(mode="RGBA", size=img_size, color=(255, 0, 0, 0))

    img.paste(im=scroll, box=(0, 0, scroll.width, scroll.height))

    d = ImageDraw.Draw(im=img, mode="RGBA")

    quote_coords = [75, 65]  # [536, 449]
    quote_width = 27

    # font_path = "resources/Canterbury.ttf"
    # font_path = "resources/Olde English Regular.ttf"
    # font_path = "resources/Demo_ConeriaScript.ttf"
    # font_path = "resources/AngillaTattoo.ttf"
    # font_path = "resources/always forever.ttf"
    # font_path = "resources/Silent Reaction.ttf"
    # font_path = "resources/CoalhandLuke.ttf"
    font_path = "resources/Chocolate Covered Raindrops BOLD.ttf"
    font_size = 65
    font = ImageFont.truetype(font=font_path, size=font_size)

    lines = textwrap.wrap(quote, width=quote_width)
    for line in lines:
        d.multiline_text(
            xy=quote_coords,
            font=font,
            text=line,
            fill=(0, 0, 0)
        )
        quote_coords[1] += font.getsize(line)[1]

    image_path = "resources/quote.png"
    img.save(fp=image_path)
    discord_file = File(fp=image_path)

    return discord_file


class ImageCommands(commands.Cog, name="Fun Image Commands"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def quote(self, ctx, *, quote: str, author=None):
        """ Build a quote scroll! You can either reaction to a message with the pencil (📝) reaction or include a quote you want.
        # $quote This is a test quote."""

        await ctx.send(file=build_quote(quote, ctx.author))

        # if ctx.message.channel.id in [CHAN_SCOTTS_BOTS, CHAN_NORTH_BOTTTOMS, CHAN_POSSUMS]:
        #     await ctx.send(file=build_quote(quote, author))
        # else:
        #     raise AttributeError(f"You are not allowed to use this command in this channel!")

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def possum(self, ctx):
        """ Possums are love; possums are life """
        possum_list = (
            "https://cdn.discordapp.com/attachments/442047437561921548/631876712841347117/e3l21wsflor31.jpg",
            "https://i.imgur.com/UI3l2Xu.jpg",
            "https://cdn.discordapp.com/attachments/442047437561921548/631580916342325258/image0.gif",
            "https://thumbs.gfycat.com/WideEcstaticImperialeagle-size_restricted.gif",
            "https://thumbs.gfycat.com/AlienatedNaturalChuckwalla-size_restricted.gif"
        )
        await ctx.send(embed=build_image_embed(title="Possum Paradise 🌴✈", image=random.choice(possum_list)))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def crabfrost(self, ctx):
        """ 🦀 🦀 🦀 """
        await ctx.send(embed=build_image_embed(title="🦀D🦀A🦀N🦀C🦀E🦀P🦀A🦀R🦀T🦀Y🦀", image="https://thumbs.gfycat.com/FalseTestyDotterel-size_restricted.gif"))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def ohyeah(self, ctx):
        """ It's all coming together """
        await ctx.send(embed=build_image_embed(title="If we have Frost, we have national championships.", image="https://i.imgur.com/tdN5IEG.png"))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def danceparty(self, ctx):
        """ 💃🕺👯‍️👯‍️"""
        dances = ("https://thumbs.gfycat.com/FriendlyUnrulyCottonmouth-size_restricted.gif", "https://thumbs.gfycat.com/GiddyOldfashionedBluebreastedkookaburra-size_restricted.gif")
        await ctx.send(embed=build_image_embed(title="🕺💃👯‍♂️👯‍♀️", image=random.choice(dances)))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def yeet(self, ctx):
        """ Yeeeeeeeeet """
        await ctx.send(embed=build_image_embed(title="BIG BOY PARTY", image="https://i.imgur.com/3sshtBD.gif"))

    @commands.command(aliases=["td", ])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def touchdown(self, ctx):
        await ctx.send(embed=build_image_embed(title="🏈🎈🏈🎈", image="https://i.imgur.com/Wh4aLYo.gif"))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def fuckiowa(self, ctx):
        """ FUCK IOWA """
        await ctx.send(embed=build_image_embed(title="FUCK IOWA", image="https://thumbs.gfycat.com/CanineEssentialGelding-size_restricted.gif"))

    @commands.command(aliases=["fuckminn"])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def fuckminnesota(self, ctx):
        """ FUCK MINNESOTA """
        await ctx.send(embed=build_image_embed(title="SINK THE BOAT", image="https://thumbs.gfycat.com/SadClearcutGalapagosalbatross-size_restricted.gif"))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def iowasux(self, ctx):
        """ IOWA SUX """
        await ctx.send(embed=build_image_embed(title="IOWA SUX", image="https://i.imgur.com/j7JDuGe.gif"))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    @commands.has_role(ROLE_POTATO)
    async def potatoes(self, ctx):
        """ Po-tay-toes! """
        await ctx.send(embed=build_image_embed(title="Po-Tay-Toes", image="https://media1.tenor.com/images/9e7881b55627ba4a2b2cbce5649372a3/tenor.gif?itemid=11409033"))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    @commands.has_role(ROLE_ASPARAGUS)
    async def asparagus(self, ctx):
        """ Uh-spare-uh-gus """
        await ctx.send(embed=build_image_embed(title="Asparagang", image="https://i.imgur.com/QskqFO0.gif"))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def flex(self, ctx):
        """ Strong man """
        await ctx.send(embed=build_image_embed(title="FLEXXX", image="https://i.imgur.com/92b9uFU.gif"))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def shrug(self, ctx):
        """ ;) """
        await ctx.send(embed=build_image_embed(title="🤷‍♀", image="https://i.imgur.com/Yt63gGE.gif"))

    @commands.command(aliases=["oof"])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def ohno(self, ctx):
        """ Oof fr, fr """
        await ctx.send(embed=build_image_embed(title="Big OOOOOOF", image=random.choice(["https://i.imgur.com/f4P6jBO.png", "https://i.imgur.com/g63wKDl.png"])))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def bigsexy(self, ctx):
        """ BIG SEXY """
        await ctx.send(embed=build_image_embed(title="OOOHHH YEEAAAHHH", image="https://i.imgur.com/UpKIx5I.png"))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def whoami(self, ctx):
        """ The Kool Aid man! """
        await ctx.send(embed=build_image_embed(title="Who the F I am?", image="https://i.imgur.com/jgvr8pd.gif"))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def thehit(self, ctx):
        """ This hit was legal! """
        await ctx.send(embed=build_image_embed(title="CLEAN HIT (AT THE TIME)!", image="https://i.imgur.com/mKRUPoD.gif"))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def uwot(self, ctx):
        """ Excuse me, what! """
        await ctx.send(embed=build_image_embed(title="What did you just say?!", image="https://i.imgur.com/XpFWJp9.gif"))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def strut(self, ctx):
        """ Ooohhh yeah """
        await ctx.send(embed=build_image_embed(title="Dat Strut", image="https://media.giphy.com/media/iFrlakPVXLIj8bAqCc/giphy.gif"))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def bones(self, ctx):
        """ ☠☠☠☠ """
        await ctx.send(embed=build_image_embed(title="☠ Bones ☠", image="https://i.imgur.com/0gcawNo.jpg"))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def theflip(self, ctx):
        """ Just goofin' 🤠 """
        await ctx.send(embed=build_image_embed(title="Too Cool", image="https://media.giphy.com/media/lllup6g803SaeRUwiM/giphy.gif"))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def guzzle(self, ctx):
        """ 🍻🍻🍻🍻🍻🍻🍻 """
        await ctx.send(embed=build_image_embed(title="Give it to me bb", image="https://i.imgur.com/OW7rChr.gif"))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def nicoleistall(self, ctx):
        """ I AM A TALL BOY """
        await ctx.send(embed=build_image_embed(title="Big Boye", image="https://media1.tenor.com/images/99972fba7f9f38377b56d5d56e4b6052/tenor.gif"))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def maxhype(self, ctx):
        """ I AM A TALL BOY """
        await ctx.send(embed=build_image_embed(title="HYPE", image="https://giant.gfycat.com/ImpishSevereAfricanfisheagle.gif"))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def siryacht(self, ctx):
        """ SirYacht was never wrong! """
        await ctx.send(embed=build_image_embed(title="I am the captain now", image="https://i.imgur.com/0CoT3Jg.gif"))

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def deeretroll(self, ctx):
        """ His pessimism knows no bounds """
        await ctx.send(embed=build_image_embed(title="Whomp, whomp", image="https://i.imgur.com/4Gwlpap.jpg"))


def setup(bot):
    bot.add_cog(ImageCommands(bot))

# print("### Image Commands loaded! ###")
