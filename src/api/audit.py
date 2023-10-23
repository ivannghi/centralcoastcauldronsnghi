import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    total_potions = 0
    with db.engine.begin() as connection:
        # result = connection.execute(sqlalchemy.text("SELECT * from global_inventory"))
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
        first_row = result.first()
        total_ml = total_red_ml + total_blue_ml + total_green_ml

        potions_list = connection.execute(
            sqlalchemy.text("""
            SELECT SUM(change) from potion_ledger_entry
            """))
        
        total_potions = potions_list.scalar_one()
        print(f"total potions: {total_potions}")
        print(f"total_ml: {total_ml}")
        print(f"total gold: {total_gold}")

    return {"number_of_potions": total_potions, "ml_in_barrels": total_ml, "gold": total_gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
