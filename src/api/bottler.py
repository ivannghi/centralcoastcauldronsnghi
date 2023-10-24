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
    print(potions_delivered)
    with db.engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text(
                """SELECT resource_id, SUM(change) as resource
                FROM resource_ledger_entry
                GROUP BY resource_id
                """))
        first_row = result.all()
        total_red_ml = 0
        total_green_ml = 0
        total_blue_ml = 0
        for resource in first_row:
            if resource[0] == "red":
                total_red_ml = resource[1]
            elif resource[0] == "green":
                total_green_ml = resource[1]
            elif resource[0] == "blue":
                total_blue_ml = resource[1]

        total_red_used = 0
        total_green_used = 0
        total_blue_used = 0
        # total_red_potions = first_row.num_red_potions
        # total_blue_potions = first_row.num_blue_potions
        # total_green_potions = first_row.num_green_potions


        for potion in potions_delivered:
            potion_red = potion.potion_type[0]
            potion_green = potion.potion_type[1]
            potion_blue = potion.potion_type[2]
            # potion_dark = potion.potion_type[3]

            if total_red_ml >= potion_red and total_green_ml >= potion_green and total_blue_ml >= potion_blue:
                total_red_used += potion_red * potion.quantity
                total_red_ml -= potion_red * potion.quantity
                total_green_used += potion_green * potion.quantity
                total_green_ml -= potion_green * potion.quantity
                total_blue_used += potion_blue * potion.quantity
                total_blue_ml -= potion_blue * potion.quantity

                potion_details = connection.execute(
                    sqlalchemy.text("""
                                    SELECT id, name
                                    FROM potions
                                    WHERE red_ml = :potion_red and
                                    green_ml = :potion_green and
                                    blue_ml = :potion_blue 
                                    """),
                                    [{"potion_red": potion_red, "potion_green": potion_green, "potion_blue": potion_blue}])
                potion_id_name = potion_details.fetchone()

                result = connection.execute(
                    sqlalchemy.text("""
                                    INSERT INTO transactions
                                    (description)
                                    VALUES
                                    ('Bottled ' || :potion_quantity || ' ' || :potion_name || '(s)')
                                    RETURNING id
                                    """),
                                    [{"potion_quantity": str(potion.quantity), "potion_name": str(potion_id_name[1])}])
                transaction_id = result.scalar_one()


                connection.execute(
                    sqlalchemy.text("""
                                    INSERT INTO potion_ledger_entry
                                    (potion_id, transaction_id, change)
                                    VALUES
                                    (:potion_id, :transaction_id, :potion_quantity)
                                    """),
                                    [{"potion_id": potion_id_name[0], "transaction_id": transaction_id, "potion_quantity": potion.quantity}])


        if total_red_used > 0:
            connection.execute(
                sqlalchemy.text("""
                                INSERT INTO resource_ledger_entry
                                (resource_id, transaction_id, change)
                                VALUES
                                ('red', :transaction_id, :total_red_used)
                                """),
                                [{"transaction_id": transaction_id, "total_red_used": -total_red_used}])
            
        if total_green_used > 0:
            connection.execute(
                sqlalchemy.text("""
                                INSERT INTO resource_ledger_entry
                                (resource_id, transaction_id, change)
                                VALUES
                                ('green', :transaction_id, :total_green_used)
                                """),
                                [{"transaction_id": transaction_id, "total_green_used": -total_green_used}])
            
        if total_blue_used > 0:
            connection.execute(
                sqlalchemy.text("""
                                INSERT INTO resource_ledger_entry
                                (resource_id, transaction_id, change)
                                VALUES
                                ('blue', :transaction_id, :total_blue_used)
                                """),
                                [{"transaction_id": transaction_id, "total_blue_ml": -total_blue_used}])


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

    with db.engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text(
                """SELECT resource_id, SUM(change) as resource
                FROM resource_ledger_entry
                GROUP BY resource_id
                """))
        first_row = result.all()
        total_red_ml = 0
        total_green_ml = 0
        total_blue_ml = 0
        for resource in first_row:
            if resource[0] == "red":
                total_red_ml = resource[1]
            elif resource[0] == "green":
                total_green_ml = resource[1]
            elif resource[0] == "blue":
                total_blue_ml = resource[1]

        to_bottle_list = []
        # potions_result = connection.execute(sqlalchemy.text("SELECT red_ml, green_ml, blue_ml, inventory FROM potions"))
        # potions_result_table = potions_result.fetchall()

        potions_result = connection.execute(
            sqlalchemy.text(
                """SELECT potion_id, SUM(change) as quantity
                FROM potion_ledger_entry
                GROUP BY potion_id
                """)).all()
        print(potions_result)

        for potion in potions_result:
            potion_id = potion[0]
            formula = connection.execute(
                sqlalchemy.text("""SELECT red_ml, green_ml, blue_ml from potions
                                WHERE potions.id = :potion_id
                                """),
                                [{"potion_id": potion_id}])
            first_row = formula.first()
            print(first_row)

            to_bottle_list.append((potion[1], [first_row.red_ml, first_row.green_ml, first_row.blue_ml, 0]))
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