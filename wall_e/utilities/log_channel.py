import asyncio
import aiohttp
import discord


async def write_to_bot_log_channel(logger, config, bot, file_path, chan_id):
    """
    Takes care of opening a file and keeping it opening while reading from it and uploading it's contents
     to the specified channel
    :param logger: the service's logger instance
    :param config: used to determine the gmail credentials
    :param bot: needed to get the channel ID for the channel that the logs will be sent to and ensure the
     while loop only runs while bot.is_closed() is False
    :param file_path: the path of the log file to upload to the text channel
    :param chan_id: the ID of the channel that the log file lines will be uploaded to
    :param error_channel: indicator of whether chan_id is for an error channel and therefore error emails
     may need to be sent
    :return:
    """
    channel = discord.utils.get(
        bot.guilds[0].channels, id=chan_id
    )
    logger.debug(
        f"[log_channel.py write_to_bot_log_channel()] {channel} channel "
        f"with id {chan_id} successfully retrieved."
    )
    f = open(file_path, 'r')
    f.seek(0)
    incident_report_chanel_name = config.get_config_value('channel_names', 'INCIDENT_REPORT_CHANNEL')
    while not bot.is_closed():
        f.flush()
        line = f.readline()
        while line:
            if line.strip() != "":
                # this was done so that no one gets accidentally pinged from the bot log channel
                if channel.name != incident_report_chanel_name:
                    line = line.replace("@", "[at]")
                if line[0] == ' ':
                    line = f".{line}"
                output = line
                # done because discord has a character limit of 2000 for each message
                # so what basically happens is it first tries to send the full message, then if it cant, it
                # breaks it down into 2000 sizes messages and send them individually
                try:
                    await channel.send(output)
                except (aiohttp.ClientError, discord.errors.HTTPException):
                    finished = False
                    first_index, last_index = 0, 2000
                    while not finished:
                        await channel.send(output[first_index:last_index])
                        first_index = last_index
                        last_index += 2000
                        if len(output[first_index:last_index]) == 0:
                            finished = True
                except RuntimeError:
                    logger.debug(
                        "[log_channel.py write_to_bot_log_channel()] encountered RuntimeError, "
                        " will assume that the user is attempting to exit"
                    )
                    break
                except Exception as exc:
                    exc_str = f'{type(exc).__name__}: {exc}'
                    raise Exception(
                        f'[log_channel.py write_to_bot_log_channel()] write to channel failed\n{exc_str}'
                    )
            line = f.readline()
        await asyncio.sleep(1)
