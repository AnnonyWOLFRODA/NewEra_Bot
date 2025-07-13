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
from discord.ext.commands import has_role
from discord.ext.commands import Context
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
from discord_utils import *
from text_formatting import *
from typing import Union
import interactions
from PIL import Image
import io
import string
import requests
from dotenv import dotenv_values
import math
import contextlib
from discord.ui import Button, View
from discord import message, emoji, Webhook, SyncWebhook
from removebg import RemoveBg
from context import *
from groq import Groq

Erreurs = {}
continents = []

token = dotenv_values(".env")["TOKEN"]
removebg_apikey = dotenv_values(".env")["REMOVEBG_API_KEY"]
groq_api_key = dotenv_values(".env")["GROQ_API_KEY"]
debug = False
embed_p = ""

intents = discord.Intents().all()
bot = commands.Bot(
    intents=intents,
    activity=discord.Game(name="Aider le staff!"),
    command_prefix=[".", "/"],
)
bi_admins_id = []
usefull_role_ids_dic = {}
groq_client = Groq(api_key=groq_api_key)
last_groq_query_time = datetime.now(timezone.utc)

rmbg = RemoveBg(removebg_apikey, "error.log")

duration_in_seconds = 0

starting_amounts = {}

continents_dict = {}

groq_chat_history = []
error_color_int = int("FF5733", 16)
money_color_int = int("FFF005", 16)
p_points_color_int = int("006AFF", 16)
d_points_color_int = int("8b1bd1", 16)
all_color_int = int("00FF44", 16)
factory_color_int = int("6E472E", 16)

code_list = []

# Usine = 0
# Terrestre = 1
# Aerienne = 2
# Maritime = 3
# Ecole = 4
bat_types = {}
query_types = {}

db = Database()
dUtils = discordUtils(bot)
# Créer une nouvelle connexion et table

with open("datas/usines.json") as f:
    production_data = json.load(f)

with open("datas/bases.json") as f:
    base_data = json.load(f)

with open("datas/main.json") as f:
    json_data = json.load(f)
    bat_types = json_data["bat_types"]
    query_types = json_data["query_types"]
    bi_admins_id = json_data["bi_admins_id"]
    Erreurs = json_data["Erreurs"]
    continents_dict = json_data["continents_dict"]
    code_list = json_data["code_list"]
    starting_amounts = json_data["starting_amounts"]
    usefull_role_ids_dic = json_data["usefull_role_ids_dic"]


@bot.event
async def on_message(message):
    if (
        isinstance(message.channel, discord.DMChannel)
        and message.author.id == 293869524091142144
        and message.content.startswith("!")
    ):
        await bot.get_channel(873645606214721536).send(message.content[1:])
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
        message.channel.id != 1122576341582221434
        and message.channel.category.id != 1269295981183369279
    ):
        return
    if (
        message.author == bot.user
        and reaction.emoji in ["🖋️", "🖊️"]
        and message.channel.id == 1122576341582221434
    ):
        await handle_treaty(reaction, user)
    elif reaction.emoji == "✅":
        await create_treaty(reaction, user)


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
    return await ctx.send(error)


wall_prices = {
    "béton": (60, 150),  # prix par m³
    "ossature métallique": (1000, 1000),  # prix par m²
}


async def get_player_role(ctx):
    return ctx.guild.get_role(873955562734362625)


async def get_non_player_role(ctx):
    return ctx.guild.get_role(873955513921048646)


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
async def construction_immeuble(ctx) -> None:
    if (
        await dUtils.discord_input(
            ctx,
            "Bienvenue dans le programme de construction d'immeubles!\nVoulez-vous construire un immeuble par nombre d'habitants ou par coût de construction? (habitants/coût)",
        )
        == "habitants"
    ):
        buildings, datas = await calculate_by_population(ctx)
    else:
        buildings, datas = await calculate_by_budget(ctx)

    await ctx.send("Enregistrement des données...")

    total_construction_cost = sum(
        building["construction_cost"] for building in buildings
    )
    total_logements = sum(building["nombre_logements"] for building in buildings)
    total_etages = sum(building["nombre_etages"] for building in buildings)
    total_habitants = sum(
        building["nombre_logements"] * building["people_per_apartment"]
        for building in buildings
    )

    await ctx.send("<a:loading:1259247395603222600> Calcul en cours...")
    answer = "\nBilan de la construction de l'immeuble:\n"

    for i, building in enumerate(buildings):
        logements_par_etage = building["nombre_logements"] // building["nombre_etages"]
        habitants_par_etage = logements_par_etage * building["people_per_apartment"]
        if len(answer) > 1800 and len(buildings) < 20:
            await ctx.send(answer)
            answer = ""
        answer += f"\n- Bâtiment {i + 1}:\n"
        answer += f"  - Coût de construction: {convert(str(building['construction_cost']))} €\n"
        answer += f"  - Nombre d'étages: {building['nombre_etages']}\n"
        answer += f"  - Logements par étage: {logements_par_etage}\n"
        answer += f"  - Habitants par étage: {habitants_par_etage}\n"
        answer += f"  - Nombre total de logements: {building['nombre_logements']}\n"
        answer += f"  - Nombre total d'habitants: {building['nombre_logements'] * building['people_per_apartment']}\n"
        answer += f"  - Surface totale: {building['surface']} m²\n"
        answer += f"  - Surface nette: {building['surface_net']} m²\n"
        answer += f"  - Surface habitable: {building['surface_habitable']} m²\n"
        answer += (
            f"  - Surface nette habitable: {building['surface_net_habitable']} m²\n"
        )
        answer += (
            f"  - Profondeur des fondations: {building['profondeur_fondation']} m\n"
        )

    if len(buildings) < 20:
        await dUtils.send_long_message(ctx, answer)
        answer = f"\n- **Bilan final:**\n  - Coût total de construction: {convert(str(total_construction_cost))} €\n"
    else:
        answer += f"\n- Coût total de construction: {convert(str(total_construction_cost))} €\n"
    answer += f"  - Nombre total d'étages: {total_etages}\n"
    answer += f"  - Nombre total de logements: {total_logements}\n"
    answer += f"  - Nombre total d'habitants: {total_habitants}\n"
    answer += f"  - Nombre moyen d'habitants par logement: {total_habitants / total_logements}\n"
    answer += f"  - Surface totale brute: {sum(building['surface'] for building in buildings)} m²\n"
    answer += f"  - Surface totale nette: {sum(building['surface_net'] for building in buildings)} m²\n"
    answer += f"  - Surface totale habitable: {sum(building['surface_habitable'] for building in buildings)} m²\n"
    answer += f"  - Surface totale nette habitable: {sum(building['surface_net_habitable'] for building in buildings)} m²\n"
    answer += f"  - Moyenne du nombre d'étages par bâtiment: {total_etages / len(buildings)}\n"
    answer += f"  - Nombre total de bâtiments: {len(buildings)}"

    answer += f"\n- Paramètres utilisés:\n"
    answer += f"  - Taille moyenne des appartements: {datas['taille_moyenne']} m²\n"
    answer += f"  - Prix moyen du mètre carré: {datas['prix_moyen']} €\n"
    answer += f"  - Type de murs: {datas['type_murs']}\n"
    answer += f"  - Nombre maximum d'étages: {datas['max_etages']}\n"
    answer += f"  - Nombre maximum de logements par étage: {datas['max_apartments']}\n"
    answer += (
        f"  - Nombre moyen d'habitants par logement: {datas['people_per_apartment']}\n"
    )
    if datas["objectif_type"] == "habitants":
        answer += (
            f"  - Objectif de nombre d'habitants: {convert(str(datas['objectif']))}\n"
        )
        answer += f"  - Dépassement de l'objectif: {total_habitants - datas['objectif']} habitants\n"
    else:
        answer += f"  - Objectif de coût de construction: {convert(str(datas['objectif']))} €\n"
        answer += f"  - Dépassement de l'objectif: {total_construction_cost - datas['objectif']} €\n"
    if len(buildings) < 20:
        await dUtils.send_long_message(ctx, answer)
    else:
        with open("construction_immeuble.txt", "w") as f:
            f.write(answer)
        await ctx.send(file=discord.File("construction_immeuble.txt"))
        os.remove("construction_immeuble.txt")


async def calculate_by_population(ctx):
    """
    Asynchronously calculates the number of buildings required to meet a population objective based on user inputs.
    Args:
        ctx: The context in which the command was invoked.
    Returns:
        A tuple containing:
            - A list of dictionaries, each representing a building with the following keys:
                - 'nombre_etages': Number of floors in the building.
                - 'nombre_logements': Number of apartments in the building.
                - 'people_per_apartment': Number of people per apartment.
                - 'surface': Total surface area of the building.
                - 'surface_net': Net surface area per floor.
                - 'surface_habitable': Habitable surface area of the building.
                - 'surface_net_habitable': Net habitable surface area per floor.
                - 'construction_cost': Total construction cost of the building.
                - 'profondeur_fondation': Depth of the foundation.
            - A dictionary containing the input data used for the calculations.
    """
    datas = {
        "taille_moyenne": 40,
        "prix_moyen": 1500,
        "type_murs": "béton",
        "max_etages": 10,
        "max_apartments": 30,
        "people_per_apartment": 4,
        "objectif": 0,
        "objectif_type": "habitants",
        "prix_fondations": 50,
    }
    datas["objectif"] = int(
        await dUtils.discord_input(ctx, "Entrez l'objectif de nombre d'habitants : ")
    )
    datas["max_etages"] = int(
        await dUtils.discord_input(
            ctx,
            f"Entrez le nombre maximum d'étages (par défaut: {datas['max_etages']}): ",
        )
        or datas["max_etages"]
    )
    datas["max_apartments"] = int(
        await dUtils.discord_input(
            ctx,
            f"Entrez le nombre maximum de logements par étage (par défaut: {datas['max_apartments']}): ",
        )
        or datas["max_apartments"]
    )
    datas["people_per_apartment"] = get_people_per_apartment(datas["taille_moyenne"])
    datas["prix_moyen"] = int(
        await dUtils.discord_input(
            ctx,
            f"Entrez le prix moyen du mètre carré (par défaut: {datas['prix_moyen']}): ",
        )
        or datas["prix_moyen"]
    )

    buildings = []
    current_building = {
        "nombre_etages": 1,
        "nombre_logements": 1,
        "people_per_apartment": datas["people_per_apartment"],
        "surface": 0,
        "surface_net": 0,
        "surface_habitable": 0,
        "surface_net_habitable": 0,
        "construction_cost": 0,
        "profondeur_fondation": 3,
    }
    actual_stage_logements = 0

    while True:
        ctx.author.send(
            f"Calcul en cours... ({current_building['nombre_logements']} logements)"
        )
        total_area = calculate_total_area(
            datas["taille_moyenne"], current_building["nombre_logements"]
        )
        current_building["surface"] = total_area
        current_building["surface_net"] = round(
            total_area / current_building["nombre_etages"]
        )
        construction_cost = calculate_construction_cost(
            datas, total_area, current_building
        )
        current_building["construction_cost"] = construction_cost
        current_building["surface_habitable"] = total_area - (total_area * 0.1)
        current_building["surface_net_habitable"] = round(
            current_building["surface_habitable"] / current_building["nombre_etages"]
        )
        current_building["profondeur_fondation"] = current_building["nombre_etages"] + 1

        if (
            sum(
                building["nombre_logements"] * building["people_per_apartment"]
                for building in buildings + [current_building]
            )
            >= datas["objectif"]
        ):
            buildings.append(current_building)
            break

        current_building["nombre_logements"] += 1
        actual_stage_logements += 1
        if actual_stage_logements >= datas["max_apartments"]:
            if current_building["nombre_etages"] < datas["max_etages"]:
                current_building["nombre_etages"] += 1
                actual_stage_logements = 0
            else:
                buildings.append(current_building)
                current_building = {
                    "nombre_etages": 1,
                    "nombre_logements": 1,
                    "people_per_apartment": datas["people_per_apartment"],
                    "surface": 0,
                    "surface_net": 0,
                    "surface_habitable": 0,
                    "surface_net_habitable": 0,
                    "construction_cost": 0,
                    "profondeur_fondation": 3,
                }

    return buildings, datas


async def calculate_by_budget(ctx):
    """
    Asynchronously calculates the number of buildings that can be constructed within a given budget.
    Parameters:
        ctx (Context): The context in which the command was invoked.
    Returns:
        tuple: A tuple containing:
            - buildings (list): A list of dictionaries, each representing a building with the following keys:
                - nombre_etages (int): Number of floors in the building.
                - nombre_logements (int): Number of apartments in the building.
                - people_per_apartment (int): Number of people per apartment.
                - surface (float): Total surface area of the building.
                - surface_net (float): Net surface area per floor.
                - surface_habitable (float): Habitable surface area of the building.
                - surface_net_habitable (float): Net habitable surface area per floor.
                - construction_cost (float): Total construction cost of the building.
                - profondeur_fondation (int): Depth of the foundation.
            - datas (dict): A dictionary containing the input data and calculated values.
    """
    datas = {
        "taille_moyenne": 40,
        "prix_moyen": 1500,
        "type_murs": "béton",
        "max_etages": 10,
        "max_apartments": 30,
        "people_per_apartment": 4,
        "objectif": 0,
        "objectif_type": "budget",
        "prix_fondations": 50,
    }
    datas["objectif"] = int(
        await dUtils.discord_input(ctx, "Entrez l'objectif de prix : ")
    )
    datas["max_etages"] = int(
        await dUtils.discord_input(
            ctx,
            f"Entrez le nombre maximum d'étages (par défaut: {datas['max_etages']}): ",
        )
        or datas["max_etages"]
    )
    datas["max_apartments"] = int(
        await dUtils.discord_input(
            ctx,
            f"Entrez le nombre maximum de logements par étage (par défaut: {datas['max_apartments']}): ",
        )
        or datas["max_apartments"]
    )
    datas["people_per_apartment"] = get_people_per_apartment(datas["taille_moyenne"])

    buildings = []
    current_building = {
        "nombre_etages": 1,
        "nombre_logements": 1,
        "people_per_apartment": datas["people_per_apartment"],
        "surface": 0,
        "surface_net": 0,
        "surface_habitable": 0,
        "surface_net_habitable": 0,
        "construction_cost": 0,
        "profondeur_fondation": 3,
    }
    actual_stage_logements = 0
    while True:
        total_area = calculate_total_area(
            datas["taille_moyenne"], current_building["nombre_logements"]
        )
        current_building["surface"] = total_area
        current_building["surface_net"] = round(
            total_area / current_building["nombre_etages"]
        )
        construction_cost = calculate_construction_cost(
            datas, total_area, current_building
        )
        current_building["construction_cost"] = construction_cost
        current_building["surface_habitable"] = total_area - (total_area * 0.1)
        current_building["surface_net_habitable"] = round(
            current_building["surface_habitable"] / current_building["nombre_etages"]
        )
        current_building["profondeur_fondation"] = current_building["nombre_etages"] + 1

        if (
            sum(
                building["construction_cost"]
                for building in buildings + [current_building]
            )
            >= datas["objectif"]
        ):
            buildings.append(current_building)
            break

        current_building["nombre_logements"] += 1
        actual_stage_logements += 1
        if actual_stage_logements >= datas["max_apartments"]:
            if current_building["nombre_etages"] < datas["max_etages"]:
                current_building["nombre_etages"] += 1
                actual_stage_logements = 0
            else:
                buildings.append(current_building)
                current_building = {
                    "nombre_etages": 1,
                    "nombre_logements": 1,
                    "people_per_apartment": datas["people_per_apartment"],
                    "surface": 0,
                    "surface_net": 0,
                    "surface_habitable": 0,
                    "surface_net_habitable": 0,
                    "construction_cost": 0,
                    "profondeur_fondation": 3,
                }
    return buildings, datas


## Eco


@bot.command()
async def give(ctx, user: discord.Member, amount: Union[int, str]):

    author = ctx.author

    sender_balance = db.get_balance(author.id)
    if sender_balance is None:
        sender_balance = 0

    if not amount_converter(amount, sender_balance):
        embed = discord.Embed(
            title="Erreur de donation",
            description=":moneybag: Le montant spécifié est invalide.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    payment_amount = amount_converter(amount, sender_balance)

    if not db.has_enough_balance(author.id, payment_amount):
        print(sender_balance, payment_amount)
        embed = discord.Embed(
            title="Erreur de donation",
            description=f":moneybag: L'utilisateur {ctx.author.mention} n'a pas assez d'argent.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    recipient_balance = db.get_balance(user.id)
    if recipient_balance is None:
        recipient_balance = 0

    db.give_balance(user.id, payment_amount)
    db.take_balance(author.id, payment_amount)
    transa_embed = discord.Embed(
        title="Opération réussie",
        description=f":moneybag: **{convert(str(payment_amount))}** ont été donnés à l'utilisateur {user.mention}.",
        color=money_color_int,
    )

    await eco_logger("M1", payment_amount, ctx.author, user)
    await ctx.send(embed=transa_embed)


@bot.command()
async def remove_money(ctx, user: discord.Member, amount: Union[int, str]):
    if not dUtils.is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    balance = db.get_balance(user.id)
    if balance is None:
        balance = 0

    if not amount_converter(amount, balance):
        embed = discord.Embed(
            title="Erreur de retrait d'argent",
            description=":moneybag: Le montant spécifié est invalide.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    payment_amount = amount_converter(amount, balance)
    if not db.has_enough_balance(user.id, payment_amount):
        embed = discord.Embed(
            title="Erreur de retrait d'argent",
            description=f":moneybag: L'utilisateur {user.name} n'a pas assez d'argent.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return
    db.take_balance(user.id, payment_amount)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":moneybag: **{convert(str(payment_amount))}** ont été retirés de la réserve d'argent de l'utilisateur {user.name}.",
        color=money_color_int,
    )
    await eco_logger("M5", payment_amount, user, ctx.author)
    await ctx.send(embed=embed)


@bot.command()
async def remove_pp(ctx, user: discord.Member, amount: Union[int, str]):
    if not dUtils.is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    points = db.get_points(user.id, 1)
    if not amount_converter(amount, points):
        embed = discord.Embed(
            title="Erreur de retrait de points",
            description=":blue_circle: Le montant spécifié est invalide.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    payment_amount = amount_converter(amount, points)

    if not db.has_enough_points(user.id, payment_amount, 1):
        embed = discord.Embed(
            title="Erreur de retrait de points",
            description=f":blue_circle: L'utilisateur {user.name} n'a pas assez de points.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    db.take_points(user.id, payment_amount, 1)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":blue_circle: **{payment_amount}** ont été retirés des points de l'utilisateur {user.name}.",
        color=p_points_color_int,
    )
    await eco_logger("P4", payment_amount, user, ctx.author, 1)
    await ctx.send(embed=embed)


@bot.command()
async def remove_pd(ctx, user: discord.Member, amount: Union[int, str]):
    if not dUtils.is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    points = db.get_points(user.id, 2)
    if not amount_converter(amount, points):
        embed = discord.Embed(
            title="Erreur de retrait de points",
            description=":purple_circle: Le montant spécifié est invalide.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    payment_amount = amount_converter(amount, points)

    if not db.has_enough_points(user.id, payment_amount, 2):
        embed = discord.Embed(
            title="Erreur de retrait de points",
            description=f":purple_circle: L'utilisateur {user.name} n'a pas assez de points.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    db.take_points(user.id, payment_amount, 2)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":purple_circle: **{payment_amount}** ont été retirés des points de l'utilisateur {user.name}.",
        color=d_points_color_int,
    )
    await eco_logger("P4", payment_amount, user, ctx.author, 2)
    await ctx.send(embed=embed)


@bot.command()
async def bal(ctx, user: discord.Member = None):
    if user is None:
        user = ctx.author
    balance = db.get_balance(str(user.id))
    if balance == 0:
        embed = discord.Embed(
            title=":moneybag: Cet utilisateur n'a pas d'argent", color=money_color_int
        )
    else:
        embed = discord.Embed(
            title=f"Balance de {user.name}",
            description=f":moneybag: L'utilisateur {user.name} a **{convert(str(balance))} d'argent**.",
            color=money_color_int,
        )
        embed.set_footer(text=f"Classement: {db.get_leads(1, user.id)}")
    await ctx.send(embed=embed)


@bot.command()
async def points_p(ctx, user: discord.Member = None):
    if user is None:
        user = ctx.author
    balance = db.get_points(str(user.id), 1)
    if balance == 0:
        embed = discord.Embed(
            title=":blue_circle: Cet utilisateur n'a pas de points politiques.",
            color=p_points_color_int,
        )
    else:
        embed = discord.Embed(
            title=f"Nombre de points politiques de {user.name}",
            description=f":blue_circle: L'utilisateur {user.name} a **{balance} points politiques**.",
            color=p_points_color_int,
        )
        embed.set_footer(text=f"Classement: {db.get_leads(2, user.id)}")
    await ctx.send(embed=embed)


@bot.command()
async def points_d(ctx, user: discord.Member = None):
    if user is None:
        user = ctx.author
    balance = db.get_points(str(user.id), 2)
    if balance == 0:
        embed = discord.Embed(
            title=":purple_circle: Cet utilisateur n'a pas de points diplomatiques.",
            color=d_points_color_int,
        )
    else:
        embed = discord.Embed(
            title=f"Nombre de points diplomatiques de {user.name}",
            description=f":purple_circle: L'utilisateur {user.name} a **{balance} points diplomatiques**.",
            color=d_points_color_int,
        )
        embed.set_footer(text=f"Classement: {db.get_leads(3, user.id)}")
    await ctx.send(embed=embed)


@bot.command()
async def set_money(ctx, user: discord.Member, amount: int):
    if not dUtils.is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    db.set_balance(str(user.id), amount)

    embed = discord.Embed(
        title="Opération réussie",
        description=f":moneybag: **{convert(str(amount))}** dollars ont été définis pour l'utilisateur {user.name}.",
        color=money_color_int,
    )
    await eco_logger("M3", amount, user, ctx.author)
    await ctx.send(embed=embed)


@bot.command()
async def set_pp(ctx, user: discord.Member, amount: int):
    if not dUtils.is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    db.set_points(str(user.id), amount, 1)

    embed = discord.Embed(
        title="Opération réussie",
        description=f":blue_circle: **{amount}** points politiques ont été définis pour l'utilisateur {user.name}.",
        color=p_points_color_int,
    )
    await eco_logger("P2", amount, user, ctx.author, 1)
    await ctx.send(embed=embed)


@bot.command()
async def set_pd(ctx, user: discord.Member, amount: int):
    if not dUtils.is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    db.set_points(str(user.id), amount, 2)

    embed = discord.Embed(
        title="Opération réussie",
        description=f":purple_circle: **{amount}** points diplomatiques ont été définis pour l'utilisateur {user.name}.",
        color=d_points_color_int,
    )
    await eco_logger("P2", amount, user, ctx.author, 2)
    await ctx.send(embed=embed)


@bot.command()
async def add_money(ctx, user: discord.Member, amount: int):
    if not dUtils.is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    db.give_balance(str(user.id), amount)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":moneybag: **{convert(str(amount))}** ont été ajoutés à l'utilisateur {user.name}.",
        color=money_color_int,
    )
    await eco_logger("M2", amount, user, ctx.author)
    await ctx.send(embed=embed)


@bot.command()
async def add_pp(ctx, user: discord.Member, amount: int):
    if not dUtils.is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    db.give_points(str(user.id), amount, 1)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":blue_circle: **{amount}** ont été ajoutés à l'utilisateur {user.name}.",
        color=p_points_color_int,
    )
    await eco_logger("P1", amount, user, ctx.author, 1)
    await ctx.send(embed=embed)


@bot.command()
async def add_pd(ctx, user: discord.Member, amount: int):
    if not dUtils.is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    db.give_points(str(user.id), amount, 2)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":purple_circle: **{amount}** ont été ajoutés à l'utilisateur {user.name}.",
        color=d_points_color_int,
    )
    await eco_logger("P1", amount, user, ctx.author, 2)
    await ctx.send(embed=embed)


@bot.command()
async def pay(ctx, amount: Union[int, str]):
    user = ctx.author
    balance = db.get_balance(str(user.id))

    if not amount_converter(amount, balance):
        embed = discord.Embed(
            title="Erreur de retrait d'argent",
            description=":moneybag: Le montant spécifié est invalide.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    payment_amount = amount_converter(amount, balance)

    if not db.has_enough_balance(user.id, payment_amount):
        embed = discord.Embed(
            title="Erreur de paiement",
            description=f":moneybag: Vous n'avez pas assez d'argent pour effectuer cette transaction.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    db.take_balance(user.id, payment_amount)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":moneybag: **{convert(str(payment_amount))}** ont été payés au bot.",
        color=money_color_int,
    )
    await eco_logger("M4", payment_amount, ctx.author)
    await ctx.send(embed=embed)


@bot.command()
async def use_pp(ctx, amount: int = 1):
    user = ctx.author
    points = db.get_points(user.id, 1)
    if not amount_converter(amount, points):
        embed = discord.Embed(
            title="Erreur d'utilisation des points",
            description=":blue_circle: Le montant spécifié est invalide.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    payment_amount = amount_converter(amount, points)

    if not db.has_enough_points(user.id, amount, 1):
        embed = discord.Embed(
            title="Erreur d'utilisation des points",
            description=f":blue_circle: L'utilisateur {ctx.author.mention} n'a pas assez de points politiques.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return
    db.take_points(user.id, payment_amount, 1)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":blue_circle: **{amount}** points politiques ont été utilisés par {user.name}.",
        color=p_points_color_int,
    )
    await eco_logger("P3", amount, ctx.author, None, 1)
    await ctx.send(embed=embed)


@bot.command()
async def use_pd(ctx, amount: int = 1):
    user = ctx.author
    points = db.get_points(user.id, 2)
    if not amount_converter(amount, points):
        embed = discord.Embed(
            title="Erreur d'utilisation des points",
            description=":purple_circle: Le montant spécifié est invalide.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    payment_amount = amount_converter(amount, points)

    if not db.has_enough_points(user.id, amount, 2):
        embed = discord.Embed(
            title="Erreur d'utilisation des points",
            description=f":purple_circle: L'utilisateur {ctx.author.mention} n'a pas assez de points diplomatiques.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return
    db.take_points(user.id, payment_amount, 2)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":purple_circle: **{amount}** points diplomatiques ont été utilisés par {user.name}.",
        color=d_points_color_int,
    )
    await eco_logger("P3", amount, ctx.author, None, 2)
    await ctx.send(embed=embed)


@bot.command()
async def lead(ctx):
    async def create_lead_embed(leaderboard, offset):
        embed = discord.Embed(
            title=f"Classement des pays (de {offset + 1} à {offset + len(leaderboard)})",
            color=0x00FF00,
        )
        for i, (user_id, balance, pp, pd) in enumerate(leaderboard, offset + 1):
            user = ctx.guild.get_member(int(user_id))
            if user:
                username = user.name + f" - {str(user_id)}"
            else:
                username = str(user_id) + " - Non identifié"
            embed.add_field(
                name=f"{i}. {username}",
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


class EcoLogEvent:
    def __init__(self, code, amount, user1, user2=None, type=1):
        self.code = code
        self.amount = convert(str(amount)) if len(str(amount)) > 3 else amount
        self.user1 = user1
        self.user2 = user2
        self.type = type

    def is_valid_code(self):
        return self.code in code_list

    def get_embed(self):
        if self.code.startswith("M"):
            return self._money_embed()
        elif self.code.startswith("P"):
            return self._points_embed()
        return None

    def _money_embed(self):
        templates = {
            "M1": (
                "Nouvelle transaction entre joueurs",
                ":moneybag: L'utilisateur {u1} a donné {amt} à {u2}.",
            ),
            "M2": (
                "<a:NE_Alert:1261090848024690709> Ajout d'argent",
                ":moneybag: {u1} s'est fait ajouter {amt} par {u2}.",
            ),
            "M3": (
                "<a:NE_Alert:1261090848024690709> Argent défini",
                ":moneybag: {u1} s'est fait définir son argent à {amt} par {u2}.",
            ),
            "M4": ("Argent payé", ":moneybag: {u1} a payé {amt} à la banque."),
            "M5": (
                "<a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> Retrait d'argent",
                ":moneybag: {u1} s'est fait retirer {amt} par {u2}.",
            ),
            "MR": (
                "<a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> Reset de l'économie",
                ":moneybag: {u1} a réinitialisé l'économie.",
            ),
            "MRR": (
                "<a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> Tentative de reset",
                ":moneybag: {u1} a tenté de réinitialiser l'économie.",
            ),
        }

        title, desc_template = templates.get(self.code, (None, None))
        if not title:
            return None

        desc = desc_template.format(
            u1=f"{self.user1.name} ({self.user1.id})",
            u2=f"{self.user2.name} ({self.user2.id})" if self.user2 else "❓",
            amt=self.amount,
        )
        return discord.Embed(title=title, description=desc, color=money_color_int)

    def _points_embed(self):
        p_type = "Points politiques" if self.type == 1 else "Points diplomatiques"
        color = p_points_color_int if self.type == 1 else d_points_color_int

        templates = {
            "P1": (
                f"<a:NE_Alert:1261090848024690709> {p_type} ajoutés",
                ":blue_circle: {u1} s'est fait ajouter {amt} {p_type} par {u2}.",
            ),
            "P2": (
                f"<a:NE_Alert:1261090848024690709> {p_type} définis",
                ":blue_circle: {u1} s'est fait définir ses {p_type} à {amt} par {u2}.",
            ),
            "P3": (f"{p_type} utilisé", ":blue_circle: {u1} a utilisé {amt} {p_type}."),
            "P4": (
                f"<a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> {p_type} retirés",
                ":blue_circle: {u1} s'est fait retirer {amt} {p_type} par {u2}.",
            ),
            "PR": (
                f"<a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> Reset des {p_type}",
                ":blue_circle: {u1} a réinitialisé les {p_type}.",
            ),
            "PRR": (
                f"<a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> Tentative de reset",
                ":blue_circle: {u1} a tenté de réinitialiser les {p_type}.",
            ),
        }

        title, desc_template = templates.get(self.code, (None, None))
        if not title:
            return None

        desc = desc_template.format(
            u1=f"{self.user1.name} ({self.user1.id})",
            u2=f"{self.user2.name} ({self.user2.id})" if self.user2 else "❓",
            amt=self.amount,
            p_type=p_type,
        )
        return discord.Embed(title=title, description=desc, color=color)

async def eco_logger(code, amount, user1, user2=None, type=1):
    log_channel = bot.get_channel(1261064715480862866)
    event = EcoLogEvent(code, amount, user1, user2, type)

    if not event.is_valid_code():
        print("Erreur de code : Le code donné n'est pas bon.")
        return

    embed = event.get_embed()
    if embed:
        await log_channel.send(embed=embed)
    else:
        print("Code non reconnu dans les mappings.")

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


@bot.command()
async def execute_cmd(ctx, *, code: str):
    if ctx.author.id != 293869524091142144:
        await ctx.reply("You do not have the required role to use this command.")
        return
    try:
        # Créer un tampon pour capturer la sortie
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            # Exécuter le code fourni
            exec(code)
        output = buffer.getvalue()

        if not output:
            output = "L'exécution s'est terminée sans produire de sortie."

        if len(output) > 2000:
            await ctx.send(
                "Le résultat est trop long, voici le fichier contenant l'output :",
                file=discord.File(io.StringIO(output), filename="output.txt"),
            )
        else:
            await ctx.send(f"**Résultat de l'exécution :**\n```python\n{output}\n```")

    except Exception as e:
        await ctx.send(
            f"**Une erreur est survenue lors de l'exécution du code :**\n```python\n{e}\n```"
        )

##

@bot.command(
    name="construct_usine",
    brief="Construit un certain nombre d'usines d'un niveau spécifié.",
    usage="construct_usine <amount> <lvl>",
    description="Construit plusieurs usines du niveau indiqué et débite le coût correspondant.",
    help="""Construit une ou plusieurs usines en fonction de la quantité et du niveau indiqués, tout en vérifiant le solde de l'utilisateur.

    ARGUMENTS :
    - `<amount>` : Nombre d'usines à construire (entier).
    - `<lvl>` : Niveau des usines à construire (entier ou chaîne représentative du niveau).

    EXEMPLE :
    - `construct_usine 3 1` : Construit 3 usines de niveau 1 si l'utilisateur a suffisamment de fonds pour couvrir le coût.
    """,
    hidden=False,
    enabled=True,
    case_insensitive=True,
)
async def construct_usine(
    ctx,
    amount: int = commands.parameter(
        description="Nombre d'usines à construire (doit être un entier positif)."
    ),
    lvl=commands.parameter(
        description="Niveau des usines à construire (indique le coût de construction par usine)."
    ),
) -> None:
    user = ctx.author
    balance = db.get_balance(str(user.id))

    if not amount_converter(amount, balance):
        embed = discord.Embed(
            title="Erreur de paiement",
            description=":moneybag: Le montant spécifié est invalide.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    payment_amount = amount * int(production_data[str(lvl)]["cout_construction"])

    if not db.has_enough_balance(user.id, payment_amount):
        embed = discord.Embed(
            title="Erreur de paiement",
            description=f":moneybag: Vous n'avez pas assez d'argent pour effectuer cette transaction.\nMontant demandé : {payment_amount}. | Vous possédez : {balance}",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    db.take_balance(user.id, payment_amount)
    db.give_usine(user.id, amount, lvl, 0)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":factory: Vos {amount} usines de niveau {lvl} auront coûtés **{convert(str(payment_amount))}** et ont été payés au bot.",
        color=money_color_int,
    )
    await ctx.send(embed=embed)


@bot.command()
async def sell_batiment(ctx, bat_type, amount: int, lvl):
    user = ctx.author
    balance = db.get_usine(user.id, lvl, 0)
    if balance is None:
        balance = 0

    if not amount_converter(amount, balance):
        embed = discord.Embed(
            title="Erreur de retrait d'usine",
            description=":factory: Le montant spécifié est invalide.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return
    payment_amount = amount * int(production_data[str(lvl)]["cout_construction"])

    if not db.has_enough_bats(user.id, amount, lvl, 0):
        embed = discord.Embed(
            title="Erreur de paiement",
            description=f":factory: Vous n'avez pas assez d'usines pour effectuer cette transaction.\nMontant demandé : {amount}. | Vous possédez : {balance}",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    db.give_balance(user.id, payment_amount)
    db.remove_usine(user.id, amount, lvl, 0)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":factory: Vos {amount} usines de niveau {lvl} vous ont rapporté **{convert(str(payment_amount))}** et ont été ajouté à votre solde.",
        color=money_color_int,
    )
    await ctx.send(embed=embed)


@bot.command()
async def usines(ctx, type, user: discord.Member = None):
    if user is None:
        user = ctx.author
    types = [1, 2, 3, 4, 5, 6, 7]
    if (type.lower() != "all") and (int(type) not in types):
        return await ctx.send("Lol non")
    if type.lower() == "all":
        embed = discord.Embed(title=f"Usines de {user.name}", description="")
        for i in types:
            current_us = db.get_usine(user.id, i, 0)
            embed.description += f"Type {i} : {current_us}\n"
    else:
        type = int(type)
        embed = discord.Embed(
            title=f"Usines de type {type} de {user.name}",
            description=f"L'utilisateur a **{str(db.get_usine(user.id, type, 0))}** usines de type {type}.",
        )
    await ctx.send(embed=embed)

@bot.command()
async def remove_usine(ctx, user: discord.Member, amount: Union[int, str], lvl: int):
    if not dUtils.is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    balance = db.get_usine(user.id, lvl, 0)
    if balance is None:
        balance = 0

    if not amount_converter(amount, balance):
        embed = discord.Embed(
            title="Erreur de retrait d'usine",
            description=":factory: Le montant spécifié est invalide.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    payment_amount = amount_converter(amount, balance)
    if not db.has_enough_balance(user.id, payment_amount):
        embed = discord.Embed(
            title="Erreur de retrait d'argent",
            description=f":factory: L'utilisateur {user.name} n'a pas assez d'usines.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return
    db.remove_usine(user.id, amount, lvl, 0)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":factory: **{convert(str(payment_amount))}** ont été retirés de l'inventaire d'usines de niveau {lvl} de l'utilisateur {user.name}.",
        color=money_color_int,
    )
    await ctx.send(embed=embed)


@bot.command()
async def set_usine(ctx, user: discord.Member, amount: int, lvl: int):
    if not dUtils.is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    db.set_usine(user.id, amount, lvl, 0)

    embed = discord.Embed(
        title="Opération réussie",
        description=f":factory: **{convert(str(amount))}** usines de niveau {lvl} ont été définis pour l'utilisateur {user.name}.",
        color=money_color_int,
    )
    await ctx.send(embed=embed)

@bot.command()
async def set_base(ctx, bat_type: int, user: discord.Member, amount: int, lvl: int):
    if not dUtils.is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return
    db.set_usine(user.id, amount, lvl, bat_type)
    bat_cat = "bases" if bat_type < 4 else "ecoles"
    bat_cat += "_militaires"
    bat_cat = base_data[bat_cat][f"{bat_types[bat_type][0]}{lvl}"]["type"]
    embed = discord.Embed(
        title="Opération réussie",
        description=f":factory: **{convert(str(amount))}** {bat_cat} de niveau {lvl} ont été définis pour l'utilisateur {user.name}.",
        color=money_color_int,
    )
    await ctx.send(embed=embed)

@bot.command()
async def batiments(ctx, bat_type: int, type, user: discord.Member = None):
    if user is None:
        user = ctx.author
    if int(bat_type) >= len(bat_types):
        return await ctx.send("Type de bâtiment invalide.")
    bat_name, max_lvl = bat_types[
        bat_type
    ]  # Récupère le niveau maximum en fonction du type de bâtiment
    if type.lower() != "all":
        try:
            type = int(type)
        except ValueError:
            return await ctx.send("Veuillez fournir un niveau valide ou 'all'.")

        if not is_valid_lvl(type, max_lvl):
            return await ctx.send(
                f"Le niveau pour {bat_name} doit être entre 1 et {max_lvl}."
            )

    if type.lower() == "all":
        embed = discord.Embed(title=f"{bat_name}s de {user.name}", description="")
        for i in range(1, max_lvl + 1):  # On parcourt les niveaux du type de bâtiment
            embed.description += (
                f"Niveau {i} : {str(db.get_usine(user.id, i, bat_type))}\n"
            )
    else:
        embed = discord.Embed(
            title=f"{bat_name}s de type {type} de {user.name}",
            description=f"L'utilisateur a **{str(db.get_usine(user.id, type, bat_type))}** {bat_name}s de niveau {type}.",
        )
    await ctx.send(embed=embed)

@bot.command()
async def remove_bat(
    ctx, bat_type: int, user: discord.Member, amount: Union[int, str], lvl: int
):
    if not dUtils.is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    balance = db.get_usine(user.id, lvl, bat_type)
    if balance is None:
        balance = 0

    if not amount_converter(amount, balance):
        embed = discord.Embed(
            title="Erreur de retrait de batiments",
            description=":factory: Le montant spécifié est invalide.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return

    payment_amount = amount_converter(amount, balance)
    if not db.has_enough_balance(user.id, payment_amount):
        embed = discord.Embed(
            title="Erreur de retrait d'argent",
            description=f":factory: L'utilisateur {user.name} n'a pas assez d'usines.",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return
    db.remove_usine(user.id, amount, lvl, 0)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":factory: **{convert(str(payment_amount))}** ont été retirés de l'inventaire d'usines de niveau {lvl} de l'utilisateur {user.name}.",
        color=money_color_int,
    )
    await ctx.send(embed=embed)


@bot.command()
async def del_betw(ctx, base_message: discord.Message, reach_message: discord.Message):
    if not ctx.author.id in bi_admins_id:
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description=f"{Erreurs['Erreur ']}",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return
    if (
        not reach_message.channel.id == ctx.channel.id
        or not base_message.channel.id == ctx.channel.id
    ):
        await ctx.send(
            "Erreur : Vous n'êtes pas dans le salon des messages à supprimer"
        )
    deleted = await ctx.channel.purge(
        limit=1000, before=base_message, after=reach_message
    )
    await ctx.channel.send(f"J'ai supprimé {len(deleted)} message(s)")


@bot.command()
async def del_til(ctx, reach_message: discord.Message):
    if not ctx.author.id in bi_admins_id:
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description=f"{Erreurs['Erreur ']}",
            color=error_color_int,
        )
        await ctx.send(embed=embed)
        return
    if not reach_message.channel.id == ctx.channel.id:
        await ctx.send(
            "Erreur : Vous n'êtes pas dans le salon des messages à supprimer"
        )
    deleted = await ctx.channel.purge(limit=1000, after=reach_message)
    await ctx.channel.send(f"J'ai supprimé {len(deleted)} message(s)")


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
    player_role = await get_player_role(ctx)
    non_player_role = await get_non_player_role(ctx)
    if not dUtils.is_authorized(ctx):
        return await ctx.send(embed=dUtils.get_auth_embed())
    continent = (continent.replace("é", "e")).lower()
    if type(continent) == str and continent in continents.keys():
        continent = discord.utils.get(ctx.guild.categories, id=continents[continent])
    if type(continent) != discord.CategoryChannel:
        return await ctx.send("Continent invalide.")
    await set_money(ctx, user, starting_amounts["money"])
    await set_pd(ctx, user, starting_amounts["pd"])
    await set_pp(ctx, user, starting_amounts["pp"])
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


@bot.command(
    name="reformat_emoji",
    brief="Reformate un emoji en lui assignant un nouveau nom, et optionnellement, enlève son arrière-plan.",
    usage="reformat_emoji <emoji> <nouveau_nom> [del_bg]",
    description="Reformate l'emoji spécifié avec un nouveau nom. Peut également supprimer l'arrière-plan si `del_bg` est activé.",
    help="""Reformate un emoji en changeant son nom et en enlevant, si demandé, l'arrière-plan.

    ARGUMENTS :
    - `<emoji>` : L'emoji à reformater (mention ou ID).
    - `<new_name>` : Nouveau nom de l'emoji. S'il ne commence pas par "NE_", ce préfixe sera ajouté automatiquement.
    - `[del_bg]` : Optionnel. Indique si l'arrière-plan de l'emoji doit être supprimé (True/False). Si activé, utilise une API pour reformater l'image sans fond.

    EXEMPLE :
    - `reformat_emoji :smile: smile_new` : Change le nom de l'emoji `:smile:` en `NE_smile_new`.
    - `reformat_emoji :smile: smile_no_bg True` : Change le nom de l'emoji `:smile:` en `NE_smile_no_bg` et enlève l'arrière-plan.
    """,
    hidden=False,
    enabled=True,
    case_insensitive=True,
)
async def reformat_emoji(
    ctx,
    emoji: discord.Emoji = commands.parameter(
        description="L'emoji à reformater (mention ou ID)"
    ),
    new_name: str = commands.parameter(
        description="Nouveau nom de l'emoji. Ajoute automatiquement le préfixe `NE_` si absent."
    ),
    del_bg: bool = commands.parameter(
        description="Optionnel. Si True, enlève l'arrière-plan de l'emoji."
    ),
) -> None:
    image_url = emoji.url
    if not new_name.startswith("NE_"):
        new_name = "NE_" + new_name
    new_file_name = new_name + ".png"

    if del_bg:
        rmbg.remove_background_from_img_url(image_url, new_file_name=new_file_name)
        await emoji.delete(reason=f"Reformatage de l'emoji {emoji.name}")
        with open(new_file_name, "rb") as image:
            image_data = image.read()
            emoji = await ctx.guild.create_custom_emoji(
                image=image_data,
                name=new_name,
                reason=f"Reformatage de l'emoji {emoji.name}",
            )
    else:
        await emoji.edit(name=new_name, reason=f"Reformatage de l'emoji {emoji.name}")

    await ctx.send(
        f"{ctx.message.author.mention} J'ai reformatté l'emoji en <:{new_name}:{emoji.id}> pour le serveur."
    )


@bot.command()
async def cat_syncer(ctx, cat: discord.CategoryChannel):
    if ctx.author.id not in bi_admins_id:
        return await ctx.send("Non.")
    for i in cat.channels:
        if i.overwrites == cat.overwrites:
            continue
        await i.edit(sync_permissions=True)
        await asyncio.sleep(2)
    await ctx.send("Fait")


@bot.command()
async def sync_channels(
    ctx,
    chan_to_sync: Union[
        discord.TextChannel,
        discord.VoiceChannel,
        discord.ForumChannel,
        discord.StageChannel,
    ],
    model_chan: Union[
        discord.TextChannel,
        discord.VoiceChannel,
        discord.ForumChannel,
        discord.StageChannel,
    ],
):
    if ctx.author.id not in bi_admins_id:
        return await ctx.send("Non.")
    new_permissions = model_chan.overwrites
    await chan_to_sync.edit(overwrites=new_permissions)
    await ctx.send("Fait")


@bot.command()
async def sync_cats(
    ctx, cat_to_sync: discord.CategoryChannel, model_cat: discord.CategoryChannel
):
    if ctx.author.id not in bi_admins_id:
        return await ctx.send("Non.")
    await cat_to_sync.edit(overwrites=model_cat.overwrites)
    await cat_syncer(ctx, cat_to_sync)
    await ctx.send("Fait")


@bot.command()
async def reformat_rp_channels(ctx):
    if ctx.author.id not in bi_admins_id:
        return await ctx.send("Non.")
    for continent_cat in continents_dict.values():
        continent_cat = discord.utils.get(ctx.guild.categories, id=int(continent_cat))
        for channel in continent_cat.channels:
            new_name = convert_country_name_channel(channel.name)
            if new_name == channel.name:
                continue
            await ctx.send(f"{channel.name} => {new_name}")
            # await channel.edit(name=new_name)
    await ctx.send("Fait")


def parse_embed_json(json_file):
    embeds_json = json.loads(json_file)["embeds"]

    for embed_json in embeds_json:
        embed = discord.Embed().from_dict(embed_json)
        yield embed


@bot.command()
async def send_rules(ctx, webhook_url: str):
    if ctx.author.id not in bi_admins_id:
        return await ctx.send("Non.")

    rules = {
        "hrp": "hrp.json",
        "rp": "rp.json",
        "military": "military.json",
        "territorial": "territorial.json",
    }

    rules_webhooks = {}
    summary_links = []
    summary_embeds = []
    rules_titles = {}

    # Lire et parser chaque fichier de règles
    for rule in rules.values():
        with open(f"rules/{rule}", "r") as file:
            r_file = file.read()
            rules_webhooks[rule] = list(
                parse_embed_json(r_file)
            )  # Convertir en liste d'embeds
            rules_titles[rule] = json.loads(r_file)["content"]

    # Lire les embeds pour le résumé
    with open("rules/summary.json", "r") as file:
        summary_embeds = list(parse_embed_json(file.read()))

    # Utiliser la session aiohttp pour envoyer les webhooks
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(webhook_url, session=session)

        # Envoyer les règles et récupérer les liens d'embed
        for rule_title, rule_embeds in zip(
            rules_titles.values(), rules_webhooks.values()
        ):
            await webhook.send(
                content=rule_title,
                username=bot.user.name,
                avatar_url=bot.user.avatar.url,
                wait=True,
            )
            embeds_to_send = []
            for embed in rule_embeds:
                embeds_to_send.append(
                    await webhook.send(
                        embed=embed,
                        username=bot.user.name,
                        avatar_url=bot.user.avatar.url,
                        wait=True,
                    )
                )
                # await asyncio.sleep(1)  # Si tu veux vraiment un délai
            summary_links.append(embeds_to_send[0].jump_url)
            await webhook.send(
                content="``` ```",
                username=bot.user.name,
                avatar_url=bot.user.avatar.url,
            )

        # Envoyer les embeds du résumé avec les URLs ajoutées

        await webhook.send(
            embed=summary_embeds[0],
            username=bot.user.name,
            avatar_url=bot.user.avatar.url,
        )
        for i, sum_embed in enumerate(summary_embeds[1:]):
            if i < len(summary_links):
                sum_embed.url = summary_links[
                    i
                ]  # Ajouter les URLs récupérées précédemment

            await webhook.send(
                embed=sum_embed, username=bot.user.name, avatar_url=bot.user.avatar.url
            )
            await asyncio.sleep(1)  # Si nécessaire
    announce_channel = discord.utils.get(ctx.guild.channels, id=873645600183287859)
    with open("rules/announcing.json", "r") as file:
        announce_embed = embed = discord.Embed().from_dict(json.loads(file.read()))
    await announce_channel.send(embed=announce_embed)
    await announce_channel.send("@everyone")
    await ctx.message.delete()


def get_query_level(user_id):
    if user_id in bi_admins_id:
        return "admin"
    return "user"


@bot.command()
async def groq_chat(ctx, *, message):
    global last_groq_query_time

    if not dUtils.is_authorized(ctx):
        return await ctx.send(embed=dUtils.get_auth_embed())

    # Anti-flood simple par user
    if last_groq_query_time:
        delta = datetime.now(timezone.utc) - last_groq_query_time
        if delta < timedelta(seconds=180) and ctx.author.id not in bi_admins_id:
            return await ctx.send(
                "⏳ Veuillez patienter 3 minutes entre chaque requête."
            )
    level = get_query_level(ctx.author.id)
    try:
        response = await ask_groq(message, level)
        last_groq_query_time = datetime.now(timezone.utc)
        await dUtils.send_long_message(ctx, response)
    except Exception as e:
        await ctx.send(f"❌ Erreur lors de la requête : {e}")


async def ask_groq(user_message: str, level: str = "user") -> str:
    max_tokens = {"user": 400, "trusted": 800, "mod": 2000, "admin": 8000}.get(
        level, 400
    )

    system_prompt = (
        "Tu es une IA destinée à assister un jeu de rôle géopolitique post-apocalyptique se déroulant en 2045, appelé Nouvelle Ère V4. "
        "Tu ne poses jamais de questions. Tu ne dis jamais 'je suis prêt à vous aider'. "
        "Tu ne fais jamais de compliments ou d'intros inutiles. "
        "Tu dois répondre uniquement aux questions ou suggestions posées, de manière concise, précise, et thématiquement cohérente avec l'univers. "
        "Utilise toujours un ton professionnel, froid et informatif. Évite les expressions comme 'bien sûr', 'nous pouvons', 'je suppose que'."
    )
    system_prompt += "\n" + get_server_context()
    messages = [{"role": "system", "content": system_prompt}]

    # Ajout de l'historique
    for user_msg, bot_reply in groq_chat_history[
        -5:
    ]:  # Ne pas envoyer trop de contexte
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": bot_reply})

    # Ajoute la nouvelle requête
    messages.append({"role": "user", "content": user_message})

    chat_completion = groq_client.chat.completions.create(
        messages=messages, model="llama-3.3-70b-versatile", max_tokens=max_tokens
    )

    content = chat_completion.choices[0].message.content
    groq_chat_history.append((user_message, content))
    return content


bot.run(token)