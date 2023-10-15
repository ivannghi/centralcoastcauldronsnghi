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
        connection.execute(sqlalchemy.text(
            """UPDATE potions
            SET inventory = potions.inventory - cart_items.quantity
            FROM cart_items
            WHERE cart_items.cart_id = :cart_id and cart_items.potion_id = potions.id
            """),
            [{"cart_id": cart_id}]
            )     
        

        result = connection.execute(sqlalchemy.text(
            """
            SELECT quantity, potions.price
            FROM cart_items
            JOIN potions ON potions.id = cart_items.potion_id
            WHERE cart_items.cart_id = :cart_id  
            """),
            [{"cart_id": cart_id}]
            )
        
        for quant,price in result.fetchall():
            print((quant, price))
            bought_potions += quant
            total_cost += quant*price
        
        connection.execute(sqlalchemy.text(
            """
            UPDATE global_inventory
            SET gold = gold + :total_cost
            """),
            [{"total_cost": total_cost}]
        )

    return {"total_potions_bought": bought_potions, "total_gold_paid": total_cost}