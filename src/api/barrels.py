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


        connection.execute(
            sqlalchemy.text("""
                            UPDATE global_inventory SET
                            num_red_ml = num_red_ml + :total_red_ml,
                            num_green_ml = num_green_ml + :total_green_ml,
                            num_blue_ml = num_blue_ml + :total_blue_ml,
                            gold = gold - :total_cost                          
                            """),
                            [{"total_red_ml": total_red_ml, "total_green_ml": total_green_ml, "total_blue_ml": total_blue_ml, "total_cost": total_cost}])

        # connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {total_gold}"))
        # connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {total_red_ml}"))
        # connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = {total_blue_ml}"))
        # connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {total_green_ml}"))
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    barrels_list = []
    red_barrels = 0
    blue_barrels = 0 
    green_barrels = 0
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_blue_ml, num_green_ml, gold FROM global_inventory"))
        first_row = result.fetchone()
        total_gold = first_row.gold
        #find which potion to purchase first
        ml_list = [(first_row.num_green_ml, "green"), (first_row.num_blue_ml, "blue"), (first_row.num_red_ml, "red")]
        random.shuffle(ml_list)
        ml_list = sorted(ml_list, key=itemgetter(0))
        print(ml_list)

        for pot in ml_list:
            for barrel in wholesale_catalog:
                if pot[1] == "red":
                    #if red, look for red barrel
                    if barrel.sku == "SMALL_RED_BARREL":
                        if total_gold >= barrel.price:
                            #purchase barrel for gold
                            red_barrels = 1
                            total_gold -= barrel.price
                elif pot[1] == "blue":
                    if barrel.sku == "SMALL_BLUE_BARREL":
                        if total_gold >= barrel.price:
                            blue_barrels = 1
                            total_gold -= barrel.price
                elif pot[1] == "green":
                    if barrel.sku == "SMALL_GREEN_BARREL":
                        if total_gold >= barrel.price:
                            green_barrels = 1
                            total_gold -= barrel.price

    if red_barrels >= 1:
        barrels_list.append({
            "sku": "SMALL_RED_BARREL",
            "quantity": red_barrels, 
        })
    if blue_barrels >= 1:
        barrels_list.append({
            "sku": "SMALL_BLUE_BARREL",
            "quantity": blue_barrels, 
        })
    if green_barrels >= 1:
        barrels_list.append({
            "sku": "SMALL_GREEN_BARREL",
            "quantity": green_barrels, 
        })
    # print(barrels_to_buy)
    return barrels_list
