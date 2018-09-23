from discord.ext import commands
import discord
import asyncio
import json
from helper_files.embed import embed as em
import helper_files.settings as settings

import logging
logger = logging.getLogger('wall_e')

class Mod():

    def isMinion(self, ctx):
        role = discord.utils.get(ctx.guild.roles, name='Minions')
        membersOfRole = role.members
        for members in membersOfRole:
            if ctx.author.id == members.id:
                return True
        return False

    async def rekt(self, ctx):
        logger.info('[Mod rekt()] sending troll to unauthorized user')
        lol = '[secret](https://www.youtube.com/watch?v=dQw4w9WgXcQ)'
        eObj = em(title='Minion Things', author=settings.BOT_NAME, avatar=settings.BOT_AVATAR, description=lol)        
        msg = await ctx.send(embed=eObj)
        await asyncio.sleep(5)
        await msg.delete()
        logger.info('[Mod rekt()] troll message deleted')
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(aliases=['em'])
    async def embed(self, ctx, *arg):
        logger.info('[Mod embed()] embed function detected by user ' + str(ctx.message.author))
        if not arg:
            logger.error("[Mod embed()] no args, so command ended")
            return
        await ctx.message.delete()
        logger.info('[Mod embed()] invoking message deleted')
        
        if not self.isMinion(ctx):
            logger.error('[Mod embed()] unathorized command attempt detected. Being handled.')
            await self.rekt(ctx)
            return
        
        logger.info('[Mod embed()] minion confirmed')
        fields = []
        desc = ''
        arg = list(arg)
        argLen = len(arg)
        # odd number of args means description plus fields
        if not argLen%2 == 0:
            desc = arg[0]
            arg.pop(0)
            argLen = len(arg)
            
        i = 0
        while i < argLen:
            fields.append([arg[i], arg[i+1]])
            i +=2

        name = ctx.author.nick or ctx.author.name
        eObj = em(description=desc, author=name, avatar=ctx.author.avatar_url, colour=0xffc61d ,content=fields)
        await ctx.send(embed=eObj)

    @commands.command(aliases=['warn'])
    async def modspeak(self, ctx, *arg):
        logger.info('[Mod modspeak()] modspeack function detected by minion ' + str(ctx.message.author))
        
        if not arg:
            logger.error("[Mod modspeak()] no args, so command ended")
            return
        await ctx.message.delete()
        logger.info('[Mod embed()] invoking message deleted')

        if not self.isMinion(ctx):
            logger.error('[Mod modspeak()] unathorized command attempt detected. Being handled.')
            await self.rekt(ctx)
            return

        msg = ''
        for wrd in arg:
            msg += wrd + ' '

        eObj = em(title='A Bellow From the Underworld says...', colour=0xff0000, author=ctx.author.display_name, avatar=ctx.author.avatar_url, description=msg, footer='Moderator Warning')
        await ctx.send(embed=eObj)

def setup(bot):
    bot.add_cog(Mod(bot))
