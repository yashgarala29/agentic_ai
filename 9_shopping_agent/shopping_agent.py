from typing import Optional
import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
import sqlite3
from review_api import get_product_review
import base64
load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "product.db")
llm = ChatGroq(model="qwen/qwen3.8-27b", temperature=0)
vision_llm=ChatGroq(model="qwen/qwen3.8-27b", temperature=0)

@tool
def search_products(query: str, limit: Optional[int] = 5) -> list[dict]:
    """
    Search for products based on a query string.
    sort the results by relevance and limit the number of results returned.
    Returns a list of product dictionaries with id, name, and description.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, description FROM products WHERE name LIKE ? OR description LIKE ? LIMIT ?",
        (f"%{query}%", f"%{query}%", limit)
    )
    rows = cursor.fetchall()
    conn.close()

    return [{"id": row[0], "name": row[1], "description": row[2]} for row in rows]

@tool
def get_product_review_tool(product_id: int) -> dict:
    """
    Get the average rating and review count for a product.
    Returns a dictionary with average_rating and review_count.
    """
    return get_product_review(product_id) 

@tool
def place_order(product_id: int, customer_name: str, quantity: int) -> dict:
    """
    Place an order for a product.
    Returns a dictionary with order_id and status.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if the product exists and has enough stock
    cursor.execute("SELECT stock, price FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        conn.close()
        return {"error": "Product not found."}
    
    stock, price = product
    if stock < quantity:
        conn.close()
        return {"error": "Insufficient stock."}

    total_price = price * quantity

    # Insert the order into the orders table
    cursor.execute(
        "INSERT INTO orders (product_id, customer_name, quantity, total_price) VALUES (?, ?, ?, ?)",
        (product_id, customer_name, quantity, total_price)
    )
    order_id = cursor.lastrowid

    # Update the product stock
    cursor.execute(
        "UPDATE products SET stock = stock - ? WHERE id = ?",
        (quantity, product_id)
    )

    conn.commit()
    conn.close()

    return {"order_id": order_id, "status": "pending"}

@tool
def describe_image(image_path: str) -> str:
    """
    Analyze a product image and return its key attributes as a JSON object.
    Use this when the user uploads a photo of a product they are interested in.
    The returned attributes can be used directly with search_products.
    """
    with open(image_path,"rb") as img_file:
        image_data=base64.b64encode(img_file.read()).decode()

    ext = os.path.splitext(image_path)[1].lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

    message = HumanMessage(content=[
        {
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{image_data}"},
        },
        {
            "type": "text",
            "text": (
                "Look at this product image and extract its key attributes. "
                "Return ONLY a JSON object with these fields:\n"
                "- product_type: what kind of product it is (e.g. honey, olive oil, almonds)\n"
                "- search_query: a short keyword to search for it (e.g. 'honey', 'olive oil')\n"
                "- is_organic: true if the label says organic, false if not, null if unclear\n"
                "- description: one sentence describing the product"
            ),
        },
    ])

    response = vision_llm.invoke([message])
    return response.content


SYSTEM_PROMPT = (
    "You are a helpful shopping assistant. Follow these rules strictly.\n\n"
    "IMAGE SEARCH — when the user provides an image or image file path:\n"
    "1. Call describe_image with the image_path to analyze the product and extract key attributes.\n"
    "2. Extract the search_query and product_type from the returned JSON.\n"
    "3. Call search_products using the extracted search_query.\n"
    "4. Follow the BROWSING steps below with the found products.\n\n"
    "BROWSING — when the user describes what they want to buy or search for (or after image analysis):\n"
    "1. Call search_products with a query to find matching items (returns id, name, description).\n"
    "2. For each candidate product, call get_product_review_tool with its product_id to retrieve average_rating and review_count.\n"
    "3. Filter by the user's minimum rating if specified.\n"
    "4. Present qualifying products as a numbered list. For each item use this exact format "
    "(plain text, no backticks, no code blocks, no bold, no italic):\n\n"
    "   #<number>. <name> (ID:<product_id>) — ★<average_rating> (<review_count> reviews) — <description>\n\n"
    "   Add a blank line between each product entry for readability. "
    "Always include (ID:X) so you can reference it later.\n"
    "5. If only one product qualifies, still show it in the list and ask: "
    "'Would you like to order it? Just say yes or give me the number.'\n"
    "6. If no products are found, inform the user clearly and suggest alternative search terms.\n"
    "7. Do NOT call place_order at this stage.\n\n"
    "ORDERING — when the user confirms they want to buy (e.g. 'yes', 'sure', 'go ahead', "
    "'order number 2', 'the first one', 'get me #3'):\n"
    "1. Look at your previous message to find the (ID:X) for the chosen product "
    "(if only one was listed and the user says 'yes', use that product's ID).\n"
    "2. If customer_name is not provided, ask the user for their name. Default quantity to 1 if not specified.\n"
    "3. Call place_order with product_id, customer_name, and quantity.\n"
    "4. Confirm the order to the user in plain text using the returned order_id and status.\n\n"
    "Never place an order unless the user explicitly confirms. "
    "Never guess a product_id — always take it from the (ID:X) in your own previous message."
)

agent = create_agent(
    tools=[search_products, get_product_review_tool, place_order,describe_image],
    model=llm,
    system_prompt=SYSTEM_PROMPT
)

if __name__ == "__main__":
    
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "I want to buy Bottle with 4.5+ rating."
                    ),
                }
            ]
        }
    )
    print(result["messages"][-1].content)

# if __name__ == "__main__":
#     search_query = "Shoes"
#     results = search_products(search_query,limit=2)
#     print(f"Search results for '{results}':")
#     for product in results:
#         review_stats = get_product_review(product["id"])
#         print(f"Product: {product['name']}, Average Rating: {review_stats['average_rating']}, Review Count: {review_stats['review_count']}")

