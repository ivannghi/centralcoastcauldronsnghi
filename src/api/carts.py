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

class NewCart(BaseModel):
    customer: str

carts = {}
cart_id = 1
@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    global cart_id
    global carts
    created_cart_id = cart_id
    cart_id += 1
    return {"cart_id": created_cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    carts.update({cart_id: Item(item_sku, cart_item.quantity)})
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    bought_potions = 0
    if carts[cart_id].sku == "RED_POTION_0":
        bought_potions = carts[cart_id].quantity

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * from global_inventory"))
        first_row = result.first()
        potions_count = first_row.num_red_potions
        total_gold = first_row.gold
        total_cost = 0
        if bought_potions <= potions_count:
            total_cost = 50*bought_potions
            total_gold -= total_cost
            potions_count -= bought_potions
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {total_gold}"))
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {potions_count}"))

    return {"total_potions_bought": bought_potions, "total_gold_paid": total_cost}