import re

def check_order_id(order_id: str) -> bool:
    pattern = r'^\d{19}$'
    if re.match(pattern, order_id):
        return True
    else:
        return False