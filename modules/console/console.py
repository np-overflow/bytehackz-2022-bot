from typing import Optional

from dis_snek.models import Scale, User, listen
from dis_snek.models.application_commands import (
    OptionTypes,
    component_callback,
    slash_command,
    slash_option,
    slash_permission
)
from dis_snek.models.context import InteractionContext
from dis_snek.models.discord_objects.channel import GuildText
from dis_snek.models.discord_objects.components import Button
from dis_snek.models.discord_objects.embed import Embed
from dis_snek.models.enums import ButtonStyles

from storage.console import Console
from utils.config import BOT_DEV_ROLE

from utils.embeds import CONSOLE
from utils.perms import ADMIN_ONLY, BOT_DEV_ONLY, NOT_EVERYBODY


class Console(Scale):
    def __init__(self, bot):
        self.bot = bot
        self.console: "Console" = bot.storage.container.console
        self.now_playing_user: Optional["User"] = None

    @listen()
    async def on_ready(self):
        await self.console.load_discord_objects(self.bot)
        if self.console.is_setup_done():
            await self._update_queue()
            # await self._update_leaderboard()  # Not needed

    @slash_command(
        name="console_setup",
        description="Setup the Console Games queue in a specified text channel"
    )
    @slash_option(
        "queuechannel",
        "ChannelID of channel to set up queue",
        OptionTypes.CHANNEL,
        required=True,
    )
    @slash_permission(NOT_EVERYBODY, BOT_DEV_ONLY)
    async def console_setup(self, ctx: InteractionContext, queuechannel):
        await ctx.defer()

        if type(queuechannel) != GuildText:
            await ctx.send(embeds=Embed("Whoops", f"Channels must be text channels", color="#F9AC42"))
            return

        if self.console.is_setup_done():
            await ctx.send(embeds=Embed("Whoops", f"You have already setup the console channels!", color="#F9AC42"))
            return

        await self._setup_queue_channel(queuechannel)
        # await self._setup_leaderboard_channel(boardchannel)
        self.bot.storage.save()

        await self._update_queue()
        # await self._update_leaderboard()

        await ctx.send("Queue setup completed!")

    async def _setup_queue_channel(self, queuechannel):
        await queuechannel.purge()
        await queuechannel.send(embeds=[CONSOLE])

        queue_msg = await queuechannel.send("Queue here!")
        self.console.queue.clear()
        self.console.set_queue_message(queue_msg)

        await queuechannel.send(
            "Wanna give it a try? Click here and we'll give u a direct ping when you're up!",
            components=[
                Button(
                    style=ButtonStyles.BLURPLE,
                    label="Queue up",
                    emoji="▶",
                    custom_id="getInQueueConsole",
                ),
                Button(
                    style=ButtonStyles.RED,
                    label="De-queue",
                    custom_id="getOutQueueConsole",
                )
            ],
        )

    @slash_command(
        name="console_next",
        description="Call up the next individual in the queue"
    )
    @slash_permission(NOT_EVERYBODY, ADMIN_ONLY)
    async def console_next(self, ctx: InteractionContext):
        if self.console.queue_is_empty():
            await ctx.send("Queue currently empty!")
            return

        if not self.console.queue_msg:
            await ctx.send("Please setup the console queue channel first!")
            return

        self.now_playing_user = await self.bot.get_user(self.console.dequeue())
        self.bot.storage.save()

        await self._update_queue()

        await ctx.send(f"It is now {self.now_playing_user}'s turn.")
        await self.now_playing_user.send(f"Hey {self.now_playing_user.display_name}! "
                                         f"You're up for the Console game, be here in 5 mins or we'll move on!")

    @component_callback("getInQueueConsole")
    async def get_in_queue(self, ctx):
        if not self.console.queue_msg:
            await ctx.send("Error: Queue channel not setup yet.", ephemeral=True)
            return

        author_id = ctx.author.id
        if author_id in self.console.queue:
            await ctx.send("You're already in the queue mate", ephemeral=True)
        else:
            self.console.enqueue(author_id)
            self.bot.storage.save()
            await self._update_queue()
            await ctx.send("Queue up successful! Wait for our ping!", ephemeral=True)

    @component_callback("getOutQueueConsole")
    async def get_out_queue(self, ctx):
        if not self.console.queue_msg:
            await ctx.send("Error: Queue channel not setup yet.", ephemeral=True)
            return

        author_id = ctx.author.id
        if author_id in self.console.queue:
            self.console.queue.remove(author_id)
            self.bot.storage.save()
            await ctx.send("De-queued you", ephemeral=True)
            await self._update_queue()
        else:
            await ctx.send("You are already not in the queue :(", ephemeral=True)

    async def _update_queue(self):
        text = "\n\n```\nNow playing:"
        if self.now_playing_user:
            text += f"{self.now_playing_user.display_name}\n\n"
        else:
            text += f"Nobody :(\n\n"

        if self.console.queue_is_empty():
            text += "\n\nThe queue is currently empty!"
        else:
            for index, user in enumerate(self.console.queue):
                u = await self.bot.get_user(user)
                text += f"{index + 1}. {u.display_name}\n"

        text += "```\n\n"

        await self.console.queue_msg.edit(text)


def setup(bot):
    Console(bot)
