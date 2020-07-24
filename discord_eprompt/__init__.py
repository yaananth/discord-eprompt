import asyncio

import discord
from discord.ext import commands

from enum import Enum

from typing import Dict

class ReactPromptPreset(Enum):
    """ 
    A preset is defined as a dictionary with the keys being emoji to react with, and the values being a string 
    representation of the response.
    """

    YES_NO = {'\U0001F44D': 'yes', '\U0001F44E': 'no'}
    DIGITS = {f'{i}\u20e3': i for i in range(10)}

async def on_prompt_reacted(prompt, bot, response:str, future):
    await prompt.message.delete()
    bot.remove_cog(prompt)
    
    future.set_result(response)

async def react_prompt_response(bot, user, message, preset:ReactPromptPreset=None, reacts:Dict[str, str]=None):
    if preset is None and reacts is None:
        raise ValueError('either a preset or set of reactions must be defined')
    elif preset is not None and reacts is not None:
        raise ValueError('cannot have both a preset and set of reactions')

    if preset is not None:
        reacts = preset.value

    loop = asyncio.get_running_loop()
    future = loop.create_future()

    prompt = ReactPrompt(bot, user, message, reacts, lambda response: on_prompt_reacted(prompt, bot, response, future))
    await prompt.setup()

    return await future

class ReactPrompt(commands.Cog):
    def __init__(self, bot: commands.Bot, user: discord.User, message: discord.Message, reacts: Dict[str, str], callback):
        self.bot = bot
        self.user = user
        self.message = message
        self.reacts = reacts
        self.callback = callback

        self.reactions_added = False

    async def setup(self):
        for react in self.reacts.keys():
            await self.message.add_reaction(react)
        self.reactions_added = True

        self.bot.add_cog(self)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.id != self.message.id:
            # Only act when the bound message is reacted to.
            return

        if user == self.bot.user:
            # Allow the bot to react with the choices.
            return

        if not self.reactions_added:
            await self.message.remove_reaction(reaction, user)
            return

        if user != self.user or str(reaction) not in self.reacts.keys():
            # Remove reactions from other users, or reactions that were not already made by the bot.
            await self.message.remove_reaction(reaction, user)
            return

        reaction_response = self.reacts[str(reaction)]
        await self.callback(reaction_response)
