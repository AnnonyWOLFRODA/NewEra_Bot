"""
Construction utilities for NEBot.
Contains functions for construction cost and area calculations.
"""


def calculate_total_area(taille_moyenne, nombre_logements):
    return taille_moyenne * nombre_logements


def calculate_construction_cost(datas, total_area, building):
    mur_price = datas.get("wall_prices", {}).get(datas.get("type_murs"), (0,))[0]
    mur_cost = mur_price * total_area
    etages = building.get("nombre_etages", 1)
    prix_fonda = datas.get("prix_fondations", 0) + (etages * 50)
    fondations_cost = prix_fonda * (
        building.get("surface_net", 0) * building.get("profondeur_fondation", 0)
    )
    construction_cost = (
        total_area * datas.get("prix_moyen", 0) + mur_cost + fondations_cost
    )
    return construction_cost


def get_people_per_apartment(taille_moyenne):
    surface_per_first_4 = 8
    surface_per_additional = 6
    initial_habitants = 4
    initial_surface = initial_habitants * surface_per_first_4
    if taille_moyenne >= initial_surface:
        remaining_surface = taille_moyenne - initial_surface
        additional_habitants = remaining_surface // surface_per_additional
        total_habitants = initial_habitants + additional_habitants
    else:
        total_habitants = taille_moyenne // surface_per_first_4
    return total_habitants


async def calculate_by_population(ctx, dUtils):
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

async def calculate_by_budget(ctx, dUtils):
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
