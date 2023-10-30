import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("TRUNCATE carts, cart_items, potion_ledger_entry, resource_ledger_entry, transactions"))
        t_id = connection.execute(
            sqlalchemy.text("""
                            INSERT INTO transactions
                            (description) VALUES ('start')
                            RETURNING id
                            """))
        t_id = t_id.scalar_one()
        connection.execute(
            sqlalchemy.text("""
                            INSERT INTO resource_ledger_entry
                            (resource_id, transaction_id, change)
                            VALUES
                            ('red', :t_id, 0),
                            ('green', :t_id, 0),
                            ('blue', :t_id, 0),
                            ('gold', :t_id, 100)
                            """),
                            [{"t_id": t_id}])
        connection.execute(
            sqlalchemy.text("""
                            INSERT INTO potion_ledger_entry
                            (potion_id, transaction_id, change)
                            VALUES
                            (13, :t_id, 0),
                            (14, :t_id, 0),
                            (15, :t_id, 0),
                            (16, :t_id, 0),
                            (17, :t_id, 0),
                            (18, :t_id, 0)
                            """),
                            [{"t_id": t_id}])

    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    # TODO: Change me!
    return {
        "shop_name": "cauldrons and potions",
        "shop_owner": "Ivan Nghi",
    }

