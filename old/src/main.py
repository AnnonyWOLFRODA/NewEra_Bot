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
import events as events
from typing import Union
import interactions
from PIL import Image
import io
import string
import requests
import math
import contextlib
from discord.ui import Button, View
from discord import message, emoji, Webhook, SyncWebhook
from removebg import RemoveBg
#from context import *
from groq import Groq
from other import *
from bot import bot
import logging
from config import token, DB_PATH
from bot import bot, setup_bot
from database import DatabaseManager, db_manager

logger = logging.getLogger("Database")

(""" 
CREATE TABLE IF NOT EXISTS Countries (
    country_id TEXT PRIMARY KEY,             -- Identifiant unique du pays
    name TEXT NOT NULL,                      -- Nom du pays
    public_channel_id TEXT NOT NULL,         -- ID du salon public (NON NULLABLE)
    secret_channel_id TEXT,                  -- ID du salon secret (NULLABLE)
    player_id TEXT                           -- ID du joueur qui contrôle le pays (NULL si aucun joueur)
);
CREATE TABLE IF NOT EXISTS Inventory (
    country_id TEXT PRIMARY KEY,             -- Clé étrangère liée au pays
    balance INTEGER DEFAULT 0 NOT NULL,      -- Balance financière
    pol_points INTEGER DEFAULT 0 NOT NULL,   -- Points politiques
    diplo_points INTEGER DEFAULT 0 NOT NULL, -- Points diplomatiques
    soldiers INTEGER DEFAULT 0 NOT NULL,     -- Nombre de soldats actifs
    reserves INTEGER DEFAULT 0 NOT NULL,     -- Nombre de réservistes
    FOREIGN KEY (country_id) REFERENCES Countries(country_id)
        ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS Structures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,     -- ID unique de la structure
    country_id TEXT NOT NULL,                 -- Clé étrangère vers le pays
    type TEXT NOT NULL CHECK (type IN ('Usine', 'Base', 'École')), -- Type de structure
    specialization TEXT NOT NULL CHECK (specialization IN ('Terrestre', 'Aérienne', 'Navale')), -- Spécialisation
    level INTEGER NOT NULL DEFAULT 1,         -- Niveau de la structure
    FOREIGN KEY (country_id) REFERENCES Countries(country_id)
        ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS Stats (
    country_id TEXT PRIMARY KEY,              -- Clé étrangère liée au pays
    population INTEGER DEFAULT 0 NOT NULL,    -- Population totale
    population_capacity INTEGER DEFAULT 0 NOT NULL, -- Capacité d’accueil de la population
    tech_level INTEGER DEFAULT 1 NOT NULL,    -- Niveau technologique
    gdp INTEGER DEFAULT 0 NOT NULL,           -- Produit Intérieur Brut
    FOREIGN KEY (country_id) REFERENCES Countries(country_id)
        ON DELETE CASCADE
);
""")
    
# if debug:
#     # N.B for DB debug : Deleting the file won't work. You have to incode DROP the table & creating it back.
#     cur.execute("PRAGMA table_info(inventory)")
#     columns = cur.fetchall()
#     cols = [''.join(str(tups)) for tups in columns]
#     with open("db_test.logs", "w") as f:
#        f.write("\n".join(cols) + '\n')

with open('../datas/usines.json') as f:
    production_data = json.load(f)

with open('../datas/bases.json') as f:
    base_data = json.load(f)

@bot.event
async def on_message(message):
    if isinstance(message.channel, discord.DMChannel) and message.author.id == 293869524091142144 and message.content.startswith("!"):
        await bot.get_channel(873645606214721536).send(message.content[1:])
    if (message.author == bot.user) or (not message.content):
        return
    if message.author.id == 292953664492929025:
        for embed in message.embeds:
            if embed.description.startswith('<:xmark:773218895150448640> '):
                sleep(10)
                await message.delete()
    if message.content == len(message.content) * message.content[0]:
        return
    if "soup" in message.content.lower():
        await message.add_reaction("🥣")
    await bot.process_commands(message)
    
@bot.event
async def on_reaction_add(reaction:discord.Reaction, user:discord.User):
    if user == bot.user:
        return
    message = reaction.message
    if message.channel.id != 1122576341582221434 and message.channel.category.id != 1269295981183369279:
        return
    if message.author == bot.user and reaction.emoji in ["🖋️", "🖊️"] and message.channel.id == 1122576341582221434:
        await handle_treaty(reaction, user)
    elif reaction.emoji == "✅":
        await create_treaty(reaction, user)
       
@bot.event
async def on_command_error(ctx, error):
    return await ctx.send(error)

# Single on_ready event handler for the shared bot
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    global db_manager
    from database import db_manager
    db_manager = DatabaseManager(DB_PATH)
    await db_manager.connect()
    
    # Set up and start the bot
    try:
        await setup_bot()
    except Exception as e:
        logger.exception(f"Error starting bot: {e}")
    finally:
        await db_manager.close()

# Run the bot
if __name__ == "__main__":
    bot.run(token)