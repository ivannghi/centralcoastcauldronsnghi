import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * from global_inventory"))
        first_row = result.first()
        total_red_ml = first_row.num_red_ml
        total_blue_ml = first_row.num_blue_ml
        total_green_ml = first_row.num_green.ml
        total_red_potions = first_row.num_red_potions
        total_blue_potions = first_row.num_blue_potions
        total_green_potions = first_row.num_green_potions


        for potion in potions_delivered:
            if potion.potion_type == [100,0,0,0] and total_red_ml >= (100 * potion.quantity):
                total_red_ml -= (100 * potion.quantity)
                total_red_potions += potion.quantity
                print(total_red_potions)
            elif potion.potion_type == [0,0,100,0] and total_blue_ml >= (100 * potion.quantity):
                total_blue_ml -= (100 * potion.quantity)
                total_blue_potions += potion.quantity    
            elif potion.potion_type == [0,100,0,0] and total_green_ml >= (100 * potion.quantity):
                total_green_ml -= (100 * potion.quantity)
                total_green_potions += potion.quantity

        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {total_red_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {total_red_potions}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = {total_blue_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = {total_blue_potions}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {total_green_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {total_green_potions}"))

    print(f"Potions Delivered: {potions_delivered}")
    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    bottle_list = []
    bought_red_count = 0
    bought_blue_count = 0
    bought_green_count = 0

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_blue_ml, num_green_ml from global_inventory"))
        first_row = result.first()
        total_red_ml = first_row.num_red_ml
        total_blue_ml = first_row.num_blue_ml
        total_green_ml = first_row.num_green_ml
        while total_red_ml >= 100:
            #mix potions of size ___ ml
            bought_red_count += 1
            total_red_ml -= 100
        while total_blue_ml >= 100:
            #mix potions of size ___ ml
            bought_blue_count += 1
            total_blue_ml -= 100
        while total_green_ml >= 100:
            #mix potions of size ___ ml
            bought_green_count += 1
            total_green_ml -= 100

    if bought_red_count > 0:
        bottle_list.append({
                "potion_type": [100, 0, 0, 0],
                "quantity": bought_red_count,
            })
    if bought_blue_count > 0:
        bottle_list.append({
                "potion_type": [0, 0, 100, 0],
                "quantity": bought_blue_count,
            })
    if bought_green_count > 0:
        bottle_list.append({
                "potion_type": [0, 100, 0, 0],
                "quantity": bought_green_count,
            })

    print(f"Bottle List: {bottle_list}")
    return bottle_list