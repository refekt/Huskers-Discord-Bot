import random

from discord.ext import commands

from utils.consts import CD_GLOBAL_RATE, CD_GLOBAL_PER, CD_GLOBAL_TYPE
from utils.embed import build_image_embed

flag_dict = {
    'alabama': 'https://i.imgur.com/uHXPo4n.png',
    'colorado': 'https://i.imgur.com/If6MPtT.jpg',
    'illinois': 'https://i.imgur.com/MxMaS3e.jpg',
    'indiana': 'https://i.imgur.com/uc0Q8Z0.jpg',
    'iowa': 'https://i.imgur.com/xoeCOwp.png',
    'iowa_state': 'https://i.imgur.com/w9vg0QX.jpg',
    'kansas': 'https://i.imgur.com/BL4jQfx.png',
    'kstate': 'https://i.imgur.com/qtxrPn7.png',
    'maryland': 'https://i.imgur.com/G6RX8Oz.jpg',
    'miami': 'https://i.imgur.com/MInQMLb.jpg',
    'michigan': 'https://i.imgur.com/XWEDsFf.jpg',
    'michigan_state': 'https://i.imgur.com/90a9g3v.jpg',
    'minnesota': 'https://i.imgur.com/54mF0sK.jpg',
    'nebraska': 'https://i.imgur.com/q2em9Qw.jpg',
    'northern_illinois': 'https://i.imgur.com/HpmAoIh.jpg',
    'northwestern': 'https://i.imgur.com/Vzk3wdG.jpg',
    'notredame': 'https://i.imgur.com/Ofoaz7U.png',
    'ohio_state': 'https://i.imgur.com/8QwoYgm.jpg',
    'penn_state': 'https://i.imgur.com/JkQuMXf.jpg',
    'purdue': 'https://i.imgur.com/8SYhZKc.jpg',
    'rutgers': 'https://i.imgur.com/lyng39h.jpg',
    'south_alabama': 'https://i.imgur.com/BOH5reA.jpg',
    'stanford': 'https://giant.gfycat.com/PassionateRepentantCoelacanth.gif',
    'texas': 'https://i.imgur.com/rB2Rduq.jpg',
    'ttu': 'https://i.imgur.com/lpOSpH7.png',
    'tulane': 'https://gfycat.com/braveanotherdodobird',
    'usc': 'https://i.imgur.com/GrA4M0X.png',
    'wisconsin': 'https://giant.gfycat.com/PolishedFeminineBeardedcollie.gif',
    'creighton': 'https://i.imgur.com/OxVze61.png'
}


class CrappyFlags(commands.Cog, name="Flag Commands"):
    @commands.command(aliases=["rf", ])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def randomflag(self, ctx):
        """ Random Nebraskan flags """
        flags = []

        with open("resources/flags.txt") as f:
            for line in f:
                flags.append(line)
        f.close()

        random.shuffle(flags)
        await ctx.send(embed=build_image_embed(title="Random Ass Nebraska Flag", image=random.choice(flags)))

    @commands.group(aliases=["cf", ])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def crappyflag(self, ctx):
        """ Display some crappy flags """
        subcmds = []
        for cmd in CrappyFlags.crappyflag.commands:
            subcmds.append(str(cmd).split(" ")[1])

        if not ctx.subcommand_passed:
            state = random.choice(subcmds)
            await ctx.send(embed=build_image_embed(title=state.title(), image=flag_dict[state]))
        else:
            state = str(ctx.subcommand_passed).lower()
            await ctx.send(embed=build_image_embed(title=state.title(), image=flag_dict[state]))

    @crappyflag.command()
    async def alabama(self, ctx):
        pass

    @crappyflag.command()
    async def colorado(self, ctx):
        pass

    @crappyflag.command()
    async def illinois(self, ctx):
        pass

    @crappyflag.command()
    async def indiana(self, ctx):
        pass

    @crappyflag.command()
    async def iowa(self, ctx):
        pass

    @crappyflag.command()
    async def iowa_state(self, ctx):
        pass

    @crappyflag.command()
    async def kansas(self, ctx):
        pass

    @crappyflag.command()
    async def kstate(self, ctx):
        pass

    @crappyflag.command()
    async def maryland(self, ctx):
        pass

    @crappyflag.command()
    async def miami(self, ctx):
        pass

    @crappyflag.command()
    async def michigan(self, ctx):
        pass

    @crappyflag.command()
    async def michigan_state(self, ctx):
        pass

    @crappyflag.command()
    async def minnesota(self, ctx):
        pass

    @crappyflag.command()
    async def nebraska(self, ctx):
        pass

    @crappyflag.command(aliases=["niu"])
    async def northern_illinois(self, ctx):
        pass

    @crappyflag.command()
    async def northwestern(self, ctx):
        pass

    @crappyflag.command()
    async def notredame(self, ctx):
        pass

    @crappyflag.command(aliases=["osu", "tosu"])
    async def ohio_state(self, ctx):
        pass

    @crappyflag.command(aliases=["penn", "psu"])
    async def penn_state(self, ctx):
        pass

    @crappyflag.command()
    async def purdue(self, ctx):
        pass

    @crappyflag.command()
    async def rutgers(self, ctx):
        pass

    @crappyflag.command()
    async def south_alabama(self, ctx):
        pass

    @crappyflag.command()
    async def stanford(self, ctx):
        pass

    @crappyflag.command()
    async def texas(self, ctx):
        pass

    @crappyflag.command(aliases=["ttu"])
    async def texas_tech(self, ctx):
        pass

    @crappyflag.command()
    async def tulane(self, ctx):
        pass

    @crappyflag.command()
    async def usc(self, ctx):
        pass

    @crappyflag.command()
    async def wisconsin(self, ctx):
        pass

    @crappyflag.command()
    async def creighton(self, ctx):
        pass


def setup(bot):
    bot.add_cog(CrappyFlags(bot))

# print("### CrappyFlags Command loaded! ###")
