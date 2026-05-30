import math
from typing import List, Dict, Any

def optimize_transport(pax_count: int, available_vehicles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Dynamic Programming Algorithm to find the optimal combination of vehicles.
    Minimizes total cost while ensuring total capacity >= pax_count.
    
    :param pax_count: Total number of passengers (e.g., 14)
    :param available_vehicles: List of dicts e.g., [{"type": "Innova", "capacity": 6, "price": 2000}]
    :return: Dictionary containing selected vehicles, total cost, and matched capacity
    """
    if not available_vehicles or pax_count <= 0:
        return {"total_cost": 0, "total_capacity": 0, "vehicles_selected": {}}

    # Find the maximum capacity a single vehicle provides to define our DP array bounds
    max_vehicle_cap = max(v['capacity'] for v in available_vehicles)
    target_capacity = pax_count + max_vehicle_cap

    # Initialize DP array with infinity
    dp = [float('inf')] * (target_capacity + 1)
    dp[0] = 0
    
    # Track the choices to reconstruct the selected vehicles
    choices = [None] * (target_capacity + 1)

    for current_cap in range(target_capacity + 1):
        if dp[current_cap] == float('inf'):
            continue
            
        for vehicle in available_vehicles:
            next_cap = current_cap + vehicle['capacity']
            if next_cap <= target_capacity:
                new_cost = dp[current_cap] + vehicle['price']
                if new_cost < dp[next_cap]:
                    dp[next_cap] = new_cost
                    choices[next_cap] = {"vehicle": vehicle, "prev": current_cap}

    # Find the absolute minimum cost that satisfies or exceeds the pax_count
    best_capacity = pax_count
    min_cost = float('inf')
    
    for cap in range(pax_count, target_capacity + 1):
        if dp[cap] < min_cost:
            min_cost = dp[cap]
            best_capacity = cap

    # Backtrack through choices to determine which vehicles were selected
    selected_vehicles = {}
    current = best_capacity
    
    while current > 0 and choices[current] is not None:
        selected_v = choices[current]["vehicle"]
        v_type = selected_v["type"]
        selected_vehicles[v_type] = selected_vehicles.get(v_type, 0) + 1
        current = choices[current]["prev"]

    return {
        "total_cost": min_cost,
        "total_capacity": best_capacity,
        "vehicles_selected": selected_vehicles
    }


def calculate_shared_cab_cost(vehicle_price: float, vehicle_capacity: int, required_seats: int) -> float:
    """
    Calculates fractional cab costs if "Cab Sharing" is enabled by the admin.
    """
    if required_seats >= vehicle_capacity:
        return vehicle_price
    
    per_seat_cost = vehicle_price / vehicle_capacity
    return round(per_seat_cost * required_seats, 2)


def compute_financials(
    base_hotel_cost: float,
    base_transport_cost: float,
    add_ons_cost: float,
    profit_margin: float,
    is_profit_percentage: bool,
    gst_percent: float,
    pt_percent: float,
    pg_percent: float,
    post_quote_discount: float = 0.0
) -> Dict[str, float]:
    """
    Strict financial calculator handling complex tax offsets and gateways.
    Payment Gateway (PG) fee is calculated recursively since it applies to the final swiped amount.
    """
    base_total = base_hotel_cost + base_transport_cost + add_ons_cost
    
    # Calculate Profit
    if is_profit_percentage:
        profit_amount = base_total * (profit_margin / 100.0)
    else:
        profit_amount = profit_margin
        
    subtotal = base_total + profit_amount
    
    # Standard Taxes (GST & PT apply to the subtotal before gateway fees)
    gst_amount = subtotal * (gst_percent / 100.0)
    pt_amount = subtotal * (pt_percent / 100.0)
    
    total_before_pg = subtotal + gst_amount + pt_amount - post_quote_discount
    
    # Payment Gateway Calculation 
    # Because PG fee is charged on the GRAND TOTAL (including the fee itself), 
    # we must back-calculate: Grand Total = Total Before PG / (1 - PG%)
    if pg_percent > 0:
        final_grand_total = total_before_pg / (1.0 - (pg_percent / 100.0))
        pg_amount = final_grand_total - total_before_pg
    else:
        final_grand_total = total_before_pg
        pg_amount = 0.0

    return {
        "base_cost": round(base_total, 2),
        "profit_amount": round(profit_amount, 2),
        "subtotal": round(subtotal, 2),
        "gst_amount": round(gst_amount, 2),
        "pt_amount": round(pt_amount, 2),
        "pg_amount": round(pg_amount, 2),
        "discount": round(post_quote_discount, 2),
        "grand_total": round(final_grand_total, 2)
    }

def extract_vendor_tax_waivers(payment_amount: float, gst_percent: float, pt_percent: float, pg_percent: float) -> Dict[str, float]:
    """
    When a payment is marked as "Direct to Vendor", the CRM must waive the internal 
    tax liabilities (GST, PT, PG) on that specific amount. This back-calculates the offset.
    """
    # Assuming the vendor payment represents the base value + GST
    base_val = payment_amount / (1 + (gst_percent / 100.0))
    gst_waived = payment_amount - base_val
    
    pt_waived = base_val * (pt_percent / 100.0)
    
    # PG is completely waived since the transaction didn't touch your gateway
    pg_waived = payment_amount * (pg_percent / 100.0) 

    return {
        "gst_waived": round(gst_waived, 2),
        "pt_waived": round(pt_waived, 2),
        "pg_waived": round(pg_waived, 2),
        "total_waiver": round(gst_waived + pt_waived + pg_waived, 2)
    }
