import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class Item():
    def __init__(self, sku, quantity):
        self.sku = sku
        self.quantity = quantity

    def __repr__(self) -> str:
        return f'Item(\'{self.sku}\', {self.quantity})'

class NewCart(BaseModel):
    customer: str

carts = {}
cart_id = 1
@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    name = new_cart.customer
    with db.engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text(
                """INSERT INTO carts (name) VALUES (:name) RETURNING id"""),
            [{"name": name}])
    # print(result.scalar_one())
    return {"cart_id": result.scalar_one()}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    quantity = cart_item.quantity
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """INSERT INTO cart_items
                (cart_id, potion_id, quantity)
                SELECT :cart_id, potions.id, :quantity
                FROM potions
                WHERE potions.sku = :item_sku
                """),
                [{"cart_id": cart_id, "quantity": quantity, "item_sku": item_sku}]
                )

    # if cart_id in carts:
    #     carts[cart_id].append(Item(item_sku, cart_item.quantity))
    # else:
    #     cart_item_list = [Item(item_sku, cart_item.quantity)]
    #     carts.update({cart_id: cart_item_list})
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    bought_potions = 0
    total_cost = 0

    with db.engine.begin() as connection:
        potion = connection.execute(
            sqlalchemy.text(
                """
                SELECT potion_id, quantity from cart_items
                WHERE cart_id = :cart_id
                """),
                [{"cart_id": cart_id}])
        customer = connection.execute(sqlalchemy.text(
            """
            SELECT name from carts
            WHERE id = :cart_id
            """),
            [{"cart_id": cart_id}])

        customer_name = customer.scalar_one()
        print(customer_name)
        # print(potion.fetchall())

        potion_details = potion.fetchall()
        print(potion_details)
        for pot in potion_details:
            potion_id = pot[0]
            potion_quantity = pot[1]
            bought_potions += potion_quantity

            pot2 = connection.execute(sqlalchemy.text(
                """
                SELECT name, price
                FROM potions
                WHERE id = :potion_id
                """),
                [{"potion_id": potion_id}])
            pot_stat = pot2.fetchone()
            pot_name = pot_stat[0]
            pot_price = pot_stat[1]
            print(pot_stat)

            transaction = connection.execute(sqlalchemy.text(
                """
                INSERT INTO transactions
                (description)
                VALUES 
                (:customer_name || ' bought ' || :quantity || ' ' || :pot_name || ' for ' || :pot_price || ' each.')
                RETURNING id
                """),
                [{"customer_name":customer_name, "quantity": str(potion_quantity), "potion_id": str(potion_id), "pot_name": pot_name, "pot_price":str(pot_price)}])
            transaction_id = transaction.scalar_one()
            print(transaction_id)

            connection.execute(sqlalchemy.text(
                """
                INSERT INTO potion_ledger_entry
                (potion_id, transaction_id, change)
                VALUES
                (:potion_id, :transaction_id, :potion_quantity)
                """),
                [{"potion_id": potion_id, "transaction_id": transaction_id, "potion_quantity": -potion_quantity}])

            # """UPDATE potions
            # SET inventory = potions.inventory - cart_items.quantity
            # FROM cart_items
            # WHERE cart_items.cart_id = :cart_id and cart_items.potion_id = potions.id
            # """),
            # [{"cart_id": cart_id}]    
        

            connection.execute(sqlalchemy.text(
                """
                INSERT INTO resource_ledger_entry
                (resource_id, transaction_id, change)
                VALUES
                ('gold', :transaction_id, :change)
                """),
                [{"transaction_id": transaction_id, "change": pot_price*potion_quantity}]
                )
            total_cost += pot_price*potion_quantity
        # for quant,price in result.fetchall():
        #     print((quant, price))
        #     bought_potions += quant
        #     total_cost += quant*price
        
        # connection.execute(sqlalchemy.text(
        #     """
        #     UPDATE global_inventory
        #     SET gold = gold + :total_cost
        #     """),
        #     [{"total_cost": total_cost}]
        # )

    return {"total_potions_bought": bought_potions, "total_gold_paid": total_cost}