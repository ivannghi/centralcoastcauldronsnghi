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
        result = connection.execute(sqlalchemy.text("SELECT * from global_inventory"))
        first_row = result.first()
        total_ml = first_row.num_red_ml + first_row.num_blue_ml + first_row.num_green_ml

        potions_list = connection.execute(sqlalchemy.text("SELECT inventory from potions")).fetchall()
        for potion in potions_list:
            # print(potion[0])
            total_potions += potion[0]

    return {"number_of_potions": total_potions, "ml_in_barrels": total_ml, "gold": first_row.gold}

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
