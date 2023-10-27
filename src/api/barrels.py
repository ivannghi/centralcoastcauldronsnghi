import random
import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from operator import itemgetter

router = APIRouter(
    prefix="/barrels", 
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(f"Barrels Delivered: {barrels_delivered}")
    with db.engine.begin() as connection:
        total_red_ml = 0
        total_cost = 0
        total_blue_ml = 0
        total_green_ml = 0

        for barrel in barrels_delivered:
            if barrel.potion_type == [1,0,0,0] and barrel.quantity > 0:
                total_red_ml += barrel.ml_per_barrel*barrel.quantity
                total_cost += barrel.price*barrel.quantity
            
            elif barrel.potion_type == [0,0,1,0] and barrel.quantity > 0:
                total_blue_ml += barrel.ml_per_barrel*barrel.quantity
                total_cost += barrel.price*barrel.quantity

            elif barrel.potion_type == [0,1,0,0] and barrel.quantity > 0:
                total_green_ml += barrel.ml_per_barrel*barrel.quantity
                total_cost += barrel.price*barrel.quantity

        print(f"total_red_ml: {total_red_ml}")
        print(f"total_green_ml: {total_green_ml}")
        print(f"total_blue_ml: {total_blue_ml}")
        print(f"total cost: {total_cost}")


        result = connection.execute(
            sqlalchemy.text("""
                            INSERT INTO transactions
                            (description)
                            VALUES
                            ('Bought ' || :total_red_ml || ' red mls, ' || :total_green_ml || ' green mls, and ' || :total_blue_ml || ' blue mls for '|| :total_cost || ' gold.')
                            RETURNING id
                            """),
                            [{"total_red_ml": str(total_red_ml), "total_green_ml": str(total_green_ml), "total_blue_ml": str(total_blue_ml), "total_cost": str(total_cost)}])
        transaction_id = result.scalar_one()

        if total_red_ml > 0:
            connection.execute(
                sqlalchemy.text("""
                                INSERT INTO resource_ledger_entry
                                (resource_id, transaction_id, change)
                                VALUES
                                ('red', :transaction_id, :total_red_ml)
                                """),
                                [{"transaction_id": transaction_id, "total_red_ml": total_red_ml}])
            
        if total_green_ml > 0:
            connection.execute(
                sqlalchemy.text("""
                                INSERT INTO resource_ledger_entry
                                (resource_id, transaction_id, change)
                                VALUES
                                ('green', :transaction_id, :total_green_ml)
                                """),
                                [{"transaction_id": transaction_id, "total_green_ml": total_green_ml}])
            
        if total_blue_ml > 0:
            connection.execute(
                sqlalchemy.text("""
                                INSERT INTO resource_ledger_entry
                                (resource_id, transaction_id, change)
                                VALUES
                                ('blue', :transaction_id, :total_blue_ml)
                                """),
                                [{"transaction_id": transaction_id, "total_blue_ml": total_blue_ml}])
            
        if total_cost > 0:
            connection.execute(
                sqlalchemy.text("""
                                INSERT INTO resource_ledger_entry
                                (resource_id, transaction_id, change)
                                VALUES
                                ('gold', :transaction_id, :total_cost)
                                """),
                                [{"transaction_id": transaction_id, "total_cost": -total_cost}])
        

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    barrels_list = []

    print(wholesale_catalog)
    with db.engine.begin() as connection:
        potions = connection.execute(sqlalchemy.text(
            """
            SELECT SUM(change) AS total_potions FROM potion_ledger_entry
            """
        ))
        total_potions = potions.scalar_one()
        if total_potions >= 275:
            return []
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
        total_gold = 0
        for resource in first_row:
            if resource[0] == "gold":
                total_gold = resource[1]
            elif resource[0] == "red":
                total_red_ml = resource[1]
            elif resource[0] == "green":
                total_green_ml = resource[1]
            elif resource[0] == "blue":
                total_blue_ml = resource[1]

        print(f" pre-plan total_gold:{total_gold}")
        #find which potion to purchase first
        ml_list = [(total_green_ml, "green"), (total_blue_ml, "blue"), (total_red_ml, "red")]
        random.shuffle(ml_list)
        ml_list = sorted(ml_list, key=itemgetter(0))
        print(ml_list)

        if total_gold <= 120:
            if total_gold >= 60:
                barrels_list.append({
                    "sku": "MINI_RED_BARREL",
                    "quantity": 1, 
                    })
                total_gold -= 60
            if total_gold >= 60:
                barrels_list.append({
                    "sku": "MINI_GREEN_BARREL",
                    "quantity": 1, 
                    })
                total_gold -= 60
            if total_gold >= 60:
                barrels_list.append({
                    "sku": "MINI_BLUE_BARREL",
                    "quantity": 1, 
                    })
                total_gold -= 60
            return barrels_list

        for pot in ml_list:
            third = total_gold//3
            print(f"third: {third}")
            for barrel in wholesale_catalog:
                if pot[1] == "red":
                    #if red, look for red barrel
                    if barrel.potion_type == [1,0,0,0]:
                        if third >= barrel.price:
                            #purchase barrel for gold
                            num_of_barrels = third//barrel.price
                            if num_of_barrels > barrel.quantity:
                                num_of_barrels = barrel.quantity
                            third -= barrel.price * num_of_barrels
                            barrels_list.append({
                                "sku": barrel.sku,
                                "quantity": num_of_barrels, 
                                })
                elif pot[1] == "green":
                    if barrel.potion_type == [0,1,0,0]:
                        if third >= barrel.price:
                            #purchase barrel for gold
                            num_of_barrels = third//barrel.price
                            if num_of_barrels > barrel.quantity:
                                num_of_barrels = barrel.quantity
                            third -= barrel.price * num_of_barrels
                            barrels_list.append({
                            "sku": barrel.sku,
                            "quantity": num_of_barrels, 
                            })
                elif pot[1] == "blue":
                    if barrel.potion_type == [0,0,1,0]:
                        if third >= barrel.price:
                            #purchase barrel for gold
                            num_of_barrels = third//barrel.price
                            if num_of_barrels > barrel.quantity:
                                num_of_barrels = barrel.quantity
                            third -= barrel.price * num_of_barrels
                            barrels_list.append({
                            "sku": barrel.sku,
                            "quantity": num_of_barrels, 
                            })
            print(f"post-third: {third}")
    
    print(f"post-plan total gold: {total_gold}")
    print(f"Barrels List: {barrels_list}")
    return barrels_list
