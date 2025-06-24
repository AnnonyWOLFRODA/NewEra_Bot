from config import all_color_int, error_color_int, money_color_int, p_points_color_int, d_points_color_int
from config import wall_prices, bat_types
from config import Erreurs
from config import starting_amounts
from time import sleep
from discord.ext import commands
import discord
import string
import json

async def get_player_role(ctx):
    return ctx.guild.get_role(873955562734362625)
async def get_non_player_role(ctx):
    return ctx.guild.get_role(873955513921048646)

def parse_mentions(message:str):
    """
        Parse a message to extract mentions in the format "Name (ID)".
        The function looks for the keyword "Mention : " in the message and extracts
        all mentions that follow it. Each mention is expected to be in the format
        "Name (ID)" and separated by a pipe "|" character.
        Args:
            message (str): The input message containing mentions.
        Returns:
            dict: A dictionary where the keys are the names and the values are the IDs
                  of the mentions. If no mentions are found, an empty dictionary is returned.
        Example:
            message = "Some text before Mention : John Doe (123) | Jane Smith (456)"
            result = parse_mentions(message)
            # result will be {'John Doe': '123', 'Jane Smith': '456'}
        """
    # Séparer sur "Mention : " et ignorer la partie avant la première occurrence
    parts = message.split("Mention : ", 1)
    if len(parts) < 2:
        return {}  # Si aucun "Mention : ", renvoyer un dictionnaire vide

    mentions_part = parts[1]  # Obtenir la partie après "Mention : "
    
    # Séparer les mentions individuelles
    mentions_list = mentions_part.split("|")

    mentions_dict = {}
    for mention in mentions_list:
        try:
            name, id_part = mention.split("(")
            id_value = id_part.replace(")", "").strip()
            mentions_dict[name.strip()] = id_value
        except ValueError:
            # Si la structure est incorrecte (pas de parenthèses), ignorer la mention
            continue

    return mentions_dict

async def get_users_by_reaction(emoji: list, message: discord.Message):
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

async def insert_mention(message:discord.Message, user:discord.User, mentions:dict=None):
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
    embed = discord.Embed(title=message.embeds[0].title, description=message_content, color=all_color_int)
    await message.edit(embed=embed)
    
async def handle_treaty(reaction:discord.Reaction, user:discord.User):
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
    user_list = await get_users_by_reaction(["🖋️", "🖊️"], message)
    mentions = { user.mention: user.id for user in user_list }
    mention_str = " | ".join([f"{key} ({value})" for key, value in mentions.items()])
    message_content += f"\n\n Mention : {mention_str}"
    embed = discord.Embed(title="Traité", description=message_content, color=all_color_int)
    new_message = await message.channel.send(embed=embed)
    
 
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
        'objectif_type': 'habitants',
        "prix_fondations": 50
    }
    datas["objectif"] = int(await discord_input(ctx, "Entrez l'objectif de nombre d'habitants : "))
    datas["max_etages"] = int(await discord_input(ctx, f"Entrez le nombre maximum d'étages (par défaut: {datas['max_etages']}): ") or datas["max_etages"])
    datas["max_apartments"] = int(await discord_input(ctx, f"Entrez le nombre maximum de logements par étage (par défaut: {datas['max_apartments']}): ") or datas["max_apartments"])
    datas["people_per_apartment"] = get_people_per_apartment(datas["taille_moyenne"])
    datas["prix_moyen"] = int(await discord_input(ctx, f"Entrez le prix moyen du mètre carré (par défaut: {datas['prix_moyen']}): ") or datas["prix_moyen"])
    
    buildings = []
    current_building = {
        'nombre_etages': 1,
        'nombre_logements': 1,
        'people_per_apartment': datas["people_per_apartment"],
        'surface': 0,
        'surface_net': 0,
        'surface_habitable': 0,
        'surface_net_habitable': 0,
        'construction_cost': 0,
        'profondeur_fondation': 3
    }
    actual_stage_logements = 0
    
    while True:
        ctx.author.send(f"Calcul en cours... ({current_building['nombre_logements']} logements)")
        total_area = calculate_total_area(datas["taille_moyenne"], current_building['nombre_logements'])
        current_building['surface'] = total_area
        current_building['surface_net'] = round(total_area / current_building['nombre_etages'])
        construction_cost = calculate_construction_cost(datas, total_area, current_building)
        current_building['construction_cost'] = construction_cost
        current_building['surface_habitable'] = total_area - (total_area * 0.1)
        current_building['surface_net_habitable'] = round(current_building['surface_habitable'] / current_building['nombre_etages'])
        current_building['profondeur_fondation'] = (current_building['nombre_etages'] + 1)
        
        if sum(building['nombre_logements'] * building['people_per_apartment'] for building in buildings + [current_building]) >= datas["objectif"]:
            buildings.append(current_building)
            break
        
        current_building['nombre_logements'] += 1
        actual_stage_logements += 1
        if actual_stage_logements >= datas["max_apartments"]:
            if current_building['nombre_etages'] < datas["max_etages"]:
                current_building['nombre_etages'] += 1
                actual_stage_logements = 0
            else:
                buildings.append(current_building)
                current_building = {
                    'nombre_etages': 1,
                    'nombre_logements': 1,
                    'people_per_apartment': datas["people_per_apartment"],
                    'surface': 0,
                    'surface_net': 0,
                    'surface_habitable': 0,
                    'surface_net_habitable': 0,
                    'construction_cost': 0,
                    'profondeur_fondation': 3
                }
    
    return buildings, datas

def get_auth_embed():
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
        'objectif_type': 'budget',
        "prix_fondations": 50
    }
    datas["objectif"] = int(await discord_input(ctx, "Entrez l'objectif de prix : "))
    datas["max_etages"] = int(await discord_input(ctx, f"Entrez le nombre maximum d'étages (par défaut: {datas['max_etages']}): ") or datas["max_etages"])
    datas["max_apartments"] = int(await discord_input(ctx, f"Entrez le nombre maximum de logements par étage (par défaut: {datas['max_apartments']}): ") or datas["max_apartments"])
    datas["people_per_apartment"] = get_people_per_apartment(datas["taille_moyenne"])
    
    buildings = []
    current_building = {
        'nombre_etages': 1,
        'nombre_logements': 1,
        'people_per_apartment': datas["people_per_apartment"],
        'surface': 0,
        'surface_net': 0,
        'surface_habitable': 0,
        'surface_net_habitable': 0,
        'construction_cost': 0,
        'profondeur_fondation': 3
    }
    actual_stage_logements = 0
    while True:
        total_area = calculate_total_area(datas["taille_moyenne"], current_building['nombre_logements'])
        current_building['surface'] = total_area
        current_building['surface_net'] = round(total_area / current_building['nombre_etages'])
        construction_cost = calculate_construction_cost(datas, total_area, current_building)
        current_building['construction_cost'] = construction_cost
        current_building['surface_habitable'] = total_area - (total_area * 0.1)
        current_building['surface_net_habitable'] = round(current_building['surface_habitable'] / current_building['nombre_etages'])
        current_building['profondeur_fondation'] = (current_building['nombre_etages'] + 1)
        
        if (sum(building['construction_cost'] for building in buildings + [current_building]) >= datas["objectif"]):
            buildings.append(current_building)
            break

        current_building['nombre_logements'] += 1
        actual_stage_logements += 1
        if actual_stage_logements >= datas["max_apartments"]:
            if current_building['nombre_etages'] < datas["max_etages"]:
                current_building['nombre_etages'] += 1
                actual_stage_logements = 0
            else:
                buildings.append(current_building)
                current_building = {
                    'nombre_etages': 1,
                    'nombre_logements': 1,
                    'people_per_apartment': datas["people_per_apartment"],
                    'surface': 0,
                    'surface_net': 0,
                    'surface_habitable': 0,
                    'surface_net_habitable': 0,
                    'construction_cost': 0,
                    'profondeur_fondation': 3
                }
    return buildings, datas


def get_leads(lead_type: int, user_id: str):
    if lead_type == 1:
        cur.execute("SELECT player_id FROM inventory ORDER BY balance DESC")
    elif lead_type == 2:
        cur.execute("SELECT player_id FROM inventory ORDER BY pol_points DESC")
    elif lead_type == 3:
        cur.execute("SELECT player_id FROM inventory ORDER BY diplo_points DESC")
    elif lead_type == 4:
        cur.execute("SELECT player_id FROM inventory ORDER BY (balance + pol_points + diplo_points) DESC")
    leaderboard = cur.fetchall()
    leaderboard = [str(row[0]) for row in leaderboard]  # Extraire uniquement les `player_id` dans une liste    
    return leaderboard.index(str(user_id)) + 1 if str(user_id) in leaderboard else -1



def convert_country_name(old_name: str):
    new_name = ""
    car_sal1 = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
    car_sal2 = ["𝐀", "𝐁", "𝐂", "𝐃", "𝐄", "𝐅", "𝐆", "𝐇", "𝐈", "𝐉", "𝐊", "𝐋", "𝐌", "𝐍", "𝐎", "𝐏", "𝐐", "𝐑", "𝐒", "𝐓", "𝐔", "𝐕", "𝐖", "𝐗", "𝐘", "𝐙"]
    for i in str(old_name):
        if i.isupper():
            new_name += car_sal2[car_sal1.index(i)]
        else:
            new_name += i
    return new_name

def convert_country_name_channel(old_name: str):
    new_name = ""
    car_sal1 = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
    car_sal2 = ["𝐀", "𝐁", "𝐂", "𝐃", "𝐄", "𝐅", "𝐆", "𝐇", "𝐈", "𝐉", "𝐊", "𝐋", "𝐌", "𝐍", "𝐎", "𝐏", "𝐐", "𝐑", "𝐒", "𝐓", "𝐔", "𝐕", "𝐖", "𝐗", "𝐘", "𝐙"]
    accents = [ "é", "è", "ê", "ë", "à", "â", "ä", "ô", "ö", "ù", "û", "ü", "î", "ï", "ç"]
    car_space = {
        "good":["「","」"],
        "bad":["《","》"]
    }
    for i in range(len(old_name)):
        if i == 0:
            new_name += old_name[i]
        elif (old_name[i-1] not in string.ascii_letters) and (old_name[i-1] in car_sal2) and (old_name[i] in string.ascii_letters) and (old_name[i-1] not in accents) and (old_name[i] not in car_sal2):
            new_name += car_sal2[car_sal1.index(old_name[i].upper())]
        else:
            new_name += old_name[i]
    new_name = new_name.replace(car_space["bad"][0], car_space["good"][0])
    new_name = new_name.replace(car_space["bad"][1], car_space["good"][1])
    return new_name


def convert(nu: str) -> str:
    # Conversion en entier pour manipuler les parties entières
    try:
        number = int(nu)
        return '{:,}'.format(number).replace(',', '.')
    except ValueError:
        # Gestion des nombres décimaux
        try:
            number = float(nu)
            # Séparation de la partie entière et décimale
            integer_part, decimal_part = str(number).split('.')
            # Formatage de la partie entière
            formatted_integer_part = '{:,}'.format(int(integer_part)).replace(',', '.')
            return f"{formatted_integer_part},{decimal_part}"
        except ValueError:
            return "Invalid input"

def unconvert(nu:str):
    try:
        return int(nu.replace(".", "").replace(",", ""))
    except ValueError:
        return Erreurs["Erreur 3"]

def is_authorized(ctx):
    authorized_role_id = 1230046019262087198
    return authorized_role_id in [role.id for role in ctx.author.roles]

def has_enough_balance(player_id, amount):
    cur.execute("SELECT balance FROM inventory WHERE player_id = ?", (player_id,))
    result = cur.fetchone()
    if result is None:
        return False
    if amount <= 0:
        return False
    return int(result[0]) >= int(amount)

def has_enough_points(player_id, amount, type:int=1):
    if type == 1:
        cur.execute("SELECT pol_points FROM inventory WHERE player_id = ?", (player_id,))
    else:
        cur.execute("SELECT diplo_points FROM inventory WHERE player_id = ?", (player_id,))
    result = cur.fetchone()
    if result is None:
        return False
    if amount <= 0:
        return False
    return result[0] >= amount

def give_money(player_id, amount):
    cur.execute("SELECT balance FROM inventory WHERE player_id = ?", (player_id,))
    result = cur.fetchone()
    if result is not None:
        new_balance = result[0] + amount
        cur.execute("UPDATE inventory SET balance = ? WHERE player_id = ?", (new_balance, player_id))
    else:
        cur.execute("INSERT INTO inventory (player_id, balance) VALUES (?, ?)", (player_id, amount))
    conn.commit()
    
def give_points(player_id, amount, type:int=1):
    if type == 1:
        cur.execute("SELECT pol_points FROM inventory WHERE player_id = ?", (player_id,))
    else:
        cur.execute("SELECT diplo_points FROM inventory WHERE player_id = ?", (player_id,))
    result = cur.fetchone()
    if type == 1:
        if result is not None:
            new_points = result[0] + amount
            cur.execute("UPDATE inventory SET pol_points = ? WHERE player_id = ?", (new_points, player_id))
        else:
            cur.execute("INSERT INTO inventory (player_id, pol_points) VALUES (?, ?)", (player_id, amount))
    else:
        if result is not None:
            new_points = result[0] + amount
            cur.execute("UPDATE inventory SET diplo_points = ? WHERE player_id = ?", (new_points, player_id))
        else:
            cur.execute("INSERT INTO inventory (player_id, diplo_points) VALUES (?, ?)", (player_id, amount))

    conn.commit()

def take_money_func(player_id, amount):
    cur.execute("SELECT balance FROM inventory WHERE player_id = ?", (player_id,))
    result = cur.fetchone()
    if result is not None:
        new_balance = result[0] - amount
        cur.execute("UPDATE inventory SET balance = ? WHERE player_id = ?", (new_balance, player_id))
    else:
        cur.execute("INSERT INTO inventory (player_id, balance) VALUES (?, ?)", (player_id, -amount))
    conn.commit()

def take_points_func(player_id, amount, type:int=1):
    if type == 1:
        cur.execute("SELECT pol_points FROM inventory WHERE player_id = ?", (player_id,))
    else:
        cur.execute("SELECT diplo_points FROM inventory WHERE player_id = ?", (player_id,))
    result = cur.fetchone()
    if type == 1:
        if result:
            new_balance = result[0] - amount
            cur.execute("UPDATE inventory SET pol_points = ? WHERE player_id = ?", (new_balance, player_id))
        else:
            cur.execute("INSERT INTO inventory (player_id, pol_points) VALUES (?, ?)", (player_id, -amount))
    else:
        if result:
            new_balance = result[0] - amount
            cur.execute("UPDATE inventory SET diplo_points = ? WHERE player_id = ?", (new_balance, player_id))
        else:
            cur.execute("INSERT INTO inventory (player_id, diplo_points) VALUES (?, ?)", (player_id, -amount))
    conn.commit()

def get_balance(player_id):
    cur.execute("SELECT balance FROM inventory WHERE player_id = ?", (player_id,))
    result = cur.fetchone()
    if result is not None:
        return str(result[0])
    else:
        return 0

def get_points(player_id, type:int=1):
    if type == 1:
        cur.execute("SELECT pol_points FROM inventory WHERE player_id = ?", (player_id,))
    else:
        cur.execute("SELECT diplo_points FROM inventory WHERE player_id = ?", (player_id,))

    result = cur.fetchone()
    if result is not None:
        return result[0]
    else:
        return 0

def amount_converter(amount, sender_balance):
    if isinstance(amount, int):
        # Le montant est déjà un entier
        payment_amount = amount
    elif isinstance(amount, str):
        # Le montant est une chaîne de caractères
        if amount.lower() == "all":
            # Utiliser l'intégralité du solde de l'utilisateur émetteur
            payment_amount = sender_balance
        elif amount.lower() == "mid":
            # Utiliser la moitié du solde de l'utilisateur émetteur
            payment_amount = sender_balance // 2
        else:
            try:
                payment_amount = int(amount.replace(",", ""))
            except ValueError:
                try:
                    payment_amount = int(amount.replace(".", ""))
                except ValueError:
                    return
    else:
        return 
    return payment_amount

async def discord_input(ctx, message):
    await ctx.send(message)
    try:
        response = await bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=90)
    except asyncio.TimeoutError:
        return None
    return response.content

def calculate_total_area(taille_moyenne, nombre_logements):
    return taille_moyenne * nombre_logements

def calculate_construction_cost(datas, total_area, building):
    mur_price = wall_prices[datas['type_murs']]
    mur_cost = mur_price[0] * total_area  # Calculer le coût des murs (hypothèse simplifiée)
    
    # Calculer le coût des fondations en fonction du nombre d'étages
    etages = building['nombre_etages']
    prix_fonda = datas['prix_fondations'] + (etages * 50)

    fondations_cost = prix_fonda * (building['surface_net'] * building['profondeur_fondation'])  # Hypothèse simplifiée du coût des fondations au mètre carré

    # Calculer le coût total de construction
    construction_cost = total_area * datas['prix_moyen'] + mur_cost + fondations_cost
    return construction_cost

def get_people_per_apartment(taille_moyenne):
    # Initial values for surface and number of people
    surface_per_first_4 = 8
    surface_per_additional = 6
    
    # Start by assuming 4 people
    initial_habitants = 4
    initial_surface = initial_habitants * surface_per_first_4
    
    # If the surface is enough for the initial 4 people, calculate the additional inhabitants
    if taille_moyenne >= initial_surface:
        remaining_surface = taille_moyenne - initial_surface
        additional_habitants = remaining_surface // surface_per_additional
        total_habitants = initial_habitants + additional_habitants
    else:
        # If not enough for 4 people, calculate the max inhabitants possible within the given surface
        total_habitants = taille_moyenne // surface_per_first_4
    
    return total_habitants    

async def send_long_message(ctx, message):
    messages = []
    while len(message) > 2000:
        index = message.rfind("\n", 0, 2000)
        messages.append(message[:index])
        message = message[index:]
    messages.append(message)
    for msg in messages:
        await ctx.send(msg)

async def eco_logger(code, amount, user1: discord.Member, user2: discord.Member=None, type:int=1):
    log_channel = bot.get_channel(1261064715480862866)
    if not code in code_list:
        return print("Erreur de code : Le code donné n'est pas bon.")
    if len(str(amount)) > 3:
        amount = convert(str(amount))
    if code.startswith('M'):
        if code == 'M1':
            embed = discord.Embed(title="Nouvelle transaction entre joueurs", description=f":moneybag: L'utilisateur {user1.name} ({user1.id}) a donné {amount} à {user2.name} ({user2.id}).", color=money_color_int)
        elif code == 'M2':
            embed = discord.Embed(title="<a:NE_Alert:1261090848024690709> Ajout d'argent", description=f":moneybag: L'utilisateur {user1.name} ({user1.id}) s'est fait ajouter {amount} par {user2.name} ({user2.id}).", color=money_color_int)
        elif code == 'M3':
            embed = discord.Embed(title="<a:NE_Alert:1261090848024690709> Argent défini", description=f":moneybag: L'utilisateur {user1.name} ({user1.id}) s'est fait définir son argent à {amount} par {user2.name} ({user2.id}).", color=money_color_int)
        elif code == 'M4':
            embed = discord.Embed(title="Argent payé", description=f":moneybag: L'utilisateur {user1.name} ({user1.id}) a payé {amount} à la banque.", color=money_color_int)    
        elif code == 'M5':
            embed = discord.Embed(title="<a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> Retrait d'argent", description=f":moneybag: L'utilisateur {user1.name} ({user1.id}) s'est fait retirer {amount} par {user2.name} ({user2.id}).", color=money_color_int)
        elif code == 'MR':
            embed = discord.Embed(title="<a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> Reset de l'économie", description=f":moneybag: L'utilisateur {user1.name} ({user1.id}) a réinitialisé l'économie.", color=money_color_int)
        elif code == 'MRR':
            embed = discord.Embed(title="<a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> Tentative de reset de l'économie par un membre", description=f":moneybag: L'utilisateur {user1.name} ({user1.id}) a essayé de réinitialiser l'économie.", color=money_color_int)

    elif code.startswith('P'):
        p_type = "Points politiques" if type == 1 else "Points diplomatiques"
        points_color_int = p_points_color_int if type == 1 else d_points_color_int
        if code == 'P1':
            embed = discord.Embed(title=f"<a:NE_Alert:1261090848024690709> {p_type} ajoutés", description=f":blue_circle: L'utilisateur {user1.name} ({user1.id}) s'est fait ajouter {amount} {p_type} par {user2.name} ({user2.id}).", color=points_color_int)    
        elif code == 'P2':
            embed = discord.Embed(title=f"<a:NE_Alert:1261090848024690709> {p_type} définis", description=f":blue_circle: L'utilisateur {user1.name} ({user1.id}) s'est fait définir ses {p_type} à {amount} par {user2.name} ({user2.id}).", color=points_color_int)    
        elif code == 'P3':
            embed = discord.Embed(title=f"{p_type} utilisé", description=f":blue_circle: L'utilisateur {user1.name} ({user1.id}) a utilisé {amount} {p_type}.", color=points_color_int)    
        elif code == 'P4':
            embed = discord.Embed(title=f"<a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> {p_type} retirés", description=f":blue_circle: L'utilisateur {user1.name} ({user1.id}) s'est fait retirer {amount} {p_type} par {user2.name} ({user2.id}).", color=points_color_int)
        elif code == 'PR':
            embed = discord.Embed(title=f"<a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> Reset des {p_type}", description=f":blue_circle: L'utilisateur {user1.name} ({user1.id}) a réinitialisé les {p_type}.", color=points_color_int)    
        elif code == 'PRR':
            embed = discord.Embed(title=f"<a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> <a:NE_Alert:1261090848024690709> Tentative de reset des {p_type} par un membre non autorisé", description=f":blue_circle: L'utilisateur {user1.name} ({user1.id}) a essayé de réinitialiser les {p_type}.", color=points_color_int)
    else:
        print("Erreur")
        return
    await log_channel.send(embed=embed)

async def set_money_func(ctx, user: discord.Member, amount: int):
    cur.execute("SELECT balance FROM inventory WHERE country_id = ?", (user.id,))
    result = cur.fetchone()

    if result is None:
        # L'utilisateur n'existe pas dans la base de données, l'ajouter avec le montant spécifié
        cur.execute("INSERT INTO inventory (country_id, balance) VALUES (?, ?)", (user.id, amount))
    else:
        # Mettre à jour le montant d'argent de l'utilisateur existant
        cur.execute("UPDATE inventory SET balance = ? WHERE country_id = ?", (amount, user.id))

    conn.commit()

async def set_points_func(ctx, user: discord.Member, amount: int, type:int=1):
    if type == 1:
        cur.execute("SELECT pol_points FROM inventory WHERE country_id = ?", (user.id,))
        result = cur.fetchone()
        if result is None:
            cur.execute("INSERT INTO inventory (country_id, pol_points) VALUES (?, ?)", (user.id, amount))
        else:
            cur.execute("UPDATE inventory SET pol_points = ? WHERE country_id = ?", (amount, user.id))
    else:
        cur.execute("SELECT diplo_points FROM inventory WHERE country_id = ?", (user.id,))
        result = cur.fetchone()
        if result is None:
            cur.execute("INSERT INTO inventory (country_id, diplo_points) VALUES (?, ?)", (user.id, amount))
        else:
            cur.execute("UPDATE inventory SET diplo_points = ? WHERE country_id = ?", (amount, user.id))
    conn.commit()

##

def find_app_type(app_name):
    app_types = ["terrestre", "navale", "aerienne", "explosif"]

    for app_type in app_types:
        for apparel in production_data["7"]["production_mensuelle"][app_type]:
            if apparel.lower() == app_name.lower():
                return app_type
    return None

def calculer_temps_production(player_id, appareil, quantite:int, app_type=None):
    # Connexion à la base de données
    cur.execute("SELECT * FROM inventory WHERE player_id = ?", (player_id,))
    player_data = cur.fetchone()
    
    if not player_data:
        return f"Player ID {player_id} not found."

    # Définir un mapping pour les colonnes de la base de données
    columns = ["player_id", "balance", "pol_points", "diplo_points", 
               "usine_lvl1", "usine_lvl2", "usine_lvl3", "usine_lvl4", 
               "usine_lvl5", "usine_lvl6", "usine_lvl7", "population_caapcity"]

    # Créer un dictionnaire des données du joueur
    player_inventory = dict(zip(columns, player_data))
    # Calculer la capacité de production totale par mois
    total_production_capacity = 0
    
    app_type = find_app_type(appareil)
    for i in range(1, 8):
        usine_lvl = f"usine_lvl{i}"
        usine_count = player_inventory[usine_lvl]
        if usine_count > 0:
            production_capacity = int(production_data[str(i)]["production_mensuelle"][app_type][appareil])
            total_production_capacity += production_capacity * usine_count

    if total_production_capacity == 0:
        return f"Player ID {player_id} has no production capacity for {appareil}."

    # Calculer le temps nécessaire pour produire la quantité demandée
    #return f"Quantite: {quantite}, total_production_capacity: {total_production_capacity}. Type appareil: {type(quantite)}, {type(total_production_capacity)}"
    time_needed_months = math.ceil(int(quantite) / int(total_production_capacity))
    
    return f"Pour produire {quantite} {appareil} (type {app_type}), il vous faudra {time_needed_months} mois. Vous avez une capacité de production totale de {total_production_capacity} par mois."

def is_valid_lvl(type:int, lvl:int):
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
    return False

def give_usine(player_id, amount, lvl, bat_type:int):
    cur.execute(f"SELECT {bat_types[bat_type][0]}{lvl} FROM inventory WHERE player_id = ?", (player_id,))
    result = cur.fetchone()
    if result is not None:
        new_balance = result[0] + amount
        cur.execute(f"UPDATE inventory SET {bat_types[bat_type][0]}{lvl} = ? WHERE player_id = ?", (new_balance, player_id))
    else:
        cur.execute(f"INSERT INTO inventory (player_id, {bat_types[bat_type][0]}{lvl}) VALUES (?, ?)", (player_id, amount))
    conn.commit()

def set_usine_func(player_id, amount: int, lvl: int, bat_type:int):
    cur.execute(f"SELECT {bat_types[bat_type][0]}{lvl} FROM inventory WHERE player_id = ?", (player_id,))
    result = cur.fetchone()
    if result is not None:
        cur.execute(f"UPDATE inventory SET {bat_types[bat_type][0]}{lvl} = ? WHERE player_id = ?", (amount, player_id))
    else:
        cur.execute(f"INSERT INTO inventory (player_id, {bat_types[bat_type][0]}{lvl}) VALUES (?, ?)", (player_id, amount))
    conn.commit()

def remove_usine_func(player_id, amount: int, lvl: int, bat_type:int):
    cur.execute(f"SELECT {bat_types[bat_type][0]}{lvl} FROM inventory WHERE player_id = ?", (player_id,))
    result = cur.fetchone()
    if result is not None:
        new_balance = result[0] - amount
        cur.execute(f"UPDATE inventory SET {bat_types[bat_type][0]}{lvl} = ? WHERE player_id = ?", (new_balance, player_id))
    else:
        cur.execute(f"INSERT INTO inventory (player_id, {bat_types[bat_type][0]}{lvl}) VALUES (?, ?)", (player_id, -amount))
    conn.commit()
    

def get_usine(player_id, lvl, bat_type:int):
    cur.execute(f"SELECT {bat_types[bat_type][0]}{lvl} FROM inventory WHERE player_id = ?", (player_id,))
    result = cur.fetchone()
    if result is not None:
        return int(result[0])
    else:
        return 0

def has_enough_bats(player_id, amount, lvl, bat_type:int):
    cur.execute(f"SELECT {bat_types[bat_type][0]}{lvl} FROM inventory WHERE player_id = ?", (player_id,))
    result = cur.fetchone()
    if result is None:
        return False
    if amount <= 0:
        return False
    return int(result[0]) >= int(amount)


def parse_embed_json(json_file):
    embeds_json = json.loads(json_file)['embeds']

    for embed_json in embeds_json:
        embed = discord.Embed().from_dict(embed_json)
        yield embed
    
("""
def generate_response(user_message, query_type:int=0):
    query_types = [400, 800, 2000, 8000]
    max_tokens = query_types[query_type]
    try:
        system_prompt = get_server_context()
        typed_context = get_global_context() + '\n\n' + user_message # Add user message to context
        typed_context += f"\nYou have a maximum of {max_tokens} tokens to generate a response."

        # Construct conversation history for the API call
        messages = [{"role": "system", "content": system_prompt}]
        for user_msg, bot_reply in groq_chat_history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": bot_reply})

        # Add the latest user message
        messages.append({"role": "user", "content": typed_context})

        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            max_tokens=max_tokens
        )
        # Return the response from the model
        return chat_completion.choices[0].message.content, typed_context
    except Exception as e:
        return f"Error: {e}", typed_context
""")
def respond(message, query_type:int=0):
    response, message = generate_response(message, query_type)
    groq_chat_history.append((message, response))  # Add user and bot message to history
    return response # Return empty input and updated history

def get_sql_to_json(player_id1, player_id2=None):
    cur.execute("SELECT * FROM inventory WHERE player_id = ?", (player_id1,))
    rows = cur.fetchall()
    if player_id2:
        cur.execute("SELECT * FROM inventory WHERE player_id = ?", (player_id2,))
        rows += cur.fetchall()
    column_names = [description[0] for description in cur.description]
    data = [dict(zip(column_names, row)) for row in rows]
    with open('output.json', 'w') as f:
        json.dump(data, f, indent=4)

