import random
import time
from datetime import datetime

import praw
from discord.ext import commands

from utils.client import client
from utils.consts import REDDIT_CLIENT_ID, REDDIT_SECRET, REDDIT_PW

recruits = {
    "aho": ["Junior Aho", "3*", "SDE", "https://247sports.com/player/junior-aho-46084569", "Junior Aho is officially N! 🖊", "2020 JUCO 3* SDE Junior Aho signs with Nebraska"],
    "betts": ["Zavier Betts", "4*", "WR", "https://247sports.com/player/zavier-betts-46049733", "Zavier Betts is officially N! 🖊", "2020 4* WR Zavier Betts signs with Nebraska"],
    "black": ["Marquis Black", "3*", "DT", "https://247sports.com/player/marquis-black-46055957", "Marquis Black is officially N! 🖊", "2020 3* DT Marquis Black signs with Nebraska"],
    "brown": ["Alante Brown", "4*", "WR","https://247sports.com/player/alante-brown-46041257/","Alante Brown is N!", "2020 4* WR Alante Brown commits to/signs with Nebraska"],
    "butler": ["Jimari Butler", "3*", "WDE", "https://247sports.com/player/jimari-butler-46093813", "Jimari Butler is officially N! 🖊", "2020 3* WDE Jimari Butler signs with Nebraska"],
    "bollers": ["TJ Bollers", "4*", "WDE","https://247sports.com/Player/TJ-Bollers-46051469/","TJ Bollers is N!", "2020 4* WDE TJ Bollers commits to/signs with Nebraska"],
    "coates": ["Julius Coates", "3*", "SDE", "https://247sports.com/Player/Julius-Coates-46094042/", "Julius Coates is N!", "2020 JUCO 3* SDE Julius Coates commits to/signs with Nebraska"],
    "conn": ["Alex Conn", "3*", "OT", "https://247sports.com/player/alex-conn-46081240", "Alex Conn is officially N! 🖊", "2020 3* OT Alex Conn signs with Nebraska"],
    "cooper": ["Niko Cooper", "3*", "WDE", "https://247sports.com/player/niko-cooper-46094140", "Niko Cooper is officially N! 🖊", "2020 JUCO 3* WDE Niko Cooper signs with Nebraska"],
    "corcoran": ["Turner Corcoran", "4*", "OT", "https://247sports.com/player/turner-corcoran-46054132", "Turner Corcoran is officially N! 🖊",
                 "2020 4* OT Turner Corcoran signs with Nebraska"],
    "delancy": ["Ronald Delancy III", "3*", "CB", "https://247sports.com/player/ronald-delancy-iii-46079963", "Ronald Delancy III is officially N! 🖊",
                "2020 3* CB Ronald Delancy III signs with Nebraska"],
    "densmore": ["Rishard Densmore", "3*", "ATH","https://247sports.com/Player/Rishard-Densmore-46080675/","Rishard Densmore is N!", "2020 3* ATH Rishard Densmore commits to/signs with Nebraska"],
    "durham": ["Chandler Durham", "3*", "OT","https://247sports.com/Player/Chandler-Durham-46081390/","Chandler Durham is N!", "2020 3* OT Chandler Durham commits to/signs with Nebraska"],
    "dennis": ["Kendall Dennis", "4*", "CB", "https://247sports.com/Player/Kendall-Dennis-46081780/", "Kendall Dennis is officially N! 🖊", "2020 4* CB Kendall Dennis commits to/signs with Nebraska"],
    "francois": ["Jaiden Francois", "4*", "S", "https://247sports.com/Player/Jaiden-Francois-46037035/", "Jaiden Francois is officially N! 🖊",
                 "2020 4* S Jaiden Francois commits to/signs with Nebraska"],
    "gifford": ["Isaac Gifford", "3*", "S", "https://247sports.com/player/isaac-gifford-46051030", "Isaac Gifford is officially N! 🖊", "2020 3* S Isaac Gifford signs with Nebraska"],
    "gray": ["Henry Gray", "4*", "S", "https://247sports.com/player/henry-gray-46051388", "Henry Gray is officially N! 🖊", "2020 4* S Henry Gray signs with Nebraska"],
    "green": ["Darion Green-Warren", "4*", "CB","https://247sports.com/player/darion-green-warren-46038102/","Darion Green-Warren is N!", "2020 4* CD Darion Green-Warren signs with "],
    "greene": ["Keyshawn Greene", "4*", "OLB", "https://247sports.com/player/keyshawn-greene-46050924", "Keyshawn Greene is officially N! 🖊",
               "2020 4* OLB Keyshawn Greene commits to/signs with Nebraska"],
    "gunnerson": ["Blaise Gunnerson", "3*", "SDE", "https://247sports.com/player/blaise-gunnerson-46056665", "Blaise Gunnerson is officially N! 🖊",
                  "2020 3* SDE Blaise Gunnerson signs with Nebraska"],
    "hutmacher": ["Nash Hutmacher", "3*", "DT", "https://247sports.com/player/nash-hutmacher-46056120", "Nash Hutmacher is officially N! 🖊",
                  "2020 3* DT Nash Hutmacher signs with Nebraska"],
    "johnson": ["Kaden Johnson", "4*", "OLB", "https://247sports.com/player/kaden-johnson-46050569", "Kaden Johnson is officially N! 🖊", "2020 4* OLB Kaden Johnson commits to/signs with Nebraska"],
    "lynum": ["Tamon Lynum", "3*", "CB", "https://247sports.com/player/tamon-lynum-46082028", "Tamon Lynum is officially N! 🖊", "2020 3* CB Tamon Lynum signs with Nebraska"],
    "manning": ["Omar Manning", "4*", "WR", "https://247sports.com/player/omar-manning-82004", "Omar Manning is officially N! 🖊", "2020 JUCO 4* WR Omar Manning signs with Nebraska"],
    "mauga": ["Eteva Mauga-Clements", "3*", "OLB", "https://247sports.com/player/eteva-mauga-clements-46097169", "Eteva Mauga-Clements is officially N! 🖊",
              "2020 JUCO 3* OLB Eteva Mauga-Clements signs with Nebraska"],
    "morrison": ["Sevion Morrison", "4*", "RB", "https://247sports.com/player/sevion-morrison-46059276", "Sevion Morrison is officially N! 🖊",
                 "2020 4* RB Sevion Morrison signs with Nebraska"],
    "nixon": ["William Nixon", "3*", "WR", "https://247sports.com/player/william-nixon-46055579", "William Nixon is officially N! 🖊", "2020 3* WR William Nixon signs with Nebraska"],
    "payne": ["Pheldarius Payne", "3*", "SDE", "https://247sports.com/Player/Pheldarius-Payne-46079782/", "Pheldarius Payne is N!", "2020 JUCO 3* SDE Pheldarius Payne commits to/signs with Nebraska"],
    "riley": ["Jordon Riley", "3*", "SDE", "https://247sports.com/player/jordon-riley-75571", "Jordon Riley is officially N! 🖊", "2020 JUCO 3* SDE Jordon Riley signs with Nebraska"],
    "scott": ["Marvin Scott III", "3*", "RB", "https://247sports.com/player/marvin-scott-iii-46059013", "Marvin Scott III is officially N! 🖊",
              "2020 3* RB Marvin Scott III signs with Nebraska"],
    "slusher": ["Myles Slusher", "4*", "S", "https://247sports.com/Player/Myles-Slusher-46048503/", "Myles Slusher is officially N! 🖊", "2020 4* S Myles Slusher flips from Oregon to Nebraska"],
    "smothers": ["Logan Smothers", "4*", "DUAL", "https://247sports.com/player/logan-smothers-46051967", "Logan Smothers is officially N! 🖊",
                 "2020 4* DUAL Logan Smothers signs with Nebraska"],
    "togiai": ["Tanoa Togiai", "3*", "SDE","https://247sports.com/player/tanoa-togiai-46047148/","Tanoa Togiai is N!", "2020 3* SDE Tanoa Togiai signs with Nebraska"],
}

eNSD = datetime(year=2019, day=18, month=12)


def is_me(ctx):
    return ctx.message.author.id == 189554873778307073


class RedditCommands(commands.Cog):
    @commands.command(hidden=True)
    @commands.check(is_me)
    async def nsd(self, ctx, recruit: str, source: str):
        right_now = datetime.now()
        if not right_now.date() == eNSD.date():
            print("It is not early signing day!")
            return

        me = client.get_user(189554873778307073)

        try:
            recruit = recruit.lower()
            if not recruit in recruits:
                await me.send(f"Unable to find {recruit}")
                return
        except IndexError:
            await me.send(f"Key error on {recruit}")
            return
        except:
            await me.send(f"No idea...{recruit}")
            return

        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_SECRET,
            user_agent="Scotty McFrosty",
            username="refekt",
            password=REDDIT_PW
        )

        # 0 == name, 1 == stars, 2 == position, 3 == url, 4 == /r/huskers, 5 == /r/cfb
        text = f"247Sports Profile: {recruits[recruit][3]}\n" \
               f"\n" \
               f"Source: {source}"

        huskers = reddit.subreddit("huskers")
        huskers.submit(
            title=recruits[recruit][4],
            selftext=text
        )

        time.sleep(random.randint(3, 6))

        cfb = reddit.subreddit("cfb")
        cfb.submit(
            title=recruits[recruit][5],
            selftext=text
        )


def setup(bot):
    bot.add_cog(RedditCommands(bot))