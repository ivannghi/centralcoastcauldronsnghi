from operator import itemgetter
import random
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
        total_green_ml = first_row.num_green_ml
        # total_red_potions = first_row.num_red_potions
        # total_blue_potions = first_row.num_blue_potions
        # total_green_potions = first_row.num_green_potions


        for potion in potions_delivered:
            potion_red = potion.potion_type[0]
            potion_green = potion.potion_type[1]
            potion_blue = potion.potion_type[2]
            # potion_dark = potion.potion_type[3]

            if total_red_ml >= potion_red and total_green_ml >= potion_green and total_blue_ml >= potion_blue:
                total_red_ml -= potion_red
                total_green_ml -= potion_green
                total_blue_ml -= potion_blue

                connection.execute(
                    sqlalchemy.text("""
                                    UPDATE potions 
                                    SET inventory = inventory + :potion_quantity 
                                    WHERE red_ml = :potion_red
                                    AND green_ml = :potion_green
                                    AND blue_ml = :potion_blue
                                    """),
                                    [{"potion_quantity": potion.quantity, "potion_red": potion_red, "potion_green": potion_green, "potion_blue": potion_blue}]
                                    )


            # if potion.potion_type == [100,0,0,0] and total_red_ml >= (100 * potion.quantity):
            #     total_red_ml -= (100 * potion.quantity)
            #     total_red_potions += potion.quantity
            #     print(total_red_potions)
            # elif potion.potion_type == [0,0,100,0] and total_blue_ml >= (100 * potion.quantity):
            #     total_blue_ml -= (100 * potion.quantity)
            #     total_blue_potions += potion.quantity    
            # elif potion.potion_type == [0,100,0,0] and total_green_ml >= (100 * potion.quantity):
            #     total_green_ml -= (100 * potion.quantity)
            #     total_green_potions += potion.quantity

        # connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {total_red_ml}"))
        # connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = {total_blue_ml}"))
        # connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {total_green_ml}"))
        connection.execute(
            sqlalchemy.text("""
                            UPDATE global_inventory SET
                            num_red_ml = :total_red_ml,
                            num_green_ml = :total_green_ml,
                            num_blue_ml = :total_blue_ml
                            """),
                            [{"total_red_ml": total_red_ml, "total_green_ml": total_green_ml, "total_blue_ml": total_blue_ml}]
        )

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
    # bought_red_count = 0
    # bought_blue_count = 0
    # bought_green_count = 0

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_blue_ml, num_green_ml from global_inventory"))
        first_row = result.first()
        total_red_ml = first_row.num_red_ml
        total_blue_ml = first_row.num_blue_ml
        total_green_ml = first_row.num_green_ml

        to_bottle_list = []
        potions_result = connection.execute(sqlalchemy.text("SELECT red_ml, green_ml, blue_ml, inventory FROM potions"))
        potions_result_table = potions_result.fetchall()
        for potion in potions_result_table:
            to_bottle_list.append((potion.inventory, [potion.red_ml, potion.green_ml, potion.blue_ml, 0]))
        random.shuffle(to_bottle_list)
        to_bottle_list = sorted(to_bottle_list, key=itemgetter(0))
        print(f"Potion quantities: {to_bottle_list}")

        # while total_red_ml >= 100 or total_green_ml >= 100 or total_blue_ml >= 100:
        for pot in to_bottle_list:
            potion_type = pot[1]
            print(f"potion type: {potion_type}")
            print(f"red_ml: {total_red_ml}, green_ml: {total_green_ml}, blue_ml: {total_blue_ml}")

            if potion_type[0] <= total_red_ml and potion_type[1] <= total_green_ml and potion_type[2] <= total_blue_ml:
                list_of_ml_limiters = []
                if potion_type[0] > 0:
                    list_of_ml_limiters.append(total_red_ml//potion_type[0])
                if potion_type[1] > 0:
                    list_of_ml_limiters.append(total_green_ml//potion_type[1])
                if potion_type[2] > 0:
                    list_of_ml_limiters.append(total_blue_ml//potion_type[2])
                
                make_potions = min(list_of_ml_limiters)

                bottle_list.append({
                    "potion_type": potion_type,
                    "quantity": make_potions,
                })

                total_red_ml -= potion_type[0] * make_potions
                total_green_ml -= potion_type[1] * make_potions
                total_blue_ml -= potion_type[2] * make_potions

    print(f"Bottle List: {bottle_list}")
    return bottle_list