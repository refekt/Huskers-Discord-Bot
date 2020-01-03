from discord.ext import commands

from utils.consts import role_admin_prod, role_admin_test
from utils.consts import ssh_pw, ssh_user, ssh_host
from utils.embed import build_embed

from paramiko import client as p_client

ssh_commands = {
    "status": "ps aux | grep spigot",
    "free": "free"
}


class ssh:
    client = None

    def __init__(self, address, username, password):
        print("^^^ Connecting to server... ^^^")

        self.client = p_client.SSHClient()
        self.client.set_missing_host_key_policy(p_client.AutoAddPolicy())
        self.client.connect(address, username=username, password=password, look_for_keys=False)

    def sendCommand(self, command):
        print(f"^^^ Sending SSH command [{command}] ^^^")

        import select

        alldata = ""

        if self.client:
            stdin, stdout, stderr = self.client.exec_command(command)

            while not stdout.channel.exit_status_ready():
                rl, wl, xl = select.select([stdout.channel], [], [], 0.0)

                if len(rl) > 0:
                    alldata += str(stdout.channel.recv(1024), "utf-8")
                    break

            return f"{alldata if alldata else '*'}"
        else:
            print("^^^ Connection not opened! ^^^")

    def cleanup(self):
        print("^^^ Closing SSH server connection... ^^^")
        self.client.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


def format_data(data: str, filter: str=""):
    split = data.split("\n")
    output = ""

    for s in split:
        if filter:
            if not filter in s:
                continue
        if s:
            output += f"`{s}`\n"

    return output


def connect_SSH():
    return ssh(address=ssh_host, username=ssh_user, password=ssh_pw)


class MinecraftCommands(commands.Cog, name="Minecraft Commands"):
    @commands.group(aliases=["mc",])
    async def minecraft(self, ctx):
        pass

    @commands.has_any_role(role_admin_prod, role_admin_test)
    @minecraft.command()
    async def status(self, ctx):
        edit_msg = await ctx.send("Loading...")
        ssh = connect_SSH()
        check = True
        data = ""
        while check:
            data = ssh.sendCommand(ssh_commands["status"])
            if "minecra" in data:
                check = False

        data = format_data(data, "java")
        await edit_msg.edit(content=data)
        del ssh

    @minecraft.command()
    async def server(self, ctx):
        await ctx.send(
            embed=build_embed(
                title="Husker Discord Minecraft Server",
                fields=[
                    ["Version", "Java"],
                    ["Server", "202.5.24.139"],
                    ["Port", "25565"],
                    ["Dynamic Map", "http://202.5.24.139:8123/"]
                ]
            )
        )


def setup(bot):
    bot.add_cog(MinecraftCommands(bot))


print("### Minecraft Command loaded! ###")
