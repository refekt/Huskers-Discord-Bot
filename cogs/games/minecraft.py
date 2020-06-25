from discord.ext import commands

from utils.embed import build_embed


class MinecraftCommands(commands.Cog, name="Minecraft Commands"):
    @commands.group(aliases=["mc", ])
    async def minecraft(self, ctx):
        """ View Husker Minecraft server information"""
        pass

    @minecraft.command()
    async def server(self, ctx):
        version = "1.16.1"
        await ctx.send(
            embed=build_embed(
                title=f"Husker Discord Minecraft {version} Server",
                fields=[
                    ["Version", "Java"],
                    ["Survival Server", "202.5.24.139"],
                    ["Port", "25565"],
                    ["Creative Server", "202.5.24.139"],
                    ["Port", "25566"],
                ]
            )
        )


def setup(bot):
    bot.add_cog(MinecraftCommands(bot))
