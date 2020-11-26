from discord.ext import commands

from utils.embed import build_embed

version = "1.16.4"


class MinecraftCommands(commands.Cog, name="Minecraft Commands"):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["mc", ])
    async def minecraft(self, ctx):
        """ View Husker Minecraft server information"""
        pass

    @minecraft.command()
    async def server(self, ctx):
        await ctx.send(
            embed=build_embed(
                title=f"HuskerCraft {version} Server",
                description="Java",
                fields=[
                    ["Survival Server", "202.5.24.139"],
                    ["Port", "25565"],
                ]
            )
        )

    @minecraft.command()
    async def map(self, ctx):
        # https://i.redd.it/kv7ylaz92ka51.jpg
        await ctx.send(
            embed=build_embed(
                title=f"HuskerCraft {version} Map",
                description="https://i.redd.it/kv7ylaz92ka51.jpg",
                image="https://i.redd.it/kv7ylaz92ka51.jpg"
            )
        )

    @minecraft.command()
    async def rules(self, ctx):
        await ctx.send(
            embed=build_embed(
                title=f"HuskerCraft {version} Rules",
                fields=[
                    ["Rule #1", "Drehmal v2: PRIMΩRDIAL is best played on small-scale multiplayer servers. Multiple goals across the map are designed with community in mind, such as unlocking all fast travel points, progressing the main story, and discovering all the weapons. However, the map is still perfectly playable in singleplayer. Some tasks may just be more tedious/difficult."],
                    ["Rule #2", "This map's terrain was created using the software WorldPainter, and due to its nature, animal spawns are rare. Most every animal you see across the map has been hand placed. If you stay in a chunk for long enough, animals will start to spawn very rarely. Be aware that they are a relatively finite resource, so animal breeding is encouraged."],
                    ["Rule #3", "Accessing The End is not like vanilla Minecraft. Eyes of Ender will lead you nowhere, as there are no natural strongholds on the map. The End can be accessed by progressing through the Main Story."],
                    ["Rule #4", "If you find a Cartographer villager, DO NOT LEVEL IT UP. As there are no naturally spawning Ocean Monuments on the map, cartographers are broken. When you level up a cartographer, it is guaranteed to get the trade for an ocean monument map. As there are no ocean monuments anywhere, the game will encounter an error and crash. Your world/server will be fine, "
                                "just rolled back to a few minutes before the villager leveled up."],
                    ["Rule #5", "When someone discovers a unique weapon, the crafting recipe for that weapon is unlocked for everyone else. Weapon crafting recipes can be viewed via the Recipe Book, and unlocks tracked under the 'WEAPONS OF LEGEND' advancement tab."],
                    ["Rule #6", "Do not set the map to peaceful mode for any reason. Drehmal features a number of hand-placed enemies, and if they're in loaded chunks and the world is set to peaceful, they'll be gone forever. This can lead to one Mythic-tier weapon being unobtainable without using a command to force the advancement."],
                    ["Rule #7", "Never do /kill @e unless you know what you're doing. Killing all entities will kill armor stands in forceloaded chunks, which are necessary to keep many features of the map working properly."],
                ]
            )
        )

    @minecraft.command()
    async def optifine(self, ctx):
        await ctx.send(
            embed=build_embed(
                title=f"HuskerCraft {version} Optifine",
                fields=[
                    ["Info", "Optifine is required to run all features on the server. Get the latest version here: https://optifine.net/downloads."]
                ]
            )
        )


def setup(bot):
    bot.add_cog(MinecraftCommands(bot))
