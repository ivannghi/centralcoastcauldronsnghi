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
        query = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_blue_ml, num_green_ml, gold FROM global_inventory"))
        first_row = query.first()
        total_red_ml = first_row.num_red_ml
        total_gold = first_row.gold
        total_blue_ml = first_row.num_blue_ml
        total_green_ml = first_row.num_green_ml

        for barrel in barrels_delivered:
            if barrel.sku == "SMALL_RED_BARREL" and barrel.quantity > 0 and total_gold >= barrel.price:
                total_red_ml += barrel.ml_per_barrel
                total_gold -= barrel.price
            
            elif barrel.sku == "SMALL_BLUE_BARREL" and barrel.quantity > 0 and total_gold >= barrel.price:
                total_blue_ml += barrel.ml_per_barrel
                total_gold -= barrel.price

            elif barrel.sku == "SMALL_GREEN_BARREL" and barrel.quantity > 0 and total_gold >= barrel.price:
                total_green_ml += barrel.ml_per_barrel
                total_gold -= barrel.price

        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {total_gold}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {total_red_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = {total_blue_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {total_green_ml}"))




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
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_blue_potions, num_green_potions, gold FROM global_inventory"))
        first_row = result.first()
        total_gold = first_row.gold
        #find which potion to purchase first
        potions_list = [(first_row.num_green_potions, "green"), (first_row.num_blue_potions, "blue"), (first_row.num_red_potions, "red")]
        potions_list = sorted(potions_list, key=itemgetter(0))
        # potions_list= potions_list.sort(key=lambda x: x[0], )
        print(potions_list)

        for pot in potions_list:
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
