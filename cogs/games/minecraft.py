from discord.ext import commands
from paramiko import client as client

from utils.consts import ssh_pw, ssh_user, ssh_host


class ssh:
    client = None

    def __init__(self, address, username, password):
        print("^^^ Connecting to server... ^^^")
        self.client = client.SSHClient()
        self.client.set_missing_host_key_policy(client.AutoAddPolicy())
        self.client.connect(address, username=username, password=password, look_for_keys=False)

    def sendCommand(self, command):
        alldata = None

        if (self.client):
            stdin, stdout, stderr = self.client.exec_command(command)
            while not stdout.channel.exit_status_ready():
                # Print data when available
                if stdout.channel.recv_ready():
                    alldata = stdout.channel.recv(1024)
                    prevdata = b"1"
                    while prevdata:
                        prevdata = stdout.channel.recv(1024)
                        alldata += prevdata
                try:
                    print(str(alldata, "utf-8"))
                except:
                    pass

            return f"All Data: " \
                   f"```\n" \
                   f"{str(alldata, 'utf8') if alldata else '*'}" \
                   f"\n```" \
                   f"\n" \
                   f"STD Out: ```\n{' '.join([str(elem, 'utf-8') for elem in stdout.readlines()]) if stdout.readlines() else '*'}```\n"
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
    @commands.has_any_role(606301197426753536, 440639061191950336)
    @commands.command()
    async def status(self, ctx):
        msg = await ctx.send("Checking status...")
        connection = connect_SSH()
        output = str(connection.sendCommand("sudo systemctl status minecraft@linuxconfig"))[0:1999]
        print(len(output))
        await msg.edit(content=output)

    @commands.has_any_role(606301197426753536, 440639061191950336)
    @commands.command()
    async def start(self, ctx):
        msg = await ctx.send("Starting server...")
        connection = connect_SSH()
        await msg.edit(content=connection.sendCommand("sudo systemctl start minecraft@linuxconfig"))

    @commands.has_any_role(606301197426753536, 440639061191950336)
    @commands.command()
    async def start(self, ctx):
        msg = await ctx.send("Restarting server...")
        connection = connect_SSH()
        await msg.edit(content=connection.sendCommand("sudo systemctl restart minecraft@linuxconfig"))

    @commands.has_any_role(606301197426753536, 440639061191950336)
    @commands.command()
    async def x(self, ctx, command: str):
        msg = await ctx.send("Sending command...")
        connection = connect_SSH()
        await msg.edit(content=connection.sendCommand(command))


def setup(bot):
    bot.add_cog(MinecraftCommands(bot))


print("### Minecraft Command loaded! ###")
