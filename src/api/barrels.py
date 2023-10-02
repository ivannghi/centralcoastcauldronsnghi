import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

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
    print(barrels_delivered)
    with db.engine.begin() as connection:
        query = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = query.first()
        total_red_ml = first_row.num_red_ml
        total_gold = first_row.gold
        for barrel in barrels_delivered:
            total_red_ml = total_red_ml + barrel.ml_per_barrel
            total_gold = total_gold - barrel.price
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {total_gold}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {total_red_ml}"))


    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    barrels_list = []
    barrels_to_buy = 0
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()
        if first_row.num_red_potions < 10:
            for barrel in wholesale_catalog:
                if barrel.sku == "SMALL_RED_BARREL":
                    print('hi')
                    if first_row.gold > barrel.price:
                        barrels_to_buy = 1

    if barrels_to_buy >= 1:
        barrels_list.append({
            "sku": "SMALL_RED_BARREL",
            "quantity": barrels_to_buy, 
        })

    return barrels_list
