import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# -----------------------------
# Database Connection
# -----------------------------
engine = create_engine("postgresql+psycopg2://postgres:1234@localhost:5432/tpch")

# -----------------------------
# Helper Function
# -----------------------------
def run_query(query, params=None):
    with engine.connect() as conn:
        if params:
            conn.execute(text(query), params)
        else:
            conn.execute(text(query))
        conn.commit()

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("🟢 PostgreSQL Data Entry System")

menu = st.sidebar.selectbox(
    "Choose Form",
    ["Add Customer", "Add Product", "Create Order", "Add Order Item"]
)

# ============================================================
# 1. Add Customer
# ============================================================
if menu == "Add Customer":
    st.header("➕ Add New Customer")

    name = st.text_input("Customer Name")
    country = st.text_input("Country")

    if st.button("Save Customer"):
        query = """
        INSERT INTO customers (customer_name, country)
        VALUES (:name, :country)
        """
        run_query(query, {"name": name, "country": country})
        st.success("Customer Added Successfully!")

# ============================================================
# 2. Add Product
# ============================================================
elif menu == "Add Product":
    st.header("📦 Add New Product")

    name = st.text_input("Product Name")
    category = st.text_input("Category")
    price = st.number_input("Price", min_value=0.0)

    if st.button("Save Product"):
        query = """
        INSERT INTO products (product_name, category, price)
        VALUES (:name, :category, :price)
        """
        run_query(query, {"name": name, "category": category, "price": price})
        st.success("Product Added Successfully!")

# ============================================================
# 3. Create Order
# ============================================================
elif menu == "Create Order":
    st.header("📝 Create Order")

    customers_df = pd.read_sql("SELECT customer_id, customer_name FROM customers", engine)
    customer_list = customers_df['customer_name'].tolist()

    if len(customer_list) == 0:
        st.warning("No customers found. Please add a customer first.")
    else:
        customer = st.selectbox("Select Customer", customer_list)
        date = st.date_input("Order Date")
        total = st.number_input("Total Amount", min_value=0.0)

        if st.button("Save Order"):
            cust_id = customers_df[customers_df.customer_name == customer]['customer_id'].values[0]

            query = """
            INSERT INTO orders (customer_id, order_date, total_amount)
            VALUES (:cid, :dt, :total)
            """
            run_query(query, {"cid": cust_id, "dt": date, "total": total})

            st.success("Order Created Successfully!")

# ============================================================
# 4. Add Order Item
# ============================================================
elif menu == "Add Order Item":
    st.header("🛒 Add Order Item")

    orders_df = pd.read_sql("SELECT order_id FROM orders", engine)
    products_df = pd.read_sql("SELECT product_id, product_name, price FROM products", engine)

    if len(orders_df) == 0:
        st.warning("No orders found. Please create an order first.")
    elif len(products_df) == 0:
        st.warning("No products found. Please add a product first.")
    else:
        order_ids = orders_df['order_id'].tolist()
        order_id = st.selectbox("Select Order ID", order_ids)

        product_list = products_df['product_name'].tolist()
        product = st.selectbox("Select Product", product_list)

        quantity = st.number_input("Quantity", min_value=1)

        price = float(products_df[products_df.product_name == product]['price'].values[0])
        line_total = price * quantity

        st.write(f"Line Total: **{line_total}**")

        if st.button("Save Item"):
            prod_id = products_df[products_df.product_name == product]['product_id'].values[0]

            query = """
            INSERT INTO order_items (order_id, product_id, quantity, line_total)
            VALUES (:oid, :pid, :qty, :total)
            """
            run_query(
                query,
                {
                    "oid": order_id,
                    "pid": prod_id,
                    "qty": quantity,
                    "total": line_total
                }
            )

            st.success("Order Item Added Successfully!")
