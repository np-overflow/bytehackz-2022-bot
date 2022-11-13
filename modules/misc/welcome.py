from typing import Type
from dis_snek.models import Scale
from dis_snek.models.application_commands import (
    OptionTypes,
    slash_command,
    component_callback,
    slash_option,
)
from dis_snek.models.command import message_command
from dis_snek.models.context import InteractionContext
from dis_snek.models.discord_objects.embed import EmbedAttachment
from dis_snek.models.discord_objects.embed import Embed
from dis_snek.models.discord_objects.components import Button
from dis_snek.models.discord_objects.embed import Embed
from dis_snek.models.enums import ButtonStyles

from utils.config import GUILD
from discord.utils import get


class Welcome(Scale):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="welcome", description="It's time for Bytehackz 2022!")
    async def welcome(self, ctx: InteractionContext):
        embed = Embed(

            "Hello and welcome to Bytehackz 2022!",
            "The Byte®Hackz is an annual hackathon conducted for the Information Technology and Financial Informatics students taking the module Portfolio Development (PFD).\n\n\
            There will be 6 challenge statements, with 5 Groups of 4 to 5 Participants attempting each challenge statement.",
            color="#F9AC42",
            image="https://user-images.githubusercontent.com/53942938/200157862-45c1095d-0ea7-48c9-9566-5f5f11318e99.png"
        )

        await ctx.send(embeds=[embed])

        # await ctx.send("https://cdn.discordapp.com/attachments/895590724836401175/904702785965150278/unknown.png")
        await ctx.send(
            "Welcome to Bytehackz 2022, Claim your participant role here!",
            components=[
                Button(
                    style=ButtonStyles.BLURPLE,
                    label="Claim Role",
                    emoji="😀",
                    custom_id="claimRole",
                )
            ],
        )

    @component_callback("claimRole")
    async def claimRole(self, ctx):

        guild = await self.bot.get_guild(GUILD)
        role = get(guild.roles, name="Bytehackz Participant")
        if (ctx.author.has_role(role)):
            await ctx.send("Already Claimed Role", ephemeral=True)
        else:
            await ctx.author.add_role(role)
            await ctx.send("Sucessfully claimed role, Welcome To Bytehackz 2022!", ephemeral=True)


def setup(bot):
    Welcome(bot)
