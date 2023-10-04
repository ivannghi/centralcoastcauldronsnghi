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
        total_red_potions = first_row.num_red_potions
        total_red_ml = first_row.num_red_ml
        for potion in potions_delivered:
            if potion.potion_type == [100,0,0,0] and total_red_ml >= (100 * potion.quantity):
                total_red_ml = total_red_ml - (100 * potion.quantity)
                total_red_potions = total_red_potions + potion.quantity

        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {total_red_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {total_red_potions}"))

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
    red_ml_potion_count = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml from global_inventory"))
        first_row = result.first()
        current_red_ml = first_row.num_red_ml
        while current_red_ml >= 100:
            #mix potions of size ___ ml
            red_ml_potion_count += 1
            current_red_ml -= 100

    if red_ml_potion_count >= 1:
        bottle_list.append({
                "potion_type": [100, 0, 0, 0],
                "quantity": red_ml_potion_count,
            })
    print(f"Bottle List: {bottle_list}")
    return bottle_list