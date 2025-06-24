import discord
from discord.ext import commands
from config import *
from economy import *
from other import *
from database import db_manager
from config import DB_PATH
from typing import Union

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=['.', '/'], intents=intents)

# Load the command cogs from the commands subdirectory.
for extension in [
    "commands.Chat",
    "commands.Inventory",
    "commands.Treaties",
    "commands.Admin",
    "commands.Mod",
    "commands.Production",
]:
    bot.load_extension(extension)

async def setup_bot():
    print("Setting up NEbot...")
    
@bot.command()
async def get_user_role(ctx):
    await ctx.message.reply(f"get_user_role {ctx.author.id} {ctx.author.name}: {get_player_role(ctx)}")
    
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
    if await discord_input(ctx, "Bienvenue dans le programme de construction d'immeubles!\nVoulez-vous construire un immeuble par nombre d'habitants ou par coût de construction? (habitants/coût)") == "habitants":
        buildings, datas = await calculate_by_population(ctx)
    else:
        buildings, datas = await calculate_by_budget(ctx)
        
    await ctx.send("Enregistrement des données...")
    
    total_construction_cost = sum(building['construction_cost'] for building in buildings)
    total_logements = sum(building['nombre_logements'] for building in buildings)
    total_etages = sum(building['nombre_etages'] for building in buildings)
    total_habitants = sum(building['nombre_logements'] * building['people_per_apartment'] for building in buildings)
    
    await ctx.send("<a:loading:1259247395603222600> Calcul en cours...")
    answer = ("\nBilan de la construction de l'immeuble:\n")
    
    for i, building in enumerate(buildings):
        logements_par_etage = building['nombre_logements'] // building['nombre_etages']
        habitants_par_etage = logements_par_etage * building['people_per_apartment']
        if len(answer) > 1800 and len(buildings) < 20:
            await ctx.send(answer)
            answer = ""
        answer += (f"\n- Bâtiment {i + 1}:\n")
        answer += (f"  - Coût de construction: {convert(str(building['construction_cost']))} €\n")
        answer += (f"  - Nombre d'étages: {building['nombre_etages']}\n")
        answer += (f"  - Logements par étage: {logements_par_etage}\n")
        answer += (f"  - Habitants par étage: {habitants_par_etage}\n")
        answer += (f"  - Nombre total de logements: {building['nombre_logements']}\n")
        answer += (f"  - Nombre total d'habitants: {building['nombre_logements'] * building['people_per_apartment']}\n")
        answer += (f"  - Surface totale: {building['surface']} m²\n")
        answer += (f"  - Surface nette: {building['surface_net']} m²\n")
        answer += (f"  - Surface habitable: {building['surface_habitable']} m²\n")
        answer += (f"  - Surface nette habitable: {building['surface_net_habitable']} m²\n")
        answer += (f"  - Profondeur des fondations: {building['profondeur_fondation']} m\n")
        
    if len(buildings) < 20:
        await send_long_message(ctx, answer)
        answer = (f"\n- **Bilan final:**\n  - Coût total de construction: {convert(str(total_construction_cost))} €\n")
    else:
        answer += (f"\n- Coût total de construction: {convert(str(total_construction_cost))} €\n")
    answer += (f"  - Nombre total d'étages: {total_etages}\n")
    answer += (f"  - Nombre total de logements: {total_logements}\n")
    answer += (f"  - Nombre total d'habitants: {total_habitants}\n")
    answer += (f"  - Nombre moyen d'habitants par logement: {total_habitants / total_logements}\n")
    answer += (f"  - Surface totale brute: {sum(building['surface'] for building in buildings)} m²\n")
    answer += (f"  - Surface totale nette: {sum(building['surface_net'] for building in buildings)} m²\n")
    answer += (f"  - Surface totale habitable: {sum(building['surface_habitable'] for building in buildings)} m²\n")
    answer += (f"  - Surface totale nette habitable: {sum(building['surface_net_habitable'] for building in buildings)} m²\n")
    answer += (f"  - Moyenne du nombre d'étages par bâtiment: {total_etages / len(buildings)}\n")
    answer += (f"  - Nombre total de bâtiments: {len(buildings)}")

    answer += (f"\n- Paramètres utilisés:\n")
    answer += (f"  - Taille moyenne des appartements: {datas['taille_moyenne']} m²\n")
    answer += (f"  - Prix moyen du mètre carré: {datas['prix_moyen']} €\n")
    answer += (f"  - Type de murs: {datas['type_murs']}\n")
    answer += (f"  - Nombre maximum d'étages: {datas['max_etages']}\n")
    answer += (f"  - Nombre maximum de logements par étage: {datas['max_apartments']}\n")
    answer += (f"  - Nombre moyen d'habitants par logement: {datas['people_per_apartment']}\n")
    if datas['objectif_type'] == 'habitants':
        answer += (f"  - Objectif de nombre d'habitants: {convert(str(datas['objectif']))}\n")
        answer += (f"  - Dépassement de l'objectif: {total_habitants - datas['objectif']} habitants\n")
    else:
        answer += (f"  - Objectif de coût de construction: {convert(str(datas['objectif']))} €\n")
        answer += (f"  - Dépassement de l'objectif: {total_construction_cost - datas['objectif']} €\n")
    if len(buildings) < 20:
        await send_long_message(ctx, answer)
    else:
        with open("construction_immeuble.txt", "w") as f:
            f.write(answer)
        await ctx.send(file=discord.File("construction_immeuble.txt"))
        os.remove("construction_immeuble.txt")


@bot.command()
async def give(ctx, user: discord.Member, amount: Union[int, str]):

    author = ctx.author

    sender_balance = get_balance(author.id)
    if sender_balance is None:
        sender_balance = 0
        
    if not amount_converter(amount, sender_balance):
        embed = discord.Embed(
            title="Erreur de donation",
            description=":moneybag: Le montant spécifié est invalide.",
            color=error_color_int
            )
        await ctx.send(embed=embed)
        return

    payment_amount = amount_converter(amount, sender_balance)

    if not has_enough_balance(author.id, payment_amount):
        print(sender_balance, payment_amount)
        embed = discord.Embed(
            title="Erreur de donation",
            description=f":moneybag: L'utilisateur {ctx.author.mention} n'a pas assez d'argent.",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return

    # Vérifier si l'utilisateur destinataire existe dans la base de données
    cur.execute("SELECT balance FROM inventory WHERE player_id = ?", (str(user.id),))
    recipient_balance = cur.fetchone()
    if recipient_balance is None:
        cur.execute("INSERT INTO inventory (player_id, balance) VALUES (?, ?)", (user.id, 0))

    # Effectuer la transaction en mettant à jour les données dans la base de données
    cur.execute("UPDATE inventory SET balance = balance + ? WHERE player_id = ?", (payment_amount, str(user.id)))
    cur.execute("UPDATE inventory SET balance = balance - ? WHERE player_id = ?", (payment_amount, str(author.id)))
    conn.commit()
    transa_embed = discord.Embed(
        title="Opération réussie",
        description=f":moneybag: **{convert(str(payment_amount))}** ont été donnés à l'utilisateur {user.mention}.",
        color=money_color_int
    )

    await eco_logger('M1', payment_amount, ctx.author, user)
    await ctx.send(embed=transa_embed)


@bot.command()
async def remove_money(ctx, user: discord.Member, amount: Union[int, str]):
    if not is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return
        
    balance = get_balance(user.id)
    if balance is None:
        balance = 0
    
    if not amount_converter(amount, balance):
        embed = discord.Embed(
            title="Erreur de retrait d'argent",
            description=":moneybag: Le montant spécifié est invalide.",
            color=error_color_int
            )
        await ctx.send(embed=embed)
        return

    payment_amount = amount_converter(amount, balance)
    if not has_enough_balance(user.id, payment_amount):
        embed = discord.Embed(
            title="Erreur de retrait d'argent",
            description=f":moneybag: L'utilisateur {user.name} n'a pas assez d'argent.",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return

    cur.execute("UPDATE inventory SET balance = balance - ? WHERE player_id = ?", (payment_amount, user.id))
    conn.commit()

    embed = discord.Embed(
        title="Opération réussie",
        description=f":moneybag: **{convert(str(payment_amount))}** ont été retirés de la réserve d'argent de l'utilisateur {user.name}.",
        color=money_color_int
    )
    await eco_logger('M5', payment_amount, user, ctx.author)
    await ctx.send(embed=embed)


@bot.command()
async def remove_pp(ctx, user: discord.Member, amount: Union[int, str]):
    if not is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return

    points = get_points(user.id, 1)
    if not amount_converter(amount, points):
        embed = discord.Embed(
            title="Erreur de retrait de points",
            description=":blue_circle: Le montant spécifié est invalide.",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return

    payment_amount = amount_converter(amount, points)

    if not has_enough_points(user.id, payment_amount, 1):
        embed = discord.Embed(
            title="Erreur de retrait de points",
            description=f":blue_circle: L'utilisateur {user.name} n'a pas assez de points.",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return

    take_points_func(user.id, payment_amount, 1)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":blue_circle: **{payment_amount}** ont été retirés des points de l'utilisateur {user.name}.",
        color=p_points_color_int
    )
    await eco_logger('P4', payment_amount, user, ctx.author, 1)
    await ctx.send(embed=embed)


@bot.command()
async def remove_pd(ctx, user: discord.Member, amount: Union[int, str]):
    if not is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return

    points = get_points(user.id, 2)
    if not amount_converter(amount, points):
        embed = discord.Embed(
            title="Erreur de retrait de points",
            description=":purple_circle: Le montant spécifié est invalide.",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return

    payment_amount = amount_converter(amount, points)

    if not has_enough_points(user.id, payment_amount, 2):
        embed = discord.Embed(
            title="Erreur de retrait de points",
            description=f":purple_circle: L'utilisateur {user.name} n'a pas assez de points.",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return

    take_points_func(user.id, payment_amount, 2)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":purple_circle: **{payment_amount}** ont été retirés des points de l'utilisateur {user.name}.",
        color=d_points_color_int
    )
    await eco_logger('P4', payment_amount, user, ctx.author, 2)
    await ctx.send(embed=embed)

@bot.command()
async def bal(ctx, user: discord.Member=None):
    if user is None:
        user = ctx.author
    balance = get_balance(str(user.id))
    if balance == 0:
        embed = discord.Embed(title=":moneybag: Cet utilisateur n'a pas d'argent", color=money_color_int)
    else:
        embed = discord.Embed(title=f"Balance de {user.name}", description=f":moneybag: L'utilisateur {user.name} a **{convert(str(balance))} d'argent**.", color=money_color_int)
        embed.set_footer(text=f"Classement: {get_leads(1, user.id)}")
    await ctx.send(embed=embed)


@bot.command()
async def points_p(ctx, user: discord.Member=None):
    if user is None:
        user = ctx.author
    balance = get_points(str(user.id), 1)
    if balance == 0:
        embed = discord.Embed(title=":blue_circle: Cet utilisateur n'a pas de points politiques.", color=p_points_color_int)
    else:
        embed = discord.Embed(title=f"Nombre de points politiques de {user.name}", description=f":blue_circle: L'utilisateur {user.name} a **{balance} points politiques**.", color=p_points_color_int)
        embed.set_footer(text=f"Classement: {get_leads(2, user.id)}")
    await ctx.send(embed=embed)

@bot.command()
async def points_d(ctx, user: discord.Member=None):
    if user is None:
        user = ctx.author
    balance = get_points(str(user.id), 2)
    if balance == 0:
        embed = discord.Embed(title=":purple_circle: Cet utilisateur n'a pas de points diplomatiques.", color=d_points_color_int)
    else:
        embed = discord.Embed(title=f"Nombre de points diplomatiques de {user.name}", description=f":purple_circle: L'utilisateur {user.name} a **{balance} points diplomatiques**.", color=d_points_color_int)
        embed.set_footer(text=f"Classement: {get_leads(3, user.id)}")
    await ctx.send(embed=embed)


@bot.command()
async def set_money(ctx, user: discord.Member, amount: int):
    if not is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return
    cur.execute("SELECT balance FROM inventory WHERE player_id = ?", (user.id,))
    result = cur.fetchone()

    if result is None:
        # L'utilisateur n'existe pas dans la base de données, l'ajouter avec le montant spécifié
        cur.execute("INSERT INTO inventory (player_id, balance) VALUES (?, ?)", (user.id, amount))
    else:
        # Mettre à jour le montant d'argent de l'utilisateur existant
        cur.execute("UPDATE inventory SET balance = ? WHERE player_id = ?", (amount, user.id))

    conn.commit()

    embed = discord.Embed(
        title="Opération réussie",
        description=f":moneybag: **{convert(str(amount))}** dollars ont été définis pour l'utilisateur {user.name}.",
        color=money_color_int
    )
    await eco_logger('M3', amount, user, ctx.author)
    await ctx.send(embed=embed)


@bot.command()
async def set_pp(ctx, user: discord.Member, amount: int):
    if not is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return

    cur.execute("SELECT pol_points FROM inventory WHERE player_id = ?", (user.id,))
    result = cur.fetchone()

    if result is None:
        # L'utilisateur n'existe pas dans la base de données, l'ajouter avec le montant spécifié
        cur.execute("INSERT INTO inventory (player_id, pol_points) VALUES (?, ?)", (user.id, amount))
    else:
        # Mettre à jour le montant de points de l'utilisateur existant
        cur.execute("UPDATE inventory SET pol_points = ? WHERE player_id = ?", (amount, user.id))

    conn.commit()

    embed = discord.Embed(
        title="Opération réussie",
        description=f":blue_circle: **{amount}** points politiques ont été définis pour l'utilisateur {user.name}.",
        color=p_points_color_int
    )
    await eco_logger('P2', amount, user, ctx.author, 1)
    await ctx.send(embed=embed)

@bot.command()
async def set_pd(ctx, user: discord.Member, amount: int):
    if not is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return

    cur.execute("SELECT pol_points FROM inventory WHERE player_id = ?", (user.id,))
    result = cur.fetchone()

    if result is None:
        # L'utilisateur n'existe pas dans la base de données, l'ajouter avec le montant spécifié
        cur.execute("INSERT INTO inventory (player_id, diplo_points) VALUES (?, ?)", (user.id, amount))
    else:
        # Mettre à jour le montant de points de l'utilisateur existant
        cur.execute("UPDATE inventory SET diplo_points = ? WHERE player_id = ?", (amount, user.id))

    conn.commit()

    embed = discord.Embed(
        title="Opération réussie",
        description=f":purple_circle: **{amount}** points diplomatiques ont été définis pour l'utilisateur {user.name}.",
        color=d_points_color_int
    )
    await eco_logger('P2', amount, user, ctx.author, 2)
    await ctx.send(embed=embed)


@bot.command()
async def add_money(ctx, user: discord.Member, amount: int):
    if not is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return
    
    give_money(str(user.id), amount)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":moneybag: **{convert(str(amount))}** ont été ajoutés à l'utilisateur {user.name}.",
        color=money_color_int
    )
    await eco_logger('M2', amount, user, ctx.author)
    await ctx.send(embed=embed)


@bot.command()
async def add_pp(ctx, user: discord.Member, amount: int):
    if not is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return

    give_points(str(user.id), amount, 1)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":blue_circle: **{amount}** ont été ajoutés à l'utilisateur {user.name}.",
        color=p_points_color_int
    )
    await eco_logger('P1', amount, user, ctx.author, 1)
    await ctx.send(embed=embed)

@bot.command()
async def add_pd(ctx, user: discord.Member, amount: int):
    if not is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return

    give_points(str(user.id), amount, 2)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":purple_circle: **{amount}** ont été ajoutés à l'utilisateur {user.name}.",
        color=d_points_color_int
    )
    await eco_logger('P1', amount, user, ctx.author, 2)
    await ctx.send(embed=embed)

@bot.command()
async def pay(ctx, amount: Union[int, str]):
    user = ctx.author
    balance = get_balance(str(user.id))
    

    if not amount_converter(amount, balance):
        embed = discord.Embed(
            title="Erreur de retrait d'argent",
            description=":moneybag: Le montant spécifié est invalide.",
            color=error_color_int
            )
        await ctx.send(embed=embed)
        return

    payment_amount = amount_converter(amount, balance)
    
    if not has_enough_balance(user.id, payment_amount):
        embed = discord.Embed(
            title="Erreur de paiement",
            description=f":moneybag: Vous n'avez pas assez d'argent pour effectuer cette transaction.",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return
    
    take_money_func(user.id, payment_amount)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":moneybag: **{convert(str(payment_amount))}** ont été payés au bot.",
        color=money_color_int
    )
    await eco_logger('M4', payment_amount, ctx.author)
    await ctx.send(embed=embed)

@bot.command()
async def use_pp(ctx, amount: int=1):
    user = ctx.author
    points = get_points(user.id, 1)
    if not amount_converter(amount, points):
        embed = discord.Embed(
            title="Erreur d'utilisation des points",
            description=":blue_circle: Le montant spécifié est invalide.",
            color=error_color_int
            )
        await ctx.send(embed=embed)
        return

    payment_amount = amount_converter(amount, points)

    if not has_enough_points(user.id, amount, 1):
        embed = discord.Embed(
            title="Erreur d'utilisation des points",
            description=f":blue_circle: L'utilisateur {ctx.author.mention} n'a pas assez de points politiques.",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return
    take_points_func(user.id, payment_amount, 1)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":blue_circle: **{amount}** points politiques ont été utilisés par {user.name}.",
        color=p_points_color_int
    )
    await eco_logger('P3', amount, ctx.author, None, 1)
    await ctx.send(embed=embed)

@bot.command()
async def use_pd(ctx, amount: int=1):
    user = ctx.author
    points = get_points(user.id, 2)
    if not amount_converter(amount, points):
        embed = discord.Embed(
            title="Erreur d'utilisation des points",
            description=":purple_circle: Le montant spécifié est invalide.",
            color=error_color_int
            )
        await ctx.send(embed=embed)
        return

    payment_amount = amount_converter(amount, points)

    if not has_enough_points(user.id, amount, 2):
        embed = discord.Embed(
            title="Erreur d'utilisation des points",
            description=f":purple_circle: L'utilisateur {ctx.author.mention} n'a pas assez de points diplomatiques.",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return
    take_points_func(user.id, payment_amount, 2)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":purple_circle: **{amount}** points diplomatiques ont été utilisés par {user.name}.",
        color=d_points_color_int
    )
    await eco_logger('P3', amount, ctx.author, None, 2)
    await ctx.send(embed=embed)


@bot.command()
async def lead_eco(ctx):
    cur.execute("SELECT player_id, balance FROM inventory ORDER BY balance DESC LIMIT 10")
    leaderboard = cur.fetchall()

    embed = discord.Embed(title="Classement des pays les plus riches :", color=money_color_int)
    for i, (user_id, balance) in enumerate(leaderboard, 1):
        user = ctx.guild.get_member(int(user_id))
        if user:
            username = user.name + f" - {str(user_id)}"
        else:
            username = str(user_id) + " - Non identifié"
        embed.add_field(name=f"{i}. {username}", value=f":moneybag: **{convert(str(balance))}** argent", inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def lead_pp(ctx):
    cur.execute("SELECT player_id, pol_points FROM inventory ORDER BY pol_points DESC LIMIT 10")
    leaderboard = cur.fetchall()

    embed = discord.Embed(title="Classement des pays avec le plus de pp :", color=p_points_color_int)
    for i, (user_id, points) in enumerate(leaderboard, 1):
        user = ctx.guild.get_member(int(user_id))
        if user:
            username = user.name + f" - {str(user_id)}"
        else:
            username = str(user_id) + " - Non identifié"
        embed.add_field(name=f"{i}. {username}", value=f":blue_circle: **{points}** points", inline=False)

    await ctx.send(embed=embed)


@bot.command()
async def lead_pd(ctx):
    cur.execute("SELECT player_id, diplo_points FROM inventory ORDER BY diplo_points DESC LIMIT 10")
    leaderboard = cur.fetchall()

    embed = discord.Embed(title="Classement des pays avec le plus de pp :", color=d_points_color_int)
    for i, (user_id, points) in enumerate(leaderboard, 1):
        user = ctx.guild.get_member(int(user_id))
        if user:
            username = user.name + f" - {str(user_id)}"
        else:
            username = str(user_id) + " - Non identifié"
        embed.add_field(name=f"{i}. {username}", value=f":purple_circle: **{points}** points diplomatiques", inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def lead(ctx):
    async def get_leaderboard(offset=0, limit=10):
        cur.execute(f"SELECT player_id, balance, pol_points, diplo_points FROM inventory ORDER BY (balance + pol_points + diplo_points) DESC LIMIT {limit} OFFSET {offset}")
        return cur.fetchall()

    async def create_lead_embed(leaderboard, offset):
        embed = discord.Embed(
            title=f"Classement des pays (de {offset + 1} à {offset + len(leaderboard)})", 
            color=0x00ff00
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
                inline=False
            )
        return embed

    leaderboard = await get_leaderboard()

    if len(leaderboard) == 0:
        return await ctx.send("Le classement est vide.")

    view = View()
    max_entries = 100  # Limite maximum du nombre d'utilisateurs à afficher

    async def next_callback(interaction):
        nonlocal offset
        offset += 10
        leaderboard = await get_leaderboard(offset)
        if len(leaderboard) > 0:
            embed = await create_lead_embed(leaderboard, offset)
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            offset -= 10

    async def prev_callback(interaction):
        nonlocal offset
        if offset > 0:
            offset -= 10
            leaderboard = await get_leaderboard(offset)
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
    app_type = find_app_type(appareil)
    if app_type is None:
        await ctx.send("Appareil non trouvé.")
        return

    # Récupérer les données de production pour chaque niveau
    prod_datas = []
    for i in range(1, 8):
        prod_datas.append(production_data[f"{i}"]["production_mensuelle"][app_type][appareil])

    # Construire la chaîne de caractères pour la production mensuelle
    production_info = ""
    for i in range(1, 8):
        production_info += f"Niveau {i}: {convert(str(prod_datas[i-1]))}\n"

    # Créer l'embed avec les informations de l'appareil
    embed = discord.Embed(
        title=f"Information sur l'appareil {appareil}",
        description=f"Type: {app_type}\nProduction mensuelle par niveau d'usine:\n{production_info}",
        color=0x00ff00
    )

    # Envoyer l'embed
    await ctx.send(embed=embed)


@bot.command()
async def production_time(ctx, app, qty, app_type=None, user:discord.Member=None):
    if find_app_type(app) is None:
        await ctx.send("Appareil non trouvé.")
        return
    app_type = find_app_type(app)
    if not user:
        user = ctx.author
    await ctx.send(calculer_temps_production(user.id, app.lower(), qty, app_type))

@bot.command()
async def list_apparels(ctx):
    app_types = ["terrestre", "navale", "aerienne", "explosif"]
    apparels = []

    for app_type in app_types:
        for apparel in production_data["7"]["production_mensuelle"][app_type]:
            apparels.append(apparel)
    await send_long_message(ctx, "\n- ".join(apparels))

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
            await ctx.send("Le résultat est trop long, voici le fichier contenant l'output :", 
                file=discord.File(io.StringIO(output), filename="output.txt"))
        else:
            await ctx.send(f'**Résultat de l\'exécution :**\n```python\n{output}\n```')
    
    except Exception as e:
        await ctx.send(f'**Une erreur est survenue lors de l\'exécution du code :**\n```python\n{e}\n```')


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
        amount: int = commands.parameter(description="Nombre d'usines à construire (doit être un entier positif)."),
        lvl = commands.parameter(description="Niveau des usines à construire (indique le coût de construction par usine).")
    ) -> None:
    user = ctx.author
    balance = get_balance(str(user.id))

    if not amount_converter(amount, balance):
        embed = discord.Embed(
            title="Erreur de paiement",
            description=":moneybag: Le montant spécifié est invalide.",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return

    payment_amount = amount * int(production_data[str(lvl)]["cout_construction"])
    
    if not has_enough_balance(user.id, payment_amount):
        embed = discord.Embed(
            title="Erreur de paiement",
            description=f":moneybag: Vous n'avez pas assez d'argent pour effectuer cette transaction.\nMontant demandé : {payment_amount}. | Vous possédez : {balance}",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return
    
    take_money_func(user.id, payment_amount)
    give_usine(user.id, amount, lvl, 0)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":factory: Vos {amount} usines de niveau {lvl} auront coûtés **{convert(str(payment_amount))}** et ont été payés au bot.",
        color=money_color_int
    )
    await ctx.send(embed=embed)

@bot.command()
async def sell_batiment(ctx, bat_type, amount:int, lvl):
    user = ctx.author
    balance = get_usine(user.id, lvl, 0)
    if balance is None:
        balance = 0
    
    if not amount_converter(amount, balance):
        embed = discord.Embed(
            title="Erreur de retrait d'usine",
            description=":factory: Le montant spécifié est invalide.",
            color=error_color_int
            )
        await ctx.send(embed=embed)
        return
    payment_amount = amount * int(production_data[str(lvl)]["cout_construction"])
    
    if not has_enough_bats(user.id, amount, lvl, 0):
        embed = discord.Embed(
            title="Erreur de paiement",
            description=f":factory: Vous n'avez pas assez d'usines pour effectuer cette transaction.\nMontant demandé : {amount}. | Vous possédez : {balance}",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return
    
    give_money(user.id, payment_amount)
    remove_usine_func(user.id, amount, lvl, 0)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":factory: Vos {amount} usines de niveau {lvl} vous ont rapporté **{convert(str(payment_amount))}** et ont été ajouté à votre solde.",
        color=money_color_int
    )
    await ctx.send(embed=embed)


@bot.command()
async def usines(ctx, type, user: discord.Member=None):
    if user is None:
        user = ctx.author
    types = [1, 2, 3, 4, 5, 6, 7]
    if (type.lower() != "all") and (int(type) not in types):
        return await ctx.send("Lol non")
    if type.lower() == "all":
        embed = discord.Embed(title=f"Usines de {user.name}", description="")
        for i in types:
            current_us = get_usine(user.id, i, 0)
            embed.description += f"Type {i} : {current_us}\n"
    else:
        type = int(type)
        embed = discord.Embed(title=f"Usines de type {type} de {user.name}", description=f"L'utilisateur a **{str(get_usine(user.id, type, 0))}** usines de type {type}.")
    await ctx.send(embed=embed)


@bot.command()
async def remove_usine(ctx, user: discord.Member, amount: Union[int, str], lvl:int):
    if not is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return
        
    balance = get_usine(user.id, lvl, 0)
    if balance is None:
        balance = 0
    
    if not amount_converter(amount, balance):
        embed = discord.Embed(
            title="Erreur de retrait d'usine",
            description=":factory: Le montant spécifié est invalide.",
            color=error_color_int
            )
        await ctx.send(embed=embed)
        return

    payment_amount = amount_converter(amount, balance)
    if not has_enough_balance(user.id, payment_amount):
        embed = discord.Embed(
            title="Erreur de retrait d'argent",
            description=f":factory: L'utilisateur {user.name} n'a pas assez d'usines.",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return
    remove_usine_func(user.id, amount, lvl, 0)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":factory: **{convert(str(payment_amount))}** ont été retirés de l'inventaire d'usines de niveau {lvl} de l'utilisateur {user.name}.",
        color=money_color_int
    )
    await ctx.send(embed=embed)


@bot.command()
async def set_usine(ctx, user: discord.Member, amount: int, lvl:int):
    if not is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return

    set_usine_func(user.id, amount, lvl, 0)

    embed = discord.Embed(
        title="Opération réussie",
        description=f":factory: **{convert(str(amount))}** usines de niveau {lvl} ont été définis pour l'utilisateur {user.name}.",
        color=money_color_int
    )
    await ctx.send(embed=embed)


@bot.command()
async def set_base(ctx, bat_type:int, user: discord.Member, amount: int, lvl:int):
    if not is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return
    set_usine_func(user.id, amount, lvl, bat_type)
    bat_cat = "bases" if bat_type < 4 else "ecoles"
    bat_cat += "_militaires"
    bat_cat = base_data[bat_cat][f"{bat_types[bat_type][0]}{lvl}"]['type']
    embed = discord.Embed(
        title="Opération réussie",
        description=f":factory: **{convert(str(amount))}** {bat_cat} de niveau {lvl} ont été définis pour l'utilisateur {user.name}.",
        color=money_color_int
    )
    await ctx.send(embed=embed)


@bot.command()
async def batiments(ctx, bat_type:int, type, user: discord.Member=None):
    if user is None:
        user = ctx.author
    if int(bat_type) >= len(bat_types):
        return await ctx.send("Type de bâtiment invalide.")
    bat_name, max_lvl = bat_types[bat_type]  # Récupère le niveau maximum en fonction du type de bâtiment
    if type.lower() != "all":
        try:
            type = int(type)
        except ValueError:
            return await ctx.send("Veuillez fournir un niveau valide ou 'all'.")

        if not is_valid_lvl(type, max_lvl):
            return await ctx.send(f"Le niveau pour {bat_name} doit être entre 1 et {max_lvl}.")

    if type.lower() == "all":
        embed = discord.Embed(title=f"{bat_name}s de {user.name}", description="")
        for i in range(1, max_lvl + 1):  # On parcourt les niveaux du type de bâtiment
            embed.description += f"Niveau {i} : {str(get_usine(user.id, i, bat_type))}\n"
    else:
        embed = discord.Embed(
            title=f"{bat_name}s de type {type} de {user.name}",
            description=f"L'utilisateur a **{str(get_usine(user.id, type, bat_type))}** {bat_name}s de niveau {type}."
        )
    await ctx.send(embed=embed)

@bot.command()
async def remove_bat(ctx, bat_type:int, user: discord.Member, amount: Union[int, str], lvl:int):
    if not is_authorized(ctx):
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description="Il vous faut être staff",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return
        
    balance = get_usine(user.id, lvl, bat_type)
    if balance is None:
        balance = 0
    
    if not amount_converter(amount, balance):
        embed = discord.Embed(
            title="Erreur de retrait de batiments",
            description=":factory: Le montant spécifié est invalide.",
            color=error_color_int
            )
        await ctx.send(embed=embed)
        return

    payment_amount = amount_converter(amount, balance)
    if not has_enough_balance(user.id, payment_amount):
        embed = discord.Embed(
            title="Erreur de retrait d'argent",
            description=f":factory: L'utilisateur {user.name} n'a pas assez d'usines.",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return
    remove_usine_func(user.id, amount, lvl, 0)
    embed = discord.Embed(
        title="Opération réussie",
        description=f":factory: **{convert(str(payment_amount))}** ont été retirés de l'inventaire d'usines de niveau {lvl} de l'utilisateur {user.name}.",
        color=money_color_int
    )
    await ctx.send(embed=embed)


@bot.command()
async def del_betw(ctx, base_message: discord.Message, reach_message: discord.Message):
    if not ctx.author.id in bi_admins_id:
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description=f"{Erreurs['Erreur ']}",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return
    if not reach_message.channel.id == ctx.channel.id or not base_message.channel.id == ctx.channel.id:
        await ctx.send("Erreur : Vous n'êtes pas dans le salon des messages à supprimer") 
    deleted = await ctx.channel.purge(limit=1000, before=base_message, after=reach_message)
    await ctx.channel.send(f"J'ai supprimé {len(deleted)} message(s)")


@bot.command()
async def del_til(ctx, reach_message: discord.Message):
    if not ctx.author.id in bi_admins_id:
        embed = discord.Embed(
            title="Vous n'êtes pas autorisé à effectuer cette commande.",
            description=f"{Erreurs['Erreur ']}",
            color=error_color_int
        )
        await ctx.send(embed=embed)
        return
    if not reach_message.channel.id == ctx.channel.id:
        await ctx.send("Erreur : Vous n'êtes pas dans le salon des messages à supprimer") 
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
        user: discord.Member = commands.parameter(description="ID ou mention du membre auquel attribuer le pays"),
        country_flag = commands.parameter(description="Emoji représentant le drapeau du pays"),
        country_name = commands.parameter(description="Nom du pays sans espaces. Remplacez les espaces par des underscores `_`."),
        continent: Union[discord.CategoryChannel, str] = commands.parameter(description="ID ou nom du continent (Europe, Amérique, Asie, etc.). Accents et majuscules autorisés.")
    ) -> None:
    continents = {
        "europe": 955479237001891870,
        "amerique": 952314456870907934,
        "asie": 1243672298381381816,
        "afrique": 961678827933794314,
        "oceanie": 992368253580087377,
        "moyen-orient": 951163668102520833
    }
    player_role = await get_player_role(ctx)
    non_player_role = await get_non_player_role(ctx)
    if not is_authorized(ctx):
        return await ctx.send(embed=get_auth_embed())
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
    await channel.set_permissions(ctx.guild.default_role, manage_webhooks=False, view_channel=True, read_messages=True, send_messages=False)
    await channel.set_permissions(role, manage_webhooks=True, view_channel=True, read_messages=True, send_messages=True, manage_messages=True)
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
        country_role:discord.Role=commands.parameter(description="ID ou @ du rôle du pays"), 
        service_icon=commands.parameter(description="l'Emoji du drapeau du pays"), 
        secret_name=commands.parameter(description="Nom du service secret sans espace.")
    ) -> None:
    secret_category = discord.utils.get(ctx.guild.categories, id=1269295981183369279)
    staff_role = ctx.guild.get_role(usefull_role_ids_dic["staff"])
    if not is_authorized(ctx):
        return await ctx.send(embed=get_auth_embed())
    secret_name = secret_name.replace("_", " ")
    secret_name = convert_country_name(secret_name)
    channel_name = f"「{service_icon}」{secret_name}"
    channel = await secret_category.create_text_channel(channel_name)
    await channel.set_permissions(ctx.guild.default_role, manage_webhooks=False, view_channel=False, read_messages=False, send_messages=False)
    await channel.set_permissions(country_role, manage_webhooks=True, view_channel=True, read_messages=True, send_messages=True, manage_messages=True)
    await channel.set_permissions(staff_role, manage_webhooks=True, view_channel=True, read_messages=True, send_messages=True, manage_messages=True)
    await channel.send(f"Bienvenue dans les services {secret_name} du pays {country_role.name} !")
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
        emoji: discord.Emoji = commands.parameter(description="L'emoji à reformater (mention ou ID)"),
        new_name: str = commands.parameter(description="Nouveau nom de l'emoji. Ajoute automatiquement le préfixe `NE_` si absent."),
        del_bg: bool = commands.parameter(description="Optionnel. Si True, enlève l'arrière-plan de l'emoji.")
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
            emoji = await ctx.guild.create_custom_emoji(image=image_data, name=new_name, reason=f"Reformatage de l'emoji {emoji.name}")
    else:
        await emoji.edit(name=new_name, reason=f"Reformatage de l'emoji {emoji.name}")
    
    await ctx.send(f"{ctx.message.author.mention} J'ai reformatté l'emoji en <:{new_name}:{emoji.id}> pour le serveur.")

@bot.command()
async def cat_syncer(ctx, cat:discord.CategoryChannel):
    if ctx.author.id not in bi_admins_id:
        return await ctx.send('Non.')
    for i in cat.channels:
        if i.overwrites == cat.overwrites:
            continue
        await i.edit(sync_permissions=True)
        await asyncio.sleep(2)
    await ctx.send("Fait")

@bot.command()
async def sync_channels(ctx, chan_to_sync:Union[discord.TextChannel, discord.VoiceChannel, discord.ForumChannel, discord.StageChannel], model_chan:Union[discord.TextChannel, discord.VoiceChannel, discord.ForumChannel, discord.StageChannel]):
    if ctx.author.id not in bi_admins_id:
        return await ctx.send('Non.')
    new_permissions = model_chan.overwrites
    await chan_to_sync.edit(overwrites=new_permissions)
    await ctx.send("Fait")

@bot.command()
async def sync_cats(ctx, cat_to_sync:discord.CategoryChannel, model_cat:discord.CategoryChannel):
    if ctx.author.id not in bi_admins_id:
        return await ctx.send('Non.')
    await cat_to_sync.edit(overwrites=model_cat.overwrites)
    await cat_syncer(ctx, cat_to_sync)
    await ctx.send("Fait")
    
@bot.command()
async def reformat_rp_channels(ctx):
    if ctx.author.id not in bi_admins_id:
        return await ctx.send('Non.')
    for continent_cat in continents_dict.values():
        continent_cat = discord.utils.get(ctx.guild.categories, id=int(continent_cat))
        for channel in continent_cat.channels:
            new_name = convert_country_name_channel(channel.name)
            if new_name == channel.name:
                continue
            await ctx.send(f"{channel.name} => {new_name}")
            #await channel.edit(name=new_name)
    await ctx.send("Fait")
    

@bot.command()
async def send_rules(ctx, webhook_url: str):
    if ctx.author.id not in bi_admins_id:
        return await ctx.send('Non.')
    
    rules = {
        "hrp": "hrp.json",
        "rp": "rp.json",
        "military": "military.json",
        "territorial": "territorial.json"
    }
    
    rules_webhooks = {}
    summary_links = []
    summary_embeds = []
    rules_titles = {}

    # Lire et parser chaque fichier de règles
    for rule in rules.values():
        with open(f"rules/{rule}", "r") as file:
            r_file = file.read()
            rules_webhooks[rule] = list(parse_embed_json(r_file))  # Convertir en liste d'embeds
            rules_titles[rule] = json.loads(r_file)['content']
            

    # Lire les embeds pour le résumé
    with open("rules/summary.json", "r") as file:
        summary_embeds = list(parse_embed_json(file.read()))

    # Utiliser la session aiohttp pour envoyer les webhooks
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(webhook_url, session=session)

        # Envoyer les règles et récupérer les liens d'embed
        for rule_title, rule_embeds in zip(rules_titles.values(), rules_webhooks.values()):
            await webhook.send(content=rule_title, username=bot.user.name, avatar_url=bot.user.avatar.url, wait=True)
            embeds_to_send = []
            for embed in rule_embeds:
                embeds_to_send.append(await webhook.send(embed=embed, username=bot.user.name, avatar_url=bot.user.avatar.url, wait=True))
                #await asyncio.sleep(1)  # Si tu veux vraiment un délai
            summary_links.append(embeds_to_send[0].jump_url)
            await webhook.send(content="``` ```", username=bot.user.name, avatar_url=bot.user.avatar.url)

        # Envoyer les embeds du résumé avec les URLs ajoutées

        await webhook.send(embed=summary_embeds[0], username=bot.user.name, avatar_url=bot.user.avatar.url)
        for i, sum_embed in enumerate(summary_embeds[1:]):
            if i < len(summary_links):
                sum_embed.url = summary_links[i]  # Ajouter les URLs récupérées précédemment

            await webhook.send(embed=sum_embed, username=bot.user.name, avatar_url=bot.user.avatar.url)
            await asyncio.sleep(1)  # Si nécessaire
    announce_channel = discord.utils.get(ctx.guild.channels, id=873645600183287859)
    with open("rules/announcing.json", "r") as file:
        announce_embed = embed = discord.Embed().from_dict(json.loads(file.read()))
    await announce_channel.send(embed=announce_embed)
    await announce_channel.send("@everyone")
    await ctx.message.delete()
    
# @bot.command()
# async def get_json(ctx, query, player_id1, player_id2=None):
#     if ctx.author.id not in bi_admins_id:
#         return await ctx.send('Non.')
#     get_sql_to_json(player_id1, player_id2)
#     json_file = json.load(open('output.json', 'r'))
#     context = get_global_context()
#     groq_output = respond(query)
#     await send_long_message(ctx, f"groq_output : {groq_output}")
    
@bot.command()
async def groq_chat(ctx, *, message):
    global last_groq_query_time
    if last_groq_query_time:
        if datetime.now(timezone.utc) - last_groq_query_time < timedelta(seconds=180) and ctx.author.id not in bi_admins_id:
            return await ctx.send("Veuillez attendre 3 minutes entre chaque requête.")
    query_type = 0
    if ctx.author.id not in bi_admins_id:
        query_type = 0
    else:
        query_type = -1
    groq_output = respond(message, query_type)
    #return
    last_groq_query_time = datetime.now(timezone.utc)
    return await send_long_message(ctx, f"{groq_output}")

