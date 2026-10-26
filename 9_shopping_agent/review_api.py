import sqlite3
import os
from typing import Union

DB_PATH = os.path.join(os.path.dirname(__file__), "product.db")


def get_product_review(product_id: int) -> dict:
    """Return average rating and review count for a single product_id."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT AVG(rating), COUNT(*) FROM reviews WHERE product_id = ?",
        (product_id,)
    )
    row = cursor.fetchone()
    conn.close()

    avg = round(row[0], 2) if row and row[0] is not None else 0.0
    count = row[1] if row else 0
    return {"product_id": product_id, "average_rating": avg, "review_count": count}


def get_product_reviews(product_ids: Union[int, list[int]]) -> Union[dict, list[dict]]:
    """
    Return average rating and review count.
    Accepts either a single product_id (int) or a list of product_ids (list[int]).
    """
    # If a single int is passed, return single dict
    if isinstance(product_ids, int):
        return get_product_review(product_ids)

    # Handle empty list case safely
    if not product_ids:
        return []

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    placeholders = ",".join(["?"] * len(product_ids))
    query = f"""
        SELECT product_id, AVG(rating), COUNT(*) 
        FROM reviews 
        WHERE product_id IN ({placeholders}) 
        GROUP BY product_id
    """
    cursor.execute(query, product_ids)
    rows = cursor.fetchall()
    conn.close()

    # Map results by product_id
    stats_map = {
        row[0]: {
            "product_id": row[0],
            "average_rating": round(row[1], 2) if row[1] is not None else 0.0,
            "review_count": row[2]
        }
        for row in rows
    }

    # Ensure all requested product_ids are present in the output (even if 0 reviews)
    result = []
    for pid in product_ids:
        if pid in stats_map:
            result.append(stats_map[pid])
        else:
            result.append({"product_id": pid, "average_rating": 0.0, "review_count": 0})

    return result


# if __name__ == "__main__":
#     # Test 1: Single ID
#     product_id = 1
#     review = get_product_review(product_id)
#     print(f"Single Product: {review}")

#     # Test 2: Multiple IDs
#     product_ids = [1, 2, 3]
#     reviews_list = get_product_reviews(product_ids)
#     print("\nBatch Products:")
#     for r in reviews_list:
#         print(f"  - Product ID {r['product_id']}: {r['average_rating']} stars ({r['review_count']} reviews)")