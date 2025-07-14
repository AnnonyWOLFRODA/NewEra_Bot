"""
Discord utilities for NEBot.
Contains helper functions for discord commands.
"""
import asyncio
import discord
# The bot instance must be set at runtime (e.g. by main.py)

error_color_int = int("FF5733", 16)
class discordUtils:
    """
    A utility class for Discord-related functions.
    This class provides methods to check user authorization, send messages, and handle reactions.
    """

    def __init__(self, bot):
        self.bot = bot

    def is_authorized(self, ctx) -> bool:
        authorized_role_id = 1230046019262087198
        return authorized_role_id in [role.id for role in ctx.author.roles]

    async def discord_input(self, ctx, message: str) -> str:
        await ctx.send(message)
        try:
            response = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=90)
        except asyncio.TimeoutError:
            return ""
        return response.content

    async def send_long_message(self, ctx, message: str):
        messages = []
        while len(message) > 2000:
            index = message.rfind("\n", 0, 2000)
            messages.append(message[:index])
            message = message[index:]
        messages.append(message)
        for msg in messages:
            await ctx.send(msg)

    def get_auth_embed(self) -> discord.Embed:
        """
        Creates a Discord embed message indicating lack of authorization.

        This function generates an embed message that informs the user they are not authorized to execute a command and that they need to be a staff member.

        Returns:
            discord.Embed: The embed message with the authorization error.
        """
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int
        )
        return embed

    async def get_users_by_reaction(self, emoji: list, message: discord.Message):
        """
        Retrieve a list of users who reacted to a message with specific emojis.

        Args:
            emoji (list): A list of emojis to check for reactions.
            message (discord.Message): The Discord message to check reactions on.

        Returns:
            list: A list of users who reacted with the specified emojis.
        """
        users = []
        for reaction in message.reactions:
            if reaction.emoji in emoji:
                async for user in reaction.users():
                    users.append(user)
        return users
    
    def parse_embed_json(json_file):
        embeds_json = json.loads(json_file)["embeds"]

        for embed_json in embeds_json:
            embed = discord.Embed().from_dict(embed_json)
            yield embed
