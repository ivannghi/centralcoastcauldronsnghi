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
    global cart_id
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
    if cart_id in carts:
        carts[cart_id].append(Item(item_sku, cart_item.quantity))
    else:
        cart_item_list = [Item(item_sku, cart_item.quantity)]
        carts.update({cart_id: cart_item_list})
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    # bought_potions = 0
    # if carts[cart_id].sku == "RED_POTION_0":
    #     bought_potions = carts[cart_id].quantity
    print(f"cart: {carts[cart_id]}")

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT gold, num_red_potions, num_blue_potions from global_inventory"))
        first_row = result.first()
        total_gold = first_row.gold
        total_red_potions = first_row.num_red_potions
        total_blue_potions = first_row.num_blue_potions
        total_green_potions = first_row.num_green_potions
        total_cost = 0
        bought_potions = 0

        for potion in carts[cart_id]:
            if potion.sku == "RED_POTION_0":
                total_cost += 50*potion.quantity
                total_red_potions -= potion.quantity
                bought_potions += potion.quantity
            
            elif potion.sku == "BLUE_POTION_0":
                total_cost += 50*potion.quantity
                total_blue_potions -= potion.quantity
                bought_potions += potion.quantity

            elif potion.sku == "GREEN_POTION_0":
                total_cost += 50*potion.quantity
                total_green_potions -= potion.quantity
                bought_potions += potion.quantity

        # if bought_potions <= potions_count:
        #     total_cost = 50*bought_potions
        #     first_row.gold += total_cost
        #     potions_count -= bought_potions

        #update gold total
        total_gold += total_cost

        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {total_gold}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {total_red_potions}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = {total_blue_potions}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {total_green_potions}"))


    return {"total_potions_bought": bought_potions, "total_gold_paid": total_cost}