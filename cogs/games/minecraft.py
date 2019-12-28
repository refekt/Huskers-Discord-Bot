from discord.ext import commands
from paramiko import client as client

from utils.consts import ssh_pw, ssh_user, ssh_host
from utils.embed import build_embed

ssh_commands = {
    "status": "ps aux | grep spigot"
}


class ssh:
    client = None

    def __init__(self, address, username, password):
        print("^^^ Connecting to server... ^^^")

        self.client = client.SSHClient()
        self.client.set_missing_host_key_policy(client.AutoAddPolicy())
        self.client.connect(address, username=username, password=password, look_for_keys=False)

    def sendCommand(self, command):
        print(f"^^^ Sending command [{command}] ^^^")

        import select

        alldata = "```\n"

        if self.client:
            stdin, stdout, stderr = self.client.exec_command(command)

            while not stdout.channel.exit_status_ready():
                rl, wl, xl = select.select([stdout.channel], [], [], 0.0)

                if len(rl) > 0:
                    alldata += str(stdout.channel.recv(1024), "utf-8")
                    break

            alldata += "\n```"

            return f"All Data: " \
                   f"{alldata if alldata else '*'}"
        else:
            print("^^^ Connection not opened! ^^^")

    def cleanup(self):
        print("^^^ Closing SSH server connection... ^^^")
        self.client.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


def connect_SSH():
    return ssh(address=ssh_host, username=ssh_user, password=ssh_pw)


class MinecraftCommands(commands.Cog, name="Minecraft Commands"):
    @commands.group(aliases=["mc",])
    async def minecraft(self, ctx):
        pass

    @commands.has_any_role(606301197426753536, 440639061191950336)
    @minecraft.command()
    async def status(self, ctx):
        ssh = connect_SSH()
        await ctx.send(ssh.sendCommand(ssh_commands["status"]))
        del ssh

    @minecraft.command()
    async def server(self, ctx):
        await ctx.send(
            embed=build_embed(
                title="Husker Discord Minecraft Server",
                fields=[["Version", "Java"], ["Server", "202.5.24.139"], ["Port", "25565"], ["Dynamic Map", "http://202.5.24.139:8123/"]]
            )
        )


def setup(bot):
    bot.add_cog(MinecraftCommands(bot))


print("### Minecraft Command loaded! ###")
