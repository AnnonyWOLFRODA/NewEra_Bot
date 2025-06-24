"""
Construction utilities for NEBot.
Contains functions for construction cost and area calculations.
"""

def calculate_total_area(taille_moyenne, nombre_logements):
    return taille_moyenne * nombre_logements

def calculate_construction_cost(datas, total_area, building):
    mur_price = datas.get('wall_prices', {}).get(datas.get('type_murs'), (0,))[0]
    mur_cost = mur_price * total_area
    etages = building.get('nombre_etages', 1)
    prix_fonda = datas.get('prix_fondations', 0) + (etages * 50)
    fondations_cost = prix_fonda * (building.get('surface_net', 0) * building.get('profondeur_fondation', 0))
    construction_cost = total_area * datas.get('prix_moyen', 0) + mur_cost + fondations_cost
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