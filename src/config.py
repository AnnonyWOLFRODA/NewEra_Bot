from dotenv import dotenv_values
from datetime import datetime, timezone
import discord
from discord.ext import commands
from discord.ext.commands import has_role
from discord.ext.commands import Context
from removebg import RemoveBg
from groq import Groq
import sqlite3
import os
import math

DATA_PATH = os.path.join(os.path.dirname(__file__), '../datas/')
DB_PATH = os.path.join(DATA_PATH, 'rts.db')

Erreurs = {"Erreur 1": "Le salon dans lequel vous effectuez la commande n'est pas le bon\n", "Erreur 2": "Aucun champ de recherche n'a été donné\n", "Erreur 3": "Le champ de recherche donné est invalide\n", "Erreur 3.2": "Le champ de recherche donné est invalide - Le pays n'est pas dans les fichiers\n", "Erreur 4": "La pause est déjà en cours\n", "Erreur 5": "Vous n'avez pas la permission de faire la commande.\n"}
continents = ["Europe", "Amerique", "Asie", "Afrique", "Moyen-Orient", "Oceanie"]

token = dotenv_values(".env")["TOKEN"]
removebg_apikey = dotenv_values(".env")["REMOVEBG_API_KEY"]
groq_api_key = dotenv_values(".env")["GROQ_API_KEY"]
debug = False
embed_p = ""

bi_admins_id = [293869524091142144, 557638191231008768, 1225576816958242877, 868399385149579274]
usefull_role_ids_dic = {
    "staff":1230046019262087198
}
groq_client = Groq(api_key=groq_api_key)
last_groq_query_time = datetime.now(timezone.utc)

rmbg = RemoveBg(removebg_apikey, "error.log")

duration_in_seconds = 0

starting_amounts = {
    "money": 500000000,
    "pd": 4,
    "pp": 2
}

continents_dict = {"Oceanie":992368253580087377, 
    "Asie":1243672298381381816, 
    "Moyen-Orient":951163668102520833, 
    "Afrique":961678827933794314, 
    "Amerique":952314456870907934, 
    "Europe":955479237001891870
}
groq_chat_history = []

error_color_int = int("FF5733", 16)
money_color_int = int("FFF005", 16)
p_points_color_int = int('006AFF', 16)
d_points_color_int = int('8b1bd1', 16)
all_color_int = int('00FF44', 16)
factory_color_int = int("6E472E", 16)

code_list = ['M1', 'M2', 'M3', 'M4', 'M5', 'MR', 'MRR', 'P1', 'P2', 'P3', 'P4', 'PR', 'PRR']

bat_types = {
    0: ["usine_lvl", 7],      # Usines ont 7 niveaux
    1: ["terrestre_", 7],     # Bases terrestres ont 7 niveaux
    2: ["aerienne_", 4],      # Bases aériennes ont 4 niveaux
    3: ["maritime_", 4],      # Bases maritimes ont 4 niveaux
    4: ["ecole_", 4]          # Écoles militaires ont 4 niveaux
}
wall_prices = {
    'béton': (60, 150),  # prix par m³
    'ossature métallique': (1000, 1000)  # prix par m²
}

# Usine = 0
# Terrestre = 1
# Aerienne = 2
# Maritime = 3
# Ecole = 4