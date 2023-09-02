import asyncio
import os
import subprocess

import discord
from discord import app_commands
from discord.ext import commands
from wall_e_models.models import CommandStat

from utilities.bot_channel_manager import BotChannelManager
from utilities.embed import embed
from utilities.file_uploading import start_file_uploading
from utilities.send import send as helper_send
from utilities.setup_logger import Loggers
from utilities.slash_command_checks import slash_command_checks


class Administration(commands.Cog):

    def __init__(self, bot, config, bot_channel_manager):
        log_info = Loggers.get_logger(logger_name="Administration")
        self.logger = log_info[0]
        self.debug_log_file_absolute_path = log_info[1]
        self.error_log_file_absolute_path = log_info[2]
        self.config = config
        self.help_dict = self.config.get_help_json()
        self.bot = bot
        self.bot_channel_manager = bot_channel_manager
        self.guild = None
        self.announcement_channel = None
        if self.config.enabled("database_config", option="ENABLED"):
            import matplotlib
            matplotlib.use("agg")
            import matplotlib.pyplot as plt  # noqa
            self.plt = plt
            import numpy as np  # noqa
            self.np = np
            self.image_parent_directory = ''
            if self.config.get_config_value('basic_config', 'ENVIRONMENT') == "LOCALHOST":
                image_parent_directory = self.config.get_config_value(
                    "basic_config", option="FOLDER_FOR_FREQUENCY_IMAGES"
                )
                if os.path.isdir(image_parent_directory):
                    self.image_parent_directory = image_parent_directory

    @commands.Cog.listener(name="on_ready")
    async def get_guild(self):
        self.guild = self.bot.guilds[0]

    @commands.Cog.listener(name="on_ready")
    async def get_announcement_channel(self):
        while self.guild is None:
            await asyncio.sleep(2)
        reminder_chan_id = await self.bot_channel_manager.create_or_get_channel_id(
            self.logger, self.guild, self.config.get_config_value('basic_config', 'ENVIRONMENT'),
            "announcements"
        )
        self.announcement_channel = discord.utils.get(
            self.guild.channels, id=reminder_chan_id
        )
        self.logger.info(
            f"[Administration get_announcement_channel()] bot channel {self.announcement_channel} acquired."
        )

    @commands.Cog.listener(name="on_ready")
    async def upload_debug_logs(self):
        if self.config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, self.bot, self.config, self.debug_log_file_absolute_path,
                "administration_debug"
            )

    @commands.Cog.listener(name="on_ready")
    async def upload_error_logs(self):
        if self.config.get_config_value('basic_config', 'ENVIRONMENT') != 'TEST':
            while self.guild is None:
                await asyncio.sleep(2)
            await start_file_uploading(
                self.logger, self.guild, self.bot, self.config, self.error_log_file_absolute_path,
                "administration_error"
            )

    def valid_cog(self, name):
        for cog in self.config.get_cogs():
            if cog["name"] == name:
                return True, cog["path"]
        return False, ''

    @commands.command()
    async def exit(self, ctx):
        if 'LOCALHOST' == self.config.get_config_value('basic_config', 'ENVIRONMENT'):
            await self.bot.close()

    @app_commands.command(name="delete_log_channels")
    async def delete_log_channels(self, interaction: discord.Interaction):
        if 'LOCALHOST' == self.config.get_config_value('basic_config', 'ENVIRONMENT'):
            while self.guild is None:
                await asyncio.sleep(2)
            self.logger.info("[Administration delete_log_channels()] delete_log_channels command "
                             f"detected from {interaction.user}")
            await slash_command_checks(self.logger, self.config, interaction, self.help_dict)
            await interaction.response.defer()
            await BotChannelManager.delete_log_channels(interaction)
            e_obj = await embed(
                self.logger,
                interaction=interaction,
                description='Log Channels Deleted!',
                author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
                avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR')
            )
            if e_obj is not False:
                await interaction.followup.send(embed=e_obj)

    @commands.command()
    async def load(self, ctx, module_name):
        self.logger.info(f"[Administration load()] load command detected from {ctx.message.author}")
        valid, folder = self.valid_cog(module_name)
        if not valid:
            await ctx.send(f"```{module_name} isn't a real cog```")
            self.logger.info(
                f"[Administration load()] {ctx.message.author} tried loading "
                f"{module_name} which doesn't exist."
            )
            return
        try:
            await self.bot.add_custom_cog(folder+module_name)
            await ctx.send(f"{module_name} command loaded.")
            self.logger.info(f"[Administration load()] {module_name} has been successfully loaded")
        except(AttributeError, ImportError) as e:
            await ctx.send(f"command load failed: {type(e)}, {e}")
            self.logger.info(f"[Administration load()] loading {module_name} failed :{type(e)}, {e}")

    @commands.command()
    async def unload(self, ctx, module_name):
        self.logger.info(f"[Administration unload()] unload command detected from {ctx.message.author}")
        valid, folder = self.valid_cog(module_name)
        if not valid:
            await ctx.send(f"```{module_name} isn't a real cog```")
            self.logger.info(
                f"[Administration unload()] {ctx.message.author} tried loading "
                f"{module_name} which doesn't exist."
            )
            return
        await self.bot.remove_custom_cog(folder, module_name)
        await ctx.send(f"{module_name} command unloaded")
        self.logger.info(f"[Administration unload()] {module_name} has been successfully loaded")

    @commands.command()
    async def reload(self, ctx, name):
        self.logger.info(f"[Administration reload()] reload command detected from {ctx.message.author}")
        valid, folder = self.valid_cog(name)
        if not valid:
            await ctx.send(f"```{name} isn't a real cog```")
            self.logger.info(f"[Administration reload()] {ctx.message.author} tried "
                             f"loading {name} which doesn't exist.")
            return
        await self.bot.remove_custom_cog(folder, name)
        try:
            await self.bot.add_custom_cog(folder + name)
            await ctx.send(f"`{folder + name} command reloaded`")
            self.logger.info(f"[Administration reload()] {name} has been successfully reloaded")
        except(AttributeError, ImportError) as e:
            await ctx.send(f"Command load failed: {type(e)}, {e}")
            self.logger.info(f"[Administration reload()] loading {name} failed :{type(e)}, {e}")

    @commands.command()
    async def exc(self, ctx, *args):
        self.logger.info("[Administration exc()] exc command detected "
                         f"from {ctx.message.author} with arguments {' '.join(args)}")
        query = " ".join(args)
        # this got implemented for cases when the output of the command is too big to send to the channel
        exit_code, output = subprocess.getstatusoutput(query)
        await helper_send(self.logger, ctx, f"Exit Code: {exit_code}")
        await helper_send(self.logger, ctx, output, prefix="```", suffix="```")

    @commands.command()
    async def sync(self, ctx):
        self.logger.info(f"[AdministrationAdministration sync()] sync command detected from {ctx.message.author}")
        message = "Testing guild does not provide support for Slash Commands" \
            if self.config.get_config_value("basic_config", "ENVIRONMENT") == 'TEST' \
            else 'Commands Synced!'
        e_obj = await embed(
            self.logger,
            ctx=ctx,
            description=message,
            author=self.config.get_config_value('bot_profile', 'BOT_NAME'),
            avatar=self.config.get_config_value('bot_profile', 'BOT_AVATAR')
        )
        if self.config.get_config_value("basic_config", "ENVIRONMENT") != 'TEST':
            await self.bot.tree.sync(guild=self.guild)
        if e_obj is not False:
            await ctx.send(embed=e_obj)

    @commands.command()
    async def announce(self, ctx, *args):
        self.logger.info(f"[Administration announce()] announce command detected from {ctx.message.author}")
        await self.announcement_channel.send("\n".join(args))
        await ctx.message.delete()

    @commands.command()
    async def frequency(self, ctx, *args):
        if self.config.enabled("database_config", option="ENABLED"):
            self.logger.info("[Administration frequency()] frequency command "
                             f"detected from {ctx.message.author} with arguments [{args}]")
            column_headers = CommandStat.get_column_headers_from_database()
            if len(args) == 0:
                await ctx.send(f"please specify which columns you want to count={column_headers}")
                return
            else:
                for arg in args:
                    if arg not in column_headers:
                        await ctx.send(
                            f"argument '{arg}' is not a valid option\nThe list of options are"
                            f": {column_headers}"
                        )
                        return

            dic_result = sorted(
                (await CommandStat.get_command_stats_dict(args)).items(),
                key=lambda kv: kv[1]
            )
            self.logger.info("[Administration frequency()] sorted dic_results by value")
            image_path = f"{self.image_parent_directory}image.png"
            if len(dic_result) <= 50:
                self.logger.info("[Administration frequency()] dic_results's length is <= 50")
                labels = [i[0] for i in dic_result]
                numbers = [i[1] for i in dic_result]
                self.plt.rcdefaults()
                fig, ax = self.plt.subplots()
                y_pos = self.np.arange(len(labels))
                for i, v in enumerate(numbers):
                    ax.text(v, i + .25, f"{v}", color='blue', fontweight='bold')
                ax.barh(y_pos, numbers, align='center', color='green')
                ax.set_yticks(y_pos)
                ax.set_yticklabels(labels)
                ax.invert_yaxis()  # labels read top-to-bottom
                if len(args) > 1:
                    title = '-'.join(f"{arg}" for arg in args[:len(args) - 1])
                    title += f"-{args[len(args) - 1]}"
                else:
                    title = args[0]
                ax.set_title(f"How may times each {title} appears in the database since Sept 21, 2018")
                fig.set_size_inches(18.5, 10.5)
                fig.savefig(image_path)
                self.logger.info("[Administration frequency()] graph created and saved")
                self.plt.close(fig)
                await ctx.send(file=discord.File(image_path))
                self.logger.info("[Administration frequency()] graph image file has been sent")
            else:
                self.logger.info("[Administration frequency()] dic_results's length is > 50")
                number_of_pages = int(len(dic_result) / 50)
                if len(dic_result) % 50 != 0:
                    number_of_pages += 1
                number_of_bars_per_page = int(len(dic_result) / number_of_pages) + 1
                msg = None
                current_page = 0

                first_index = 0
                last_index = number_of_bars_per_page - 1
                boundaries_for_each_page = {}
                for page in range(0, number_of_pages):
                    boundaries_for_each_page[page] = {
                        'first_index': first_index,
                        'last_index': last_index
                    }
                    first_index += number_of_bars_per_page
                    last_index += number_of_bars_per_page

                while True:
                    self.logger.info("[Administration frequency()] creating "
                                     f"a graph with entries {first_index} to {last_index}")
                    to_react = ['⏪', '⏩', '✅']
                    first_index = boundaries_for_each_page[current_page]['first_index']
                    last_index = boundaries_for_each_page[current_page]['last_index']
                    labels = [i[0] for i in dic_result][first_index:last_index]
                    numbers = [i[1] for i in dic_result][first_index:last_index]
                    self.plt.rcdefaults()
                    fig, ax = self.plt.subplots()
                    y_pos = self.np.arange(len(labels))
                    for i, v in enumerate(numbers):
                        ax.text(v, i + .25, f"{v}", color='blue', fontweight='bold')
                    ax.barh(y_pos, numbers, align='center', color='green')
                    ax.set_yticks(y_pos)
                    ax.set_yticklabels(labels)
                    ax.invert_yaxis()  # labels read top-to-bottom
                    ax.set_xlabel(f"Page {current_page}/{number_of_pages - 1}")
                    if len(args) > 1:
                        title = '_'.join(f"{arg}" for arg in args[:len(args) - 1])
                        title += f"_{args[len(args) - 1]}"
                    else:
                        title = args[0]
                    ax.set_title(f"How may times each {title} appears in the database since Sept 21, 2018")
                    fig.set_size_inches(30, 10.5)
                    fig.savefig(image_path)
                    self.logger.info("[Administration frequency()] graph created and saved")
                    self.plt.close(fig)
                    if msg is None:
                        msg = await ctx.send(file=discord.File(image_path))
                    else:
                        await msg.delete()
                        msg = await ctx.send(file=discord.File(image_path))
                    for reaction in to_react:
                        await msg.add_reaction(reaction)

                    def check_reaction(reaction, user):
                        if not user.bot:  # just making sure the bot doesnt take its own reactions
                            # into consideration
                            e = f"{reaction.emoji}"
                            self.logger.info(f"[Administration frequency()] reaction {e} detected from {user}")
                            return e.startswith(('⏪', '⏩', '✅'))

                    self.logger.info("[Administration frequency()] graph image file has been sent")
                    user_reacted = None
                    while user_reacted is None:
                        try:
                            user_reacted = await self.bot.wait_for('reaction_add', timeout=20, check=check_reaction)
                        except asyncio.TimeoutError:
                            self.logger.info(
                                "[Administration frequency()] timed out waiting for the user's reaction."
                            )
                        if user_reacted:
                            if '⏪' == user_reacted[0].emoji:
                                current_page -= 1
                                if current_page < 0:
                                    current_page = number_of_pages - 1
                                self.logger.info("[Administration frequency()] user indicates they "
                                                 f" want to go back to page {current_page}")
                            elif '⏩' == user_reacted[0].emoji:
                                current_page += 1
                                if current_page >= number_of_pages:
                                    current_page = 0
                                self.logger.info(
                                    "[Administration frequency()] user indicates they "
                                    f"want to go to page {current_page}"
                                )
                            elif '✅' == user_reacted[0].emoji:
                                self.logger.info("[Administration frequency()] user "
                                                 "indicates they are done with the roles "
                                                 "command, deleting roles message")
                                await msg.delete()
                                return
                        else:
                            self.logger.info("[Administration frequency()] deleting message")
                            await msg.delete()
                            return
                    self.logger.info("[Administration frequency()] updating first_index "
                                     f"and last_index to {first_index} and {last_index} respectively")