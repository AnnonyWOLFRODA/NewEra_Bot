from http.client import FORBIDDEN
import discord
import time
from pyutil import filereplace
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import asyncio
import discord.utils
from time import sleep
import json
from discord.ext.commands import has_role, Context, Converter, BadArgument
from discord.ext import tasks
import urllib.request
import random
import aiohttp
import os
import re
import sqlite3
import events
from construction import *
from currency import *
from db import *
from notion_handler import *
from discord_utils import *
from text_formatting import *
from typing import Union
import interactions
from PIL import Image
import pytz
import io
import string
import locale
import traceback

# Import centralized utilities
from shared_utils import (
    initialize_utilities,
    get_db,
    get_discord_utils,
    CountryEntity,
    CountryConverter,
    ERROR_COLOR_INT as error_color_int,
    MONEY_COLOR_INT as money_color_int,
    P_POINTS_COLOR_INT as p_points_color_int,
    D_POINTS_COLOR_INT as d_points_color_int,
    ALL_COLOR_INT as all_color_int,
    FACTORY_COLOR_INT as factory_color_int,
)
import requests
from dotenv import dotenv_values
import math
import contextlib
from discord.ui import Button, View, Modal, TextInput
from discord import message, emoji, Webhook, SyncWebhook
from removebg import RemoveBg
from context import *
from groq import Groq

Erreurs = {}
continents = []

token = dotenv_values(".env")["TOKEN"]
removebg_apikey = dotenv_values(".env")["REMOVEBG_API_KEY"]
groq_api_key = dotenv_values(".env")["GROQ_API_KEY"]
notion_token = dotenv_values(".env")["NOTION_TOKEN"]

_orig_print = print


def print(*args, **kwargs):
    _orig_print(*args, flush=True, **kwargs)


intents = discord.Intents().all()
bot = commands.Bot(
    intents=intents,
    activity=discord.Game(name="Aider le staff!"),
    command_prefix=[".", "/"],
)
usefull_role_ids_dic = {}
groq_client = Groq(api_key=groq_api_key)
last_groq_query_time = datetime.now(timezone.utc)


async def load_cogs():
    """Load all cogs for the bot."""
    try:
        print("🔄 Loading economy cog...")
        await bot.load_extension("cogs.economy")
        print("✅ Economy cog loaded successfully")

        print("🔄 Loading points cog...")
        await bot.load_extension("cogs.points")
        print("✅ Points cog loaded successfully")

        print("🔄 Loading structures cog...")
        await bot.load_extension("cogs.structures")
        print("✅ Structures cog loaded successfully")

        print("🔄 Loading admin utilities cog...")
        await bot.load_extension("cogs.admin_utilities")
        print("✅ AdminUtilities cog loaded successfully")

        # List loaded commands for debugging
        economy_commands = [cmd for cmd in bot.commands if cmd.cog_name == "Economy"]
        points_commands = [cmd for cmd in bot.commands if cmd.cog_name == "Points"]
        structures_commands = [
            cmd for cmd in bot.commands if cmd.cog_name == "Structures"
        ]
        admin_commands = [
            cmd for cmd in bot.commands if cmd.cog_name == "AdminUtilities"
        ]
        print(f"📋 Loaded economy commands: {[cmd.name for cmd in economy_commands]}")
        print(f"📋 Loaded points commands: {[cmd.name for cmd in points_commands]}")
        print(
            f"📋 Loaded structures commands: {[cmd.name for cmd in structures_commands]}"
        )
        print(f"📋 Loaded admin commands: {[cmd.name for cmd in admin_commands]}")
    except Exception as e:
        print(f"❌ Failed to load cogs: {e}")
        import traceback

        traceback.print_exc()


@bot.event
async def on_ready():
    """Event triggered when the bot is ready."""
    print(f"✅ Bot is ready! Logged in as {bot.user}")
    print("🔧 Utilities already initialized")

    await load_cogs()
    polling_notion.start()
    update_rp_date.start()


rmbg = RemoveBg(removebg_apikey, "error.log")

duration_in_seconds = 0
groq_chat_history = []

code_list = []
POLLING_INTERVAL = 300  # en secondes (ici toutes les 5 minutes)

# Usine = 0
# Terrestre = 1
# Aerienne = 2
# Maritime = 3
# Ecole = 4


with open("datas/usines.json") as f:
    production_data = json.load(f)
with open("datas/bases.json") as f:
    base_data = json.load(f)
with open("datas/main.json") as f:
    json_data = json.load(f)
    bat_types = json_data["bat_types"]
    query_types = json_data["query_types"]
    bi_admins_id = json_data["bi_admins_id"]
    code_list = json_data["code_list"]
    buildQuality = json_data["buildQuality"]
    bat_buffs = json_data["bat_buffs"]
    unit_types = json_data["unit_types"]

usefulDatas = UsefulDatas(bat_types, bat_buffs)

# Initialize utilities early for debug_init
initialize_utilities(bot, bat_types, bat_buffs)
db = get_db()
db.init_settings()
db.init_inventory_pricings()
dUtils = get_discord_utils(bot, db)
notion_handler = NotionHandler(notion_token, bot)

# --- All global variables

debug = db.get_setting("debug")
continents = ["Europe", "Amerique", "Asie", "Afrique", "Moyen-Orient", "Oceanie"]
continents_dict = {
    "europe": db.get_setting("europe_category_id"),
    "amerique": db.get_setting("america_category_id"),
    "asie": db.get_setting("asia_category_id"),
    "afrique": db.get_setting("africa_category_id"),
    "moyen-orient": db.get_setting("middle_east_category_id"),
    "oceanie": db.get_setting("oceania_category_id"),
}
starting_amounts = {
    "money": db.get_setting("starting_amount_money"),
    "pol_points": db.get_setting("starting_amount_pol_points"),
    "diplo_points": db.get_setting("starting_amount_diplo_points"),
}
usefull_role_ids_dic = {"staff": db.get_setting("staff_role_id")}
Erreurs = {
    "Erreur 1": "Le salon dans lequel vous effectuez la commande n'est pas le bon\n",
    "Erreur 2": "Aucun champ de recherche n'a été donné\n",
    "Erreur 3": "Le champ de recherche donné est invalide\n",
    "Erreur 3.2": "Le champ de recherche donné est invalide - Le pays n'est pas dans les fichiers\n",
    "Erreur 4": "La pause est déjà en cours\n",
    "Erreur 5": "Vous n'avez pas la permission de faire la commande.\n",
}
error_color_int = int("FF5733", 16)
money_color_int = int("FFF005", 16)
p_points_color_int = int("006AFF", 16)
d_points_color_int = int("8b1bd1", 16)
factory_color_int = int("6E472E", 16)
all_color_int = int("00FF44", 16)

### DEBUG

db.debug_init()

# --- Task de polling ---


@tasks.loop(seconds=POLLING_INTERVAL)
async def polling_notion():
    try:
        await notion_handler.check_for_updates()
    except Exception as e:
        print(f"Erreur lors du polling Notion: {e}")


@tasks.loop(minutes=1)
async def update_rp_date():
    now = datetime.now(pytz.timezone("Europe/Paris"))  # ou "UTC"
    if now.hour == 7 and now.minute == 0:
        await db.advance_playday()


@update_rp_date.before_loop
async def before():
    await bot.wait_until_ready()


###


@bot.command(
    name="resume_rp",
    brief="Relance le temps RP après une pause (Admin uniquement).",
    usage="resume_rp",
    description="Relance le compteur de temps du roleplay après une pause administrative.",
    help="""Relance le système de temps du roleplay après une pause.

    FONCTIONNALITÉ :
    - Réactive le compteur de temps RP
    - Met fin à l'état de pause du jeu
    - Permet la reprise des activités temporelles
    - Confirme la réactivation via un message

    UTILISATION :
    - Reprise après maintenance
    - Fin d'une pause administrative
    - Résolution de problèmes techniques

    RESTRICTIONS :
    - Réservé aux administrateurs uniquement
    - Ne fonctionne que si le jeu est en pause

    ARGUMENTS :
    - Aucun argument requis

    EXEMPLE :
    - `resume_rp` : Relance le temps RP
    """,
    hidden=False,
    enabled=True,
    case_insensitive=True,
)
@commands.has_permissions(administrator=True)
async def resume_rp(ctx):
    db.set_paused(False)
    await ctx.send("✅ Le temps RP a été relancé !")


@bot.command(
    name="date",
    brief="Affiche la date actuelle du jeu RP.",
    usage="date",
    description="Consulte la date et le temps actuel dans l'univers du roleplay.",
    help="""Affiche la date actuelle du roleplay avec les informations temporelles complètes.

    FONCTIONNALITÉ :
    - Affiche l'année, le mois et le jour RP actuels
    - Indique l'état du système de temps (actif/en pause)
    - Utilise le calendrier français pour l'affichage
    - Montre la progression dans le mois actuel

    INFORMATIONS AFFICHÉES :
    - Année en cours du RP
    - Mois en français (avec accentuation)
    - Jour du mois (playday)
    - État du système temporel

    UTILISATION :
    - Vérification du timing pour les actions
    - Planification d'événements RP
    - Synchronisation des joueurs

    ARGUMENTS :
    - Aucun argument requis

    EXEMPLE :
    - `date` : Affiche "Nous sommes le 15 Mars 2045"
    """,
    hidden=False,
    enabled=True,
    case_insensitive=True,
)
async def date(ctx):
    """Affiche la date actuelle du jeu."""
    if db.is_paused():
        await ctx.send("Le temps RP est actuellement en pause.")
        return

    date_dict = db.get_current_date()
    year, month, playday = (
        date_dict.get("year", 1),
        date_dict.get("month", 1),
        date_dict.get("playday", 1),
    )

    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")  # Système Unix/Linux
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, "fr_FR")  # Windows
        except locale.Error as e:
            await ctx.send(f"⚠️ Impossible de définir la locale française. {e}")
            return

    month_name = datetime(year, month, 1).strftime("%B")
    max_playdays = db.get_playdays_in_month(month)

    await ctx.send(
        f"📅 Date actuelle : {month_name.capitalize()} {year} - {playday}/{max_playdays}"
    )


@bot.event
async def on_message(message):
    if (
        isinstance(message.channel, discord.DMChannel)
        and message.author.id == 293869524091142144
        and message.content.startswith("!")
    ):
        await bot.get_channel(db.get_setting("tchat_channel_id")).send(
            message.content[1:]
        )
    if (message.author == bot.user) or (not message.content):
        return
    if message.author.id == 292953664492929025:
        for embed in message.embeds:
            if embed.description.startswith("<:xmark:773218895150448640> "):
                sleep(10)
                await message.delete()
    if message.content == len(message.content) * message.content[0]:
        return
    if "soup" in message.content.lower():
        await message.add_reaction("🥣")
    await bot.process_commands(message)


async def insert_mention(
    message: discord.Message, user: discord.User, mentions: dict = None
):
    """
    Inserts a mention into the embed description of a Discord message.

    Args:
        message (discord.Message): The Discord message object containing the embed.
        user (discord.User): The Discord user to mention.
        mentions (dict, optional): A dictionary to store mentions with user mentions as keys and user IDs as values. Defaults to None.

    Returns:
        None
    """
    embed = message.embeds[0]
    message_content = embed.description
    mentions[user.mention] = user.id
    mention_str = " | ".join([f"{key} ({value})" for key, value in mentions.items()])
    message_content += mention_str + "\n"
    embed = discord.Embed(
        title=message.embeds[0].title, description=message_content, color=all_color_int
    )
    await message.edit(embed=embed)


async def handle_treaty(reaction: discord.Reaction, user: discord.User):
    async def handle_treaty(reaction: discord.Reaction, user: discord.User):
        """
        Handles the treaty reaction event.

        This function is triggered when a user reacts to a message with a specific emoji.
        It checks if the reaction emoji is either "🖋️" or "🖊️". If the emoji is valid,
        it parses the mentions from the message's embed description and inserts the user's
        mention if it is not already present.

        Args:
            reaction (discord.Reaction): The reaction object containing the emoji and the message.
            user (discord.User): The user who reacted to the message.

        Returns:
            None
        """

    if reaction.emoji not in ["🖋️", "🖊️"]:
        return
    message = reaction.message
    mentions = parse_mentions(message.embeds[0].description)
    if user.mention in mentions.keys():
        return
    await insert_mention(message, user, mentions)


async def create_treaty(reaction, user):
    """
    Asynchronously creates a treaty message when a specific reaction is added to a message.

    Args:
        reaction (discord.Reaction): The reaction that triggered the function.
        user (discord.User): The user who added the reaction.

    Returns:
        None

    Behavior:
        - If the reaction emoji is not "✅", the function returns immediately.
        - Retrieves the content of the message that received the reaction.
        - Fetches a list of users who reacted with specific emojis ("🖋️" and "🖊️") to the message.
        - Constructs a message content string that includes the original message content and mentions of the users.
        - Creates and sends an embedded message to the same channel with the constructed content.
    """
    message = reaction.message
    if reaction.emoji != "✅":
        return
    message_content = f"Traité crée, officialisé et signé par les membres précisés dans la section ``Mention``.\n\nContenu du traité : \n\n{message.content}"
    user_list = await dUtils.get_users_by_reaction(["🖋️", "🖊️"], message)
    mentions = {user.mention: user.id for user in user_list}
    mention_str = " | ".join([f"{key} ({value})" for key, value in mentions.items()])
    message_content += f"\n\n Mention : {mention_str}"
    embed = discord.Embed(
        title="Traité", description=message_content, color=all_color_int
    )
    new_message = await message.channel.send(embed=embed)


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user == bot.user:
        return
    message = reaction.message
    if (
        message.channel.id != 1396922371121610792
        and message.channel.category.id != 1269295981183369279
    ):
        return
    if (
        message.author == bot.user
        and reaction.emoji in ["🖋️", "🖊️"]
        and message.channel.id == 1396922371121610792
    ):
        await handle_treaty(reaction, user)
    elif reaction.emoji == "✅":
        await create_treaty(reaction, user)


@bot.command()
async def notion(ctx, req_type: str = "all"):
    await ctx.defer()
    req_type = req_type.lower()
    try:
        embeds = await notion_handler.get_tasks(ctx, req_type)
        if not embeds:
            await ctx.send(
                "❌ Aucune tâche trouvée ou erreur lors de la récupération des données Notion."
            )
            return

        # Send each embed separately for better space management
        for embed in embeds:
            await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Erreur lors de la récupération des données Notion : {e}")


@bot.command(
    name="sign_user_to_treaty",
    brief="Propose la signature d'un traité à un utilisateur.",
    usage="sign_user_to_treaty <message> <user>",
    description="Permet à un utilisateur de signer un traité et, si besoin, d'envoyer le traité dans un salon secret.",
    help="""Propose à un utilisateur de signer un traité dont les détails sont contenus dans un message donné.

    ARGUMENTS :
    - `<message>` : Message contenant le traité (de préférence, un message du bot lui-même).
    - `<user>` : Utilisateur Discord invité à signer le traité.

    EXEMPLE :
    - `sign_user_to_treaty 123456789012345678 @utilisateur` : Invite l'utilisateur mentionné à signer le traité contenu dans le message avec l'ID spécifié.
    """,
    hidden=False,
    enabled=True,
    case_insensitive=True,
)
async def sign_user_to_treaty(
    ctx,
    message: discord.Message = commands.parameter(
        description="Message contenant le traité à signer."
    ),
    user: discord.User = commands.parameter(
        description="Utilisateur invité à signer le traité."
    ),
) -> None:
    if message.author != bot.user:
        return
    try:
        waiting_message = await user.send(
            f"Voulez-vous signer le traité dont les détails sont ci-dessous?\n\n{message.content} (Oui/Non)"
        )
        response = await bot.wait_for(
            "message",
            check=lambda m: m.author == user and m.channel == waiting_message.channel,
            timeout=120,
        )
        if response.content.lower() == "oui":
            await insert_mention(
                ctx.message, user, parse_mentions(ctx.message.embeds[0].description)
            )
            if message.channel.category.id == 1269295981183369279:
                waiting_message = await user.send(
                    "Veuillez indiquer l'ID / Lien / Mention de votre salon secret."
                )
                response = await bot.wait_for(
                    "message",
                    check=lambda m: m.author == user
                    and m.channel == waiting_message.channel,
                    timeout=120,
                )
                response = message.guild.get_channel(response.content.strip())
                await response.send(embed=message.embeds[0])
            await user.send("Vous avez signé le traité.")
    except discord.Forbidden:
        await ctx.send("Impossible d'obtenir l'utilisateur.")
        return


@bot.event
async def on_command_error(ctx, error):
    tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    # Only show first line and line number for users, full traceback for admins
    error_msg = f"**Error:** {error}\n"
    if error.__traceback__:
        tb_lines = tb.splitlines()
        # Find the most recent call line
        for line in reversed(tb_lines):
            error_msg += f"`{line.strip()}`\n"
    embed = discord.Embed(
        title="Une erreur s'est produite en exécutant la commande",
        description="**Message d'erreur:** " + str(error),
        color=discord.Color.red(),
    )
    await ctx.send(embed=embed)
    print(f"❌ Error in command {ctx.command}: {error}")
    print(f"Full traceback:\n{tb}")


class ConstructionForm(discord.ui.Modal, title="Données de construction"):
    def __init__(self, goal: str):
        super().__init__()

        self.objectif = discord.ui.TextInput(
            label=(
                "Objectif d'habitants"
                if goal == "habitants"
                else "Budget de construction"
            ),
            placeholder="Ex: 200",
            required=True,
        )
        self.max_etages = discord.ui.TextInput(
            label="Nombre max d'étages", default="10", required=False
        )
        self.max_apartments = discord.ui.TextInput(
            label="Nombre max de logements/étage", default="30", required=False
        )
        self.appt_lvl = discord.ui.TextInput(
            label="Niveau de qualité des logements", default="1", required=False
        )
        self.taille_appt = discord.ui.TextInput(
            label="Taille moyenne des logements (en m²)", default="40", required=False
        )

        # Ajout explicite des champs dans le Modal
        self.add_item(self.objectif)
        self.add_item(self.max_etages)
        self.add_item(self.max_apartments)
        self.add_item(self.appt_lvl)
        self.add_item(self.taille_appt)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        appt_lvl_int = int(self.appt_lvl.value or 1)
        datas = {
            "objectif": int(self.objectif.value),
            "max_etages": int(self.max_etages.value or 10),
            "max_apartments": int(self.max_apartments.value or 30),
            "appt_lvl": appt_lvl_int,
            "taille_moyenne": int(self.taille_appt.value or 40),
            "type_murs": buildQuality["walls"][str(appt_lvl_int)],
            "prix_moyen": buildQuality["price"][str(appt_lvl_int)],
            "people_per_apartment": get_people_per_apartment(
                int(self.taille_appt.value or 40)
            ),
            "objectif_type": (
                "habitants" if "habitants" in self.objectif.label.lower() else "cout"
            ),
            "prix_fondations": 50,
        }

        if datas["objectif_type"] == "habitants":
            buildings, datas = await calculate_by_population_from_datas(
                interaction, datas
            )
        else:
            buildings, datas = await calculate_by_budget_from_datas(interaction, datas)
        await send_building_summary(interaction, buildings, datas)


@bot.command(
    name="construction_immeuble",
    brief="Construit un immeuble basé sur le nombre d'habitants ou un budget.",
    usage="construction_immeuble",
    description="Permet à l'utilisateur de construire un immeuble en spécifiant soit un objectif de nombre d'habitants soit un coût de construction.",
    help="""Interagit avec l'utilisateur pour établir un projet de construction d'immeubles selon ses choix et contraintes.

    DESCRIPTION DU PROCESSUS :
    - Cette commande guide l'utilisateur pour calculer les coûts et surfaces de plusieurs bâtiments selon une estimation du nombre d'habitants ou un budget maximum.
    - Elle génère ensuite un bilan détaillé pour chaque bâtiment, ainsi qu'un récapitulatif final qui présente les coûts et surfaces totales.
    - Si le nombre de bâtiments est élevé, un fichier texte est envoyé à la place pour éviter le dépassement de la limite de caractères.

    ARGUMENTS :
    - Aucun argument n'est requis pour exécuter cette commande, car elle prend des informations via des interactions avec l'utilisateur.

    EXEMPLE :
    - `construction_immeuble` : Lance le programme de construction d'immeubles et invite l'utilisateur à choisir entre un objectif d'habitants ou un budget de construction.
    """,
    hidden=False,
    enabled=True,
    case_insensitive=True,
)
async def construction_immeuble(ctx, goal: str = None) -> None:
    """Commande classique qui initie un bouton vers un formulaire modal"""
    if not goal:
        goal = await dUtils.discord_input(
            ctx,
            "Bienvenue dans le programme de construction d'immeubles!\nVoulez-vous construire un immeuble par nombre d'habitants ou par coût de construction? (habitants/coût)",
        )
    goal = goal.lower()
    if goal not in ["habitants", "habitant", "coût", "cout"]:
        await ctx.send("Veuillez répondre par 'habitants' ou 'coût'.")
        return
    if goal == "coût":
        goal = "cout"
    if goal == "habitant":
        goal = "habitants"

    class ModalTriggerView(discord.ui.View):
        @discord.ui.button(
            label="📋 Remplir le formulaire", style=discord.ButtonStyle.green
        )
        async def launch_modal(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            await interaction.response.send_modal(ConstructionForm(goal))

    await ctx.send(
        "📋 Cliquez sur le bouton ci-dessous pour ouvrir le formulaire :",
        view=ModalTriggerView(),
    )


@bot.command()
async def lead(ctx):
    async def create_lead_embed(leaderboard, offset):
        embed = discord.Embed(
            title=f"Classement des pays (de {offset + 1} à {offset + len(leaderboard)})",
            color=0x00FF00,
        )
        for i, (role_id, balance, pp, pd) in enumerate(leaderboard, offset + 1):
            role = ctx.guild.get_role(int(role_id))
            if role:
                rolename = role.name + f" - {str(role_id)}"
            else:
                rolename = str(role_id) + " - Non identifié"
            embed.add_field(
                name=f"{i}. {rolename}",
                value=f":moneybag: **{convert(str(balance))}** argent -- :blue_circle: **{pp}** points politiques -- :green_circle: **{pd}** points diplos",
                inline=False,
            )
        return embed

    leaderboard = await db.get_leaderboard()

    if len(leaderboard) == 0:
        return await ctx.send("Le classement est vide.")

    view = View()
    max_entries = 100  # Limite maximum du nombre d'utilisateurs à afficher

    async def next_callback(interaction):
        nonlocal offset
        offset += 10
        leaderboard = await db.get_leaderboard(offset)
        if len(leaderboard) > 0:
            embed = await create_lead_embed(leaderboard, offset)
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            offset -= 10

    async def prev_callback(interaction):
        nonlocal offset
        if offset > 0:
            offset -= 10
            leaderboard = await db.get_leaderboard(offset)
            embed = await create_lead_embed(leaderboard, offset)
            await interaction.response.edit_message(embed=embed, view=view)

    offset = 0
    embed = await create_lead_embed(leaderboard, offset)

    prev_button = Button(label="◀️ Précédent", style=discord.ButtonStyle.primary)
    prev_button.callback = prev_callback
    next_button = Button(label="▶️ Suivant", style=discord.ButtonStyle.primary)
    next_button.callback = next_callback

    view.add_item(prev_button)
    view.add_item(next_button)

    await ctx.send(embed=embed, view=view)


@bot.command()
async def appareil_info(ctx, appareil):
    app_type = db.find_app_type(appareil)
    if app_type is None:
        await ctx.send("Appareil non trouvé.")
        return
    # Récupérer les données de production pour chaque niveau
    prod_datas = []
    for i in range(1, 8):
        prod_datas.append(
            production_data[f"{i}"]["production_mensuelle"][app_type][appareil]
        )
    # Construire la chaîne de caractères pour la production mensuelle
    production_info = ""
    for i in range(1, 8):
        production_info += f"Niveau {i}: {convert(str(prod_datas[i-1]))}\n"
    # Créer l'embed avec les informations de l'appareil
    embed = discord.Embed(
        title=f"Information sur l'appareil {appareil}",
        description=f"Type: {app_type}\nProduction mensuelle par niveau d'usine:\n{production_info}",
        color=0x00FF00,
    )
    # Envoyer l'embed
    await ctx.send(embed=embed)


def is_valid_lvl(type: int, lvl: int):
    if lvl < 0:
        return False
    if type == 0 and lvl <= 7:
        return True
    elif type == 1 and lvl <= 7:
        return True
    elif type == 2 and lvl <= 4:
        return True
    elif type == 3 and lvl <= 4:
        return True
    elif type == 4 and lvl <= 4:
        return True
    else:
        return False


@bot.command()
async def production_time(ctx, app, qty, app_type=None, user: discord.Member = None):
    if db.find_app_type(app, production_data) is None:
        await ctx.send("Appareil non trouvé.")
        return
    app_type = db.find_app_type(app, production_data)
    if not user:
        user = ctx.author
    await ctx.send(
        db.calculer_temps_production(
            user.id, app.lower(), qty, app_type, production_data
        )
    )


@bot.command()
async def list_apparels(ctx):
    app_types = ["terrestre", "navale", "aerienne", "explosif"]
    apparels = []

    for app_type in app_types:
        for apparel in production_data["7"]["production_mensuelle"][app_type]:
            apparels.append(apparel)
    await dUtils.send_long_message(ctx, "\n- ".join(apparels))


@bot.command(
    name="create_country",
    brief="Crée un pays, en lui attribuant ses ressources, son rôle, et son salon.",
    usage="create_country <membre> <emoji_drapeau> <nom_sans_espace> <continent>",
    description="create_country <membre> <emoji_drapeau> <nom_sans_espace> <continent>",
    help="""Crée un pays, en lui attribuant ses ressources, son rôle, et son salon.
    ARGUMENTS :
    - `<membre>` : Le membre Discord auquel attribuer le pays (mention ou ID).
    - `<emoji_drapeau>` : Emoji représentant le drapeau du pays.
    - `<nom_sans_espace>` : Nom du pays, sans espaces (utilisez des underscores `_` si besoin).
    - `<continent>` : Le nom ou ID du continent (Europe, Amérique, Asie, Afrique, Océanie, Moyen-Orient).
    EXEMPLE :
    - `create_country @membre :flag_fr: France Europe` : Crée le pays France sur le continent Europe pour membre.
    """,
    hidden=False,
    enabled=True,
    case_insensitive=True,
)
async def create_country(
    ctx,
    user: discord.Member = commands.parameter(
        description="ID ou mention du membre auquel attribuer le pays"
    ),
    country_flag=commands.parameter(
        description="Emoji représentant le drapeau du pays"
    ),
    country_name=commands.parameter(
        description="Nom du pays sans espaces. Remplacez les espaces par des underscores `_`."
    ),
    continent: Union[discord.CategoryChannel, str] = commands.parameter(
        description="ID ou nom du continent (Europe, Amérique, Asie, etc.). Accents et majuscules autorisés."
    ),
) -> None:
    continents = {
        "europe": 955479237001891870,
        "amerique": 952314456870907934,
        "asie": 1243672298381381816,
        "afrique": 961678827933794314,
        "oceanie": 992368253580087377,
        "moyen-orient": 951163668102520833,
    }
    player_role = await dUtils.get_player_role(ctx)
    non_player_role = await dUtils.get_non_player_role(ctx)
    if not dUtils.is_authorized(ctx):
        return await ctx.send(embed=dUtils.get_auth_embed())
    continent = (continent.replace("é", "e")).lower()
    if type(continent) == str and continent in continents.keys():
        continent = discord.utils.get(ctx.guild.categories, id=continents[continent])
    if type(continent) != discord.CategoryChannel:
        return await ctx.send("Continent invalide.")

    # Initialize country resources directly
    country_entity = CountryEntity(user, ctx.guild).to_dict()
    if country_entity and country_entity.get("id"):
        country_id = country_entity["id"]
        db.set_balance(country_id, starting_amounts["money"])
        db.set_points(country_id, starting_amounts["pp"], 1)  # Political points
        db.set_points(country_id, starting_amounts["pd"], 2)  # Diplomatic points

    country_name = country_name.replace("_", " ")
    role_name = f"《{country_flag}》{country_name}"
    country_name = convert_country_name(country_name)
    channel_name = f"「{country_flag}」{country_name}"
    channel = await continent.create_text_channel(channel_name)
    role = await ctx.guild.create_role(name=role_name)
    await channel.set_permissions(
        ctx.guild.default_role,
        manage_webhooks=False,
        view_channel=True,
        read_messages=True,
        send_messages=False,
    )
    await channel.set_permissions(
        role,
        manage_webhooks=True,
        view_channel=True,
        read_messages=True,
        send_messages=True,
        manage_messages=True,
    )
    await channel.send(f"Bienvenue dans le pays de {country_name} !")
    await user.add_roles(role, reason=f"Création du pays {country_name}")
    await user.add_roles(player_role, reason=f"Création du pays {country_name}")
    await user.remove_roles(non_player_role, reason=f"Création du pays {country_name}")
    await ctx.send(f"Le pays {country_name} a été créé avec succès.")


@bot.command(
    name="create_secret",
    brief="Crée un service secret, en attribuant les permissions correctes pour le pays à qui il appartient.",
    usage="create_secret <country_role> <service_icon> <nom_sans_espace>",
    description="create_secret <country_role> <service_icon> <nom_sans_espace>",
    help="""Crée un service secret, en attribuant les permissions correctes pour le pays à qui il appartient
    ARGUMENTS :
    - `<country_role>` : Role du pays à qui appartient le service secret.
    - `<service_icon>` : Emoji de l'emoji à côté du service secret.
    - `<nom_sans_espace>` : Nom du service secret sans espace - les espaces sont à remplacer par des underscores.
    - `create_secret @role :flag_fr: DGSI` : Crée le service secret 'DGSI' du pays @role avec l'emoji du drapeau français.
    """,
    hidden=False,
    enabled=True,
    case_insensitive=True,
)
async def create_secret(
    ctx,
    country_role: discord.Role = commands.parameter(
        description="ID ou @ du rôle du pays"
    ),
    service_icon=commands.parameter(description="l'Emoji du drapeau du pays"),
    secret_name=commands.parameter(description="Nom du service secret sans espace."),
) -> None:
    secret_category = discord.utils.get(ctx.guild.categories, id=1269295981183369279)
    staff_role = ctx.guild.get_role(usefull_role_ids_dic["staff"])
    if not dUtils.is_authorized(ctx):
        return await ctx.send(embed=dUtils.get_auth_embed())
    secret_name = secret_name.replace("_", " ")
    secret_name = convert_country_name(secret_name)
    channel_name = f"「{service_icon}」{secret_name}"
    channel = await secret_category.create_text_channel(channel_name)
    await channel.set_permissions(
        ctx.guild.default_role,
        manage_webhooks=False,
        view_channel=False,
        read_messages=False,
        send_messages=False,
    )
    await channel.set_permissions(
        country_role,
        manage_webhooks=True,
        view_channel=True,
        read_messages=True,
        send_messages=True,
        manage_messages=True,
    )
    await channel.set_permissions(
        staff_role,
        manage_webhooks=True,
        view_channel=True,
        read_messages=True,
        send_messages=True,
        manage_messages=True,
    )
    await channel.send(
        f"Bienvenue dans les services {secret_name} du pays {country_role.name} !"
    )
    await ctx.send(f"Le service secret {secret_name} a été créé avec succès.")


def get_query_level(user_id):
    if user_id in bi_admins_id:
        return "admin"
    return "user"


@bot.command(
    name="brief_chat_til",
    brief="Résume la situation RP actuelle d'un salon (Staff uniquement).",
    usage="brief_chat_til <message>",
    description="Génère un résumé IA de la situation géopolitique dans un salon Discord.",
    help="""Utilise l'IA pour résumer la situation géopolitique actuelle dans un salon.

    FONCTIONNALITÉ :
    - Analyse les messages récents du salon spécifié
    - Génère un résumé intelligent avec l'IA Groq
    - Se concentre sur les aspects géopolitiques et RP
    - Fournit un contexte synthétique de la situation

    UTILISATION :
    - Mise à jour rapide sur une situation
    - Briefing pour nouveaux participants
    - Synthèse d'événements complexes
    - Support administratif pour le suivi RP

    RESTRICTIONS :
    - Réservé aux membres du staff uniquement
    - Nécessite l'accès aux API externes
    - Limité par la disponibilité de l'IA

    ARGUMENTS :
    - `<message>` : Message du salon à analyser pour le contexte

    EXEMPLE :
    - `brief_chat_til <ID_message>` : Résume la situation à partir de ce message
    """,
    hidden=False,
    enabled=True,
    case_insensitive=True,
)
async def brief_chat_til(
    ctx,
    user_message: discord.Message = commands.parameter(
        description="Message du salon à analyser pour générer le résumé"
    ),
):
    """Résumer la situation actuelle du RP dans un salon."""
    if not dUtils.is_authorized(ctx):
        return await ctx.send(embed=dUtils.get_auth_embed())

    # Récupérer le contexte du salon
    channel_context = await dUtils.get_channel_context(
        user_message.channel, user_message
    )

    # Construire le message pour Groq
    system_prompt = (
        "Tu es une IA spécialisée dans la synthèse d'informations géopolitiques. "
        "Tu dois résumer la situation actuelle du RP dans un salon Discord, en te basant sur les messages récents."
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages.append({"role": "user", "content": channel_context})

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=messages, model="llama-3.3-70b-versatile"
        )
        response = chat_completion.choices[0].message.content
        await dUtils.send_long_message(ctx, f"Résumé de la situation : {response}")
    except Exception as e:
        await user_message.channel.send(f"Erreur lors de la synthèse : {e}")


@bot.command(
    name="ask_rp_questions",
    brief="Pose une question IA sur la situation RP d'un salon (Staff uniquement).",
    usage="ask_rp_questions <question> <message>",
    description="Utilise l'IA pour répondre à une question spécifique sur la situation géopolitique.",
    help="""Pose une question spécifique à l'IA sur la situation géopolitique d'un salon.

    FONCTIONNALITÉ :
    - Analyse le contexte du salon spécifié
    - Répond à votre question avec l'IA Groq
    - Se base sur les messages récents pour le contexte
    - Fournit des réponses ciblées et pertinentes

    TYPES DE QUESTIONS POSSIBLES :
    - "Quels sont les principaux enjeux actuels ?"
    - "Qui sont les acteurs clés dans cette situation ?"
    - "Quelle est la position de [pays] ?"
    - "Y a-t-il des tensions diplomatiques ?"

    RESTRICTIONS :
    - Réservé aux membres du staff uniquement
    - Nécessite l'accès aux API externes
    - Qualité dépendante du contexte disponible

    ARGUMENTS :
    - `<question>` : Votre question sur la situation RP
    - `<message>` : Message du salon pour le contexte

    EXEMPLE :
    - `ask_rp_questions "Quelle est la situation militaire ?" <ID_message>`
    """,
    hidden=False,
    enabled=True,
    case_insensitive=True,
)
async def ask_rp_questions(
    ctx,
    question: str = commands.parameter(
        description="Question à poser sur la situation RP"
    ),
    user_message: discord.Message = commands.parameter(
        description="Message du salon pour fournir le contexte"
    ),
):
    """Résumer la situation actuelle du RP dans un salon."""
    if not dUtils.is_authorized(ctx):
        return await ctx.send(embed=dUtils.get_auth_embed())

    # Récupérer le contexte du salon
    channel_context = await dUtils.get_channel_context(
        user_message.channel, user_message
    )

    # Construire le message pour Groq
    system_prompt = (
        "Tu es une IA spécialisée dans la synthèse d'informations géopolitiques. "
        "Tu dois répondre à la question de l'utilisateur en te basant sur les messages qui te seront donnés."
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages.append({"role": "user", "content": channel_context})
    messages.append({"role": "user", "content": question})

    print(f"Question posée : {question}")
    print(f"Contexte du salon : {channel_context}")

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=messages, model="llama-3.3-70b-versatile"
        )
        response = chat_completion.choices[0].message.content
        await dUtils.send_long_message(
            ctx, f"Réponse à la question {question} : {response}"
        )
    except Exception as e:
        await user_message.channel.send(f"Erreur lors de la synthèse : {e}")


@bot.command(
    name="check_for_role_exclusive_overwrites",
    brief="Vérifie les permissions spécifiques d'un rôle (Staff uniquement).",
    usage="check_for_role_exclusive_overwrites <role>",
    description="Analyse les permissions spécifiques d'un rôle dans tous les salons du serveur.",
    help="""Vérifie où un rôle a des permissions spécifiquement définies dans le serveur.

    FONCTIONNALITÉ :
    - Scanne tous les salons du serveur
    - Identifie les permissions explicitement définies pour le rôle
    - Liste les salons avec des overrides de permissions
    - Aide au diagnostic des problèmes de permissions

    UTILISATION :
    - Audit de sécurité des permissions
    - Diagnostic de problèmes d'accès
    - Vérification de la configuration des rôles
    - Maintenance administrative

    INFORMATIONS AFFICHÉES :
    - Liste des salons avec permissions spécifiques
    - Indication des overrides existants
    - Récapitulatif des permissions personnalisées

    RESTRICTIONS :
    - Réservé aux membres du staff uniquement
    - Nécessite les permissions d'administration

    ARGUMENTS :
    - `<role>` : Rôle à analyser (mention ou nom)

    EXEMPLE :
    - `check_for_role_exclusive_overwrites @Moderateur`
    """,
    hidden=False,
    enabled=True,
    case_insensitive=True,
)
async def check_for_role_exclusive_overwrites(
    ctx,
    role: discord.Role = commands.parameter(
        description="Rôle dont vérifier les permissions spécifiques"
    ),
):
    """Vérifie si le rôle a des permissions définies dans des salons spécifiques."""
    if not dUtils.is_authorized(ctx):
        return await ctx.send(embed=dUtils.get_auth_embed())

    exclusive_overwrites = []

    for channel in ctx.guild.channels:
        overwrites = channel.overwrites_for(role)

        # Vérifie si au moins une permission est explicitement définie
        for perm_name in dir(overwrites):
            if perm_name.startswith("_"):
                continue  # ignore les attributs internes

            value = getattr(overwrites, perm_name)
            if isinstance(value, bool):  # Permission explicitement définie
                exclusive_overwrites.append(f"#{channel.name}")
                break  # On passe au canal suivant dès qu'une permission est définie

    if exclusive_overwrites:
        embed = discord.Embed(
            title=f"🔍 Permissions spécifiques pour le rôle {role.name}",
            description="\n".join(exclusive_overwrites),
            color=discord.Color.gold(),
        )
        print(
            f"Permissions spécifiques trouvées pour le rôle {role.name} dans les salons suivants : {', '.join(exclusive_overwrites)}"
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send(
            f"✅ Aucune permission spécifique définie pour le rôle {role.name}."
        )


@bot.command()
async def archive_rp_channels(ctx, archive_category: discord.CategoryChannel):
    """Archive les salons de RP en les déplaçant dans une catégorie d'archive."""
    if not dUtils.is_authorized(ctx):
        return await ctx.send(embed=dUtils.get_auth_embed())

    continents_dict["services"] = (
        1269295981183369279  # ID de la catégorie des services secrets
    )

    # Liste pour stocker tous les salons de RP à archiver
    rp_channels = []

    for category_id in continents_dict.values():
        category = bot.get_channel(category_id)
        if isinstance(category, discord.CategoryChannel):
            rp_channels.extend(category.text_channels)

    if not rp_channels:
        return await ctx.send(
            "Aucun salon de RP trouvé dans les catégories spécifiées."
        )

    for channel in rp_channels:
        try:
            await channel.edit(category=archive_category)
            print(f"Salon {channel.name} archivé dans {archive_category.name}.")
        except discord.Forbidden:
            print(f"Permission refusée pour archiver le salon {channel.name}.")
            await ctx.send(
                f"❌ Permission refusée pour archiver le salon {channel.name}."
            )
        except Exception as e:
            print(f"Erreur lors de l'archivage du salon {channel.name}: {e}")
            await ctx.send(
                f"❌ Erreur lors de l'archivage du salon {channel.name}: {e}"
            )

    await ctx.send("✅ Tous les salons de RP ont été archivés avec succès.")


async def transfer_messages_from_channel_to_channel(source_channel, target_channel):
    """Copie les messages d'un salon vers un autre en utilisant des embeds."""
    async for message in source_channel.history(limit=None, oldest_first=True):
        if message.author.bot:
            continue
        if (
            message.content.startswith(".")
            or message.content.startswith("!")
            or message.content.startswith("/")
        ):
            continue

        try:
            # Embed personnalisé pour le message
            embed = discord.Embed(
                description=message.clean_content,
                timestamp=message.created_at,
                color=discord.Color.blue(),
            )
            embed.set_author(
                name=f"{message.author.display_name}",
                icon_url=(
                    message.author.display_avatar.url
                    if message.author.display_avatar
                    else discord.Embed.Empty
                ),
            )
            embed.set_footer(text=f"Envoyé dans #{source_channel.name}")

            files = [await a.to_file() for a in message.attachments]

            # Si le message a déjà des embeds (envoyés par des bots par exemple), les copier aussi
            embeds_to_send = [embed]
            if message.embeds:
                for original_embed in message.embeds:
                    try:
                        # Discord ne permet pas de cloner exactement tous les embeds
                        # mais on peut les inclure tels quels s’ils sont simples
                        embeds_to_send.append(original_embed)
                    except Exception as e:
                        print(f"Erreur lors de la copie d’un embed existant : {e}")

            await target_channel.send(embeds=embeds_to_send, files=files)

        except discord.HTTPException as e:
            print(f"Erreur HTTP : {e}")
        except discord.Forbidden:
            print(f"Permission refusée dans {target_channel.name}")
            return False
    return True


@bot.command()
async def transfer_archives_to_category(ctx):
    """Copie les salons d'archives vers une autre catégorie (dans le même serveur ou un autre où le bot est)."""
    if not dUtils.is_authorized(ctx):
        return await ctx.send(embed=dUtils.get_auth_embed())
    archive_guild = bot.get_guild(1396923284498415807)

    archive_categories_id = [1231253371902623764, 1396920393939419156]

    archive_categories = [
        bot.get_channel(cat_id)
        for cat_id in archive_categories_id
        if isinstance(bot.get_channel(cat_id), discord.CategoryChannel)
    ]

    if not archive_categories:
        return await ctx.send("Aucune catégorie d'archives trouvée.")

    for category in archive_categories:
        new_category = await archive_guild.create_category(
            name=f"Archives de {category.name}",
            reason="Transfert des salons d'archives",
        )
        for channel in category.text_channels:
            try:
                new_channel = await archive_guild.create_text_channel(
                    name=channel.name,
                    category=new_category,
                    topic=f"Copie depuis {category.name}",
                )
                await ctx.send(f"📤 Transfert de #{channel.name} en cours...")
                await transfer_messages_from_channel_to_channel(channel, new_channel)
                await new_channel.send(f"✅ Fin du transfert depuis #{channel.name}")
                await asyncio.sleep(2)
            except discord.Forbidden:
                await ctx.send(
                    f"❌ Permission refusée pour copier le salon {channel.name}"
                )
            except Exception as e:
                await ctx.send(f"❌ Erreur pour le salon {channel.name}: {e}")


@bot.command()
async def get_units(ctx, country: CountryConverter = None, unit_type: str = "all"):
    """
    Commande pour obtenir le nombre d'unités d'un pays.

    Args:
        ctx (commands.Context): Le contexte de la commande.
        country (CountryConverter): Le pays dont on veut connaître le nombre d'unités.
        unit_type (str): Le type d'unité à vérifier (par défaut "soldier").

    Returns:
        None
    """

    if not country:
        country = CountryEntity(ctx.author, ctx.guild).to_dict()
    if unit_type.lower() not in unit_types.keys() and unit_type.lower() != "all":
        return await ctx.send(
            "Type d'unité invalide. Utilisez une de ces valeurs : "
            + ", ".join(unit_types.keys())
            + " ou 'all'."
        )

    is_country = db.get_players_country(ctx.author.id) == country.get("id")
    is_channel_secret = ctx.channel.id == int(
        db.get_country_secret_channel(country.get("id"))
    )

    title_str = f"Récupération des unités {'privées & publiques' if is_country and is_channel_secret else 'publiques'} pour {country.get('name')}"

    units = {}
    if unit_type.lower() == "all":
        for utype in unit_types.keys():
            if is_country and is_channel_secret:
                units[utype] = db.get_units(country.get("id"), unit_types.get(utype))
            units[f"public_{utype}"] = db.get_units(
                country.get("id"), f"public_{unit_types.get(utype)}"
            )
    else:
        if is_country and is_channel_secret:
            units[f"public_{unit_type.lower()}"] = db.get_units(
                country.get("id"), f"public_{unit_types.get(unit_type.lower())}"
            )
        units[unit_type.lower()] = db.get_units(
            country.get("id"), unit_types.get(unit_type.lower())
        )
    if not units:
        return await ctx.send("Aucune unité trouvée pour ce pays.")
    result_text = ""
    for utype, count in units.items():
        if count is not None:
            result_text += f"{utype.replace('public_', '(chiffre public) ')}: {count}\n"
    embed = discord.Embed(
        title=title_str, color=discord.Color.blue(), description=result_text
    )
    await ctx.send(embed=embed)


@bot.command()
async def recruit(
    ctx, country: CountryConverter, note: int, goal: int, unit_type: str = "None"
):
    """
    Commande pour recruter des membres dans le pays.

    Args:
        ctx (commands.Context): Le contexte de la commande.
        note (int): La note de recrutement.
        goal (int): L'objectif de recrutement.
        unit_type (str): Le type d'unité à recruter (par défaut "None").

    Returns:
        None
    """

    if not country.get("id"):
        return await ctx.send("Pays non trouvé.")
    if not dUtils.is_authorized(ctx):
        return await ctx.send(embed=dUtils.get_auth_embed())
    if unit_type.lower() not in unit_types.keys():
        return await ctx.send(
            "Type de recrutement invalide. Utilisez une de ces valeurs : "
            + ", ".join(unit_types.keys())
        )
    if note < 1 or note > 10:
        return await ctx.send("La note doit être entre 1 et 10.")
    if goal < 1:
        return await ctx.send("L'objectif doit être supérieur à 0.")
    recruited = int(goal * (note / 10) + random.randint(-goal // 4, goal // 10))
    if recruited < 0:
        recruited = 0
    if recruited > goal:
        recruited = goal
    if recruited > 1000:
        recruited = math.ceil(recruited / 10) * 10
    cost = db.get_pricings(unit_types.get(unit_type.lower())).get("price") * recruited
    await ctx.send(
        f"Vous avez recruté {recruited} {unit_type} pour votre pays avec une note de {note}/10 et un objectif de {goal}. \n\
Le coût total est de {convert(str(cost))}.\n\n"
    )
    confirmed = await dUtils.ask_confirmation(
        ctx,
        country.get("id"),
        f"Voulez-vous confirmer le recrutement de {recruited} {unit_type} pour {convert(str(cost))} ?",
    )
    if not confirmed:
        return
    if not db.has_enough_balance(country.get("id"), cost):
        return await ctx.send("Fonds insuffisants.")
    db.take_balance(country.get("id"), cost)
    confirmed = await dUtils.ask_confirmation(
        ctx,
        country.get("id"),
        f"Voulez-vous ajouter ces recrutements aux chiffres publics de votre pays ?",
    )
    db.add_units(country.get("id"), unit_types.get(unit_type.lower()), recruited)
    if confirmed:
        db.add_units(
            country.get("id"), f"public_{unit_types.get(unit_type.lower())}", recruited
        )
    return await ctx.send(
        f"Recrutement de {recruited} {unit_type} confirmé pour {convert(str(cost))}.\n"
    )


@bot.command()
async def set_public_units(ctx, country: CountryConverter, unit_type: str, qty: int):
    """
    Commande pour définir le nombre d'unités publiques d'un pays.

    Args:
        ctx (commands.Context): Le contexte de la commande.
        country (CountryConverter): Le pays dont on veut définir les unités publiques.
        unit_type (str): Le type d'unité à définir.
        qty (int): La quantité d'unités à définir.

    Returns:
        None
    """

    if not country.get("id"):
        return await ctx.send("Pays non trouvé.")
    if not dUtils.is_authorized(ctx):
        return await ctx.send(embed=dUtils.get_auth_embed())
    if unit_type.lower() not in unit_types.keys():
        return await ctx.send(
            "Type d'unité invalide. Utilisez une de ces valeurs : "
            + ", ".join(unit_types.keys())
        )
    if qty < 0:
        return await ctx.send("La quantité doit être supérieure ou égale à 0.")

    db.set_units(country.get("id"), f"public_{unit_types.get(unit_type.lower())}", qty)
    return await ctx.send(
        f"Les unités publiques de {country.get('name')} pour {unit_type} ont été définies à {qty}."
    )


@bot.command()
async def program_ghostping(
    ctx, target: Union[discord.Member, discord.Role], waiting: int = 5
):
    """
    Programme un ghost ping sur un membre ou un rôle.

    Args:
        ctx (commands.Context): Le contexte de la commande.
        target (Union[discord.Member, discord.Role]): Le membre ou le rôle à ghost pinger.
        waiting (int): Temps d'attente en secondes avant le ghost ping (par défaut 5).

    Returns:
        None
    """
    if not dUtils.is_authorized(ctx):
        return await ctx.send(embed=dUtils.get_auth_embed())

    await ctx.message.delete()  # Supprimer la commande pour éviter le spam
    message = await ctx.send(
        f"Ghost ping programmé pour {target.name} dans {waiting} secondes."
    )
    await asyncio.sleep(2)  # Laisser le temps à l'utilisateur de lire le message
    await message.delete()  # Supprimer le message de confirmation
    await asyncio.sleep(waiting)
    message = await ctx.send(f"{target.mention}")
    await asyncio.sleep(2)
    await message.delete()  # Supprimer le message de ghost ping


@bot.command()
async def test_converter(ctx, country: CountryConverter):
    """
    Teste le convertisseur de pays.

    Args:
        ctx (commands.Context): Le contexte de la commande.
        country (CountryConverter): Le pays à tester.

    Returns:
        None
    """
    if not country.get("id"):
        return await ctx.send("Pays non trouvé.")
    await ctx.send(f"Pays trouvé : {country.get('name')} (ID: {country.get('id')})")


class TechFormData:
    """Configuration data for different technology forms loaded from JSON"""

    @staticmethod
    def load_tech_configs():
        """Load tech configurations from JSON file."""
        import json

        try:
            with open("datas/tech_form_datas.json", "r", encoding="utf-8") as f:
                raw_configs = json.load(f)

            # Convert color strings to discord.Color objects
            configs = {}
            for tech_type, config in raw_configs.items():
                configs[tech_type] = {
                    "title": config["title"],
                    "color": getattr(discord.Color, config["color"])(),
                    "color_completed": getattr(
                        discord.Color, config["color_completed"]
                    )(),
                    "emoji": config["emoji"],
                    "forms": config["forms"],
                }
            return configs
        except FileNotFoundError:
            print("⚠️ tech_form_datas.json not found, using empty config")
            return {}
        except Exception as e:
            print(f"⚠️ Error loading tech_form_datas.json: {e}")
            return {}

    # Load configurations on class initialization
    TECH_CONFIGS = load_tech_configs()


class UniversalTechForm(discord.ui.Modal):
    """Universal modal form that adapts based on configuration."""

    def __init__(
        self, tech_type: str, form_index: int, form_data: dict, parent_view=None
    ):
        config = TechFormData.TECH_CONFIGS[tech_type]
        common_config = TechFormData.TECH_CONFIGS.get("common", {"forms": []})

        # Combine common fields first, then tech-specific fields
        all_forms = common_config["forms"] + config["forms"]

        # Auto-split forms into groups of 5
        forms_per_page = 5
        start_idx = form_index * forms_per_page
        end_idx = start_idx + forms_per_page
        current_forms = all_forms[start_idx:end_idx]

        title = f"{config['title']} - Partie {form_index + 1}"
        super().__init__(title=title, timeout=None)

        self.tech_type = tech_type
        self.form_index = form_index
        self.form_data = form_data
        self.parent_view = parent_view

        # Create TextInput fields following ConstructionForm pattern
        self.fields = []
        for field_config in current_forms:
            field = discord.ui.TextInput(
                label=field_config["label"],
                placeholder=field_config["placeholder"],
                max_length=300,
                style=discord.TextStyle.short,
                required=False,
            )
            setattr(self, f"field_{field_config['key']}", field)
            self.fields.append((field_config["key"], field))
            self.add_item(field)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission and update parent view."""
        # Collect field values
        for key, field in self.fields:
            self.form_data[key] = field.value

        # Mark this form as completed in parent view
        if self.parent_view:
            self.parent_view.mark_form_completed(self.form_index)

        embed = interaction.message.embeds[0] if interaction.message.embeds else None
        if not embed:
            embed = discord.Embed(
                title=f"✅ Formulaire {self.form_index + 1} complété",
                description="Données sauvegardées avec succès !",
                color=TechFormData.TECH_CONFIGS[self.tech_type]["color_completed"],
            )

        await interaction.response.edit_message(embed=embed, view=self.parent_view)

class MultiFormView(discord.ui.View):
    """Universal view that handles tech types with auto-splitting forms."""

    def __init__(self, tech_type: str, ctx: commands.Context, image_url: str):
        super().__init__(timeout=300)
        self.tech_type = tech_type
        self.config = TechFormData.TECH_CONFIGS[tech_type]
        self.common_config = TechFormData.TECH_CONFIGS.get("common", {"forms": []})
        self.form_data = {}
        self.ctx = ctx
        self.image_url = image_url

        # Calculate number of forms needed (auto-split by 5)
        # Include common fields + tech-specific fields
        total_fields = len(self.common_config["forms"]) + len(self.config["forms"])
        self.num_forms = (total_fields + 4) // 5  # Ceiling division
        self.completed_forms = set()

        # Create buttons in a single row
        for i in range(self.num_forms):
            button = discord.ui.Button(
                label=f"Formulaire {i + 1}",
                style=discord.ButtonStyle.green,
                custom_id=f"form_{i}",
                row=0,
            )

            # Create callback using closure
            def create_callback(form_index):
                async def button_callback(interaction):
                    await interaction.response.send_modal(
                        UniversalTechForm(
                            self.tech_type, form_index, self.form_data, self
                        )
                    )

                return button_callback

            button.callback = create_callback(i)
            self.add_item(button)

    def mark_form_completed(self, form_index: int):
        """Mark a form as completed and update button appearance."""
        self.completed_forms.add(form_index)

        # Update button to dark green and make unclickable
        for item in self.children:
            if hasattr(item, "custom_id") and item.custom_id == f"form_{form_index}":
                item.style = discord.ButtonStyle.secondary
                item.label = f"✅ Formulaire {form_index + 1}"
                item.disabled = True
                break

        if self.all_forms_completed():
            asyncio.create_task(
                self.send_summary()
            )  # Utiliser create_task car on n'est pas dans async


    def all_forms_completed(self) -> bool:
        """Check if all forms have been completed."""
        return len(self.completed_forms) == self.num_forms

    async def send_summary(self):
        summary_lines = [
            f"📦 **Résumé de la technologie `{self.config['title']}` :**\n"
        ]

        print(f"Form data collected: {self.form_data}")
        print(f"Sending to ctx: {self.ctx.message.channel.id}")

        # Combine common and tech-specific fields for summary
        all_fields = self.common_config["forms"] + self.config["forms"]

        for key, value in self.form_data.items():
            label = next((f["label"] for f in all_fields if f["key"] == key), key)
            summary_lines.append(f"• **{label}** : {value or '*Non renseigné*'}")

        embed = discord.Embed(
            title="🧪 Création terminée",
            description="\n".join(summary_lines),
            color=discord.Color.green(),
        )
        embed.set_image(url=self.image_url)

        await self.ctx.send(embed=embed)

    async def on_timeout(self):
        """Disable all buttons when view times out."""
        for item in self.children:
            item.disabled = True


@bot.command(
    name="test_multi_form",
    brief="Teste les formulaires multi-étapes pour les technologies.",
    usage="test_multi_form [tech_type]",
    description="POC pour tester les formulaires auto-divisés selon le type de technologie.",
    help="""Teste les formulaires multi-étapes pour différents types de technologies.

    FONCTIONNALITÉ :
    - Divise automatiquement les champs en groupes de 5 maximum
    - Chaque formulaire est adapté au type de technologie
    - Boutons en ligne unique avec couleurs progressives

    TYPES SUPPORTÉS :
    - `armes` : Armes à feu et équipements d'armement
    - `terrestre` : Véhicules et équipements terrestres
    - `navale` : Navires et équipements navals  
    - `aerienne` : Aéronefs et équipements aériens

    CHAMPS COMMUNS :
    - Nom de la technologie
    - Niveau technologique (1-20)
    - Technologie d'inspiration originelle

    ARGUMENTS :
    - `[tech_type]` : Optionnel. Type de technologie (armes/terrestre/navale/aerienne)

    EXEMPLE :
    - `test_multi_form` : Lance l'interface de sélection
    - `test_multi_form armes` : Lance directement le formulaire d'armes
    """,
    hidden=False,
    enabled=True,
    case_insensitive=True,
)
async def test_multi_form(
    ctx,
    tech_type: str = commands.parameter(
        default=None, description="Type de technologie (terrestre/navale/aerienne)"
    ),
    image_url: str = None,
) -> None:
    """Commande de test pour les formulaires multi-étapes selon le type de technologie."""
    if not tech_type:
        tech_type = await dUtils.discord_input(
            ctx,
            f"Bienvenue dans le programme de création de technologies!\nQuel type de technologie voulez-vous créer? ({'/'.join(TechFormData.TECH_CONFIGS.keys())})",
        )

    image_url_finale = None
    if ctx.message.attachments:
        image_url_finale = ctx.message.attachments[0].url
    elif image_url and image_url.startswith("http"):
        image_url_finale = image_url

    if not image_url_finale:
        await ctx.send(
            "Veuillez fournir une illustration pour la technologie (fichier ou lien)."
        )
        return

    tech_type = tech_type.lower()
    if tech_type not in TechFormData.TECH_CONFIGS.keys() or tech_type == "common":
        valid_types = [k for k in TechFormData.TECH_CONFIGS.keys() if k != "common"]
        await ctx.send("Veuillez répondre par " + ", ".join(valid_types) + ".")
        return

    # Get tech configuration
    config = TechFormData.TECH_CONFIGS[tech_type]
    common_config = TechFormData.TECH_CONFIGS.get("common", {"forms": []})

    # Calculate number of forms (including common fields)
    total_fields = len(common_config["forms"]) + len(config["forms"])
    num_forms = (total_fields + 4) // 5  # Ceiling division

    # Création de l'embed d'information
    embed = discord.Embed(
        title=f"{config['emoji']} Création de Technologie - {config['title']}",
        description=f"Formulaires auto-divisés pour votre **{config['title']}**.\n\n"
        f"**Champs communs:** {len(common_config['forms'])}\n"
        f"**Champs spécifiques:** {len(config['forms'])}\n"
        f"**Total de champs:** {total_fields}\n"
        f"**Formulaires générés:** {num_forms}\n\n"
        f"*Chaque formulaire contient jusqu'à 5 champs.*\n"
        f"*Les boutons deviennent verts foncés une fois complétés.*",
        color=config["color"],
    )

    embed.set_footer(text="💡 Remplissez tous les formulaires pour terminer la saisie!")

    await ctx.send(embed=embed, view=MultiFormView(tech_type, ctx, image_url_finale))

@bot.command(
    name="create_tech",
    brief="Crée une technologie avec un formulaire multi-étapes.",
    usage="create_tech [tech_type] [image_url]",
    description="Formulaire pour créer une technologie avec un formulaire auto-divisé selon le type de technologie.",
    help="""Crée une technologie avec un formulaire multi-étapes.
    FONCTIONNALITÉ :
    - Divise automatiquement les champs en groupes de 5 maximum
    - Chaque formulaire est adapté au type de technologie
    - Boutons en ligne unique avec couleurs progressives
    - Calcule le coût, le temps de recherche et permet à l'utilisateur de confirmer la création
    - Si confirmation donnée, enregistre la technologie dans la base de données
    """,
    hidden=False,
    enabled=True,
    case_insensitive=True,
)
async def create_tech(
    ctx,
    tech_type: str = commands.parameter(
        default=None, description="Type de technologie (terrestre/navale/aerienne)"
    ),
    image_url: str = None,
) -> None:
    """Commande de création pour les formulaires multi-étapes selon le type de technologie."""
    valid_types = [k for k in TechFormData.TECH_CONFIGS.keys() if k != "common"]
    if not tech_type:
        tech_type = await dUtils.discord_input(
            ctx,
            f"Bienvenue dans le programme de création de technologies!\nQuel type de technologie voulez-vous créer? ({'/'.join(valid_types)})",
        )

    image_url_finale = None
    if ctx.message.attachments:
        image_url_finale = ctx.message.attachments[0].url
    elif image_url and image_url.startswith("http"):
        image_url_finale = image_url

    if not image_url_finale:
        image_url_finale = await dUtils.discord_input(
            ctx,
            "Veuillez fournir une illustration pour la technologie (lien)."
        )
    if not image_url_finale or not image_url_finale.startswith("http"):
        await ctx.send(
            "Veuillez fournir une illustration valide pour la technologie (fichier ou lien)."
        )
        return

    tech_type = tech_type.lower()
    if tech_type not in TechFormData.TECH_CONFIGS.keys() or tech_type == "common":
        await ctx.send("Veuillez répondre par " + ", ".join(valid_types) + ".")
        return

    # Get tech configuration
    config = TechFormData.TECH_CONFIGS[tech_type]
    common_config = TechFormData.TECH_CONFIGS.get("common", {"forms": []})

    # Calculate number of forms (including common fields)
    total_fields = len(common_config["forms"]) + len(config["forms"])
    num_forms = (total_fields + 4) // 5  # Ceiling division

    # Création de l'embed d'information
    embed = discord.Embed(
        title=f"{config['emoji']} Création de Technologie - {config['title']}",
        description=f"Vous allez pouvoir créer une technologie de type **{config['title']}**.\n\n",
        color=config["color"],
    )

    embed.set_footer(text="💡 Remplissez tous les formulaires pour terminer la saisie!")

    await ctx.send(embed=embed, view=MultiFormView(tech_type, ctx, image_url_finale))

@bot.command()
async def annex(ctx, region_id):
    return


@bot.command()
async def add_player_to_country(ctx, user: discord.Member, country: CountryConverter):
    return


@bot.command()
async def remove_player_from_country(
    ctx, user: discord.Member, country: CountryConverter
):
    return


@bot.command()
async def add_region(
    ctx,
    region_name: str,
    map_name: str,
    population: int,
    country: CountryConverter = None,
):
    return


@bot.command()
async def remove_region(ctx, region_id: int):
    return


@bot.command()
async def set_region_data(ctx, region_id: int, key: str, value: str):
    return


bot.run(token)
