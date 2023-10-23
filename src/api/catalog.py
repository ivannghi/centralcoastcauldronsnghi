import sqlalchemy
from src import database as db
from fastapi import APIRouter

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.
    catalog = []

    with db.engine.begin() as connection:

        result = connection.execute(
            sqlalchemy.text("""
                            select  * from potions
                            join (
                                select potion_id, sum(change) as quantity
                                from potion_ledger_entry
                                group by potion_id
                            ) as subquery on potion_id = potions.id
                            """))
        
        potions_table = result.fetchall()
        print(potions_table)
        for row in potions_table:
            if row.quantity > 0:
                catalog.append({
                    "sku": row.sku,
                    "name": row.name,
                    "quantity": row.quantity,
                    "price": row.price,
                    "potion_type": [row.red_ml, row.green_ml, row.blue_ml, row.dark_ml],
                })

    return catalog