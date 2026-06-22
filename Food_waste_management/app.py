import os
import pandas as pd
import plotly.express as px
import sqlite3
import streamlit as st

# 1. Establish robust database pathing
# This ensures it finds the DB file in the exact same directory as app.py on Streamlit Cloud
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "food_waste_management.db")

conn = sqlite3.connect(db_path)

# Page configuration
st.set_page_config(
    page_title="Food Waste Management System", page_icon="🍽️", layout="wide"
)

# Sidebar
menu = st.sidebar.selectbox(
    "Navigation", ["Home", "Food Search", "Provider Contacts", "Insights"]
)

# --- HOME PAGE ---
if menu == "Home":
    st.title("🍽️ Food Waste Management System")
    st.markdown(
        "Connect food providers with receivers and reduce food waste."
    )

    col1, col2, col3, col4 = st.columns(4)

    # Try blocks handle empty database scenarios gracefully without crashing the UI
    try:
        providers = pd.read_sql_query(
            "SELECT COUNT(*) cnt FROM providers", conn
        ).iloc[0, 0]
        receivers = pd.read_sql_query(
            "SELECT COUNT(*) cnt FROM receivers", conn
        ).iloc[0, 0]
        foods = pd.read_sql_query(
            "SELECT COUNT(*) cnt FROM food_listings", conn
        ).iloc[0, 0]
        claims = pd.read_sql_query(
            "SELECT COUNT(*) cnt FROM claims", conn
        ).iloc[0, 0]
    except Exception:
        # Fallback values if tables haven't been created/seeded yet
        providers, receivers, foods, claims = 0, 0, 0, 0

    col1.metric("Providers", providers)
    col2.metric("Receivers", receivers)
    col3.metric("Food Listings", foods)
    col4.metric("Claims", claims)

# --- FOOD SEARCH ---
elif menu == "Food Search":
    st.header("🔍 Food Search")

    try:
        food_df = pd.read_sql_query("SELECT * FROM food_listings", conn)

        if not food_df.empty:
            location = st.selectbox(
                "Location", sorted(food_df["Location"].dropna().unique())
            )
            food_type = st.selectbox(
                "Food Type", sorted(food_df["Food_Type"].dropna().unique())
            )
            meal_type = st.selectbox(
                "Meal Type", sorted(food_df["Meal_Type"].dropna().unique())
            )

            filtered = food_df[
                (food_df["Location"] == location)
                & (food_df["Food_Type"] == food_type)
                & (food_df["Meal_Type"] == meal_type)
            ]
            st.dataframe(filtered)
        else:
            st.info("No food listings available to search.")
    except Exception as e:
        st.error(f"Could not load food listings: {e}")

# --- PROVIDER CONTACTS ---
elif menu == "Provider Contacts":
    st.header("📞 Provider Contacts")

    try:
        providers_df = pd.read_sql_query("SELECT * FROM providers", conn)

        if not providers_df.empty:
            city = st.selectbox(
                "Select City", sorted(providers_df["City"].dropna().unique())
            )
            contacts = providers_df[providers_df["City"] == city][
                ["Name", "Type", "Contact", "Address"]
            ]
            st.dataframe(contacts)
        else:
            st.info("No provider contacts available.")
    except Exception as e:
        st.error(f"Could not load providers: {e}")

# --- INSIGHTS ---
elif menu == "Insights":
    st.title("📊 SQL Insights")

    # Wrap the entire insights query pool to protect against missing tables
    try:
        # 1. Which provider type contributes the most food?
        st.subheader("1. Which provider type contributes the most food?")
        q1 = """
        SELECT Provider_Type, SUM(Quantity) AS Total_Quantity 
        FROM food_listings GROUP BY Provider_Type ORDER BY Total_Quantity DESC
        """
        r1 = pd.read_sql_query(q1, conn)
        st.dataframe(r1)
        if not r1.empty:
            fig = px.bar(r1, x="Provider_Type", y="Total_Quantity")
            st.plotly_chart(fig, use_container_width=True)

        # 2. Most Common Food Types
        st.subheader("2. Most Common Food Types")
        q2 = """
        SELECT Food_Type, COUNT(*) Frequency 
        FROM food_listings GROUP BY Food_Type ORDER BY Frequency DESC
        """
        r2 = pd.read_sql_query(q2, conn)
        st.dataframe(r2)
        if not r2.empty:
            fig = px.pie(r2, names="Food_Type", values="Frequency")
            st.plotly_chart(fig, use_container_width=True)

        # 3. Claim Status Distribution
        st.subheader("3. Claim Status Distribution")
        q3 = "SELECT Status, COUNT(*) Count FROM claims GROUP BY Status"
        r3 = pd.read_sql_query(q3, conn)
        st.dataframe(r3)
        if not r3.empty:
            fig = px.pie(r3, names="Status", values="Count")
            st.plotly_chart(fig, use_container_width=True)

        # 4. Top Receivers
        st.subheader("4. Top Receivers")
        q4 = """
        SELECT r.Name, COUNT(*) Total_Claims FROM receivers r 
        JOIN claims c ON r.Receiver_ID = c.Receiver_ID 
        GROUP BY r.Receiver_ID ORDER BY Total_Claims DESC LIMIT 10
        """
        r4 = pd.read_sql_query(q4, conn)
        st.dataframe(r4)
        if not r4.empty:
            fig = px.bar(r4, x="Name", y="Total_Claims")
            st.plotly_chart(fig, use_container_width=True)

        # 5. Most Claimed Meal Type
        st.subheader("5. Most Claimed Meal Type")
        q5 = """
        SELECT f.Meal_Type, COUNT(*) Total_Claims FROM food_listings f 
        JOIN claims c ON f.Food_ID = c.Food_ID 
        GROUP BY f.Meal_Type ORDER BY Total_Claims DESC
        """
        r5 = pd.read_sql_query(q5, conn)
        st.dataframe(r5)
        if not r5.empty:
            fig = px.pie(r5, names="Meal_Type", values="Total_Claims")
            st.plotly_chart(fig, use_container_width=True)

        # 6. Total Food Available
        st.subheader("6. Total Food Available")
        q6 = "SELECT SUM(Quantity) AS Total_Food FROM food_listings"
        r6 = pd.read_sql_query(q6, conn)
        total_food_val = r6.iloc[0, 0] if not r6.empty and r6.iloc[0, 0] else 0
        st.metric("Total Food Available", int(total_food_val))

        # 7. Total Quantity Donated By Provider
        st.subheader("7. Total Quantity Donated By Provider")
        q7 = """
        SELECT p.Name, SUM(f.Quantity) Total_Donated FROM providers p 
        JOIN food_listings f ON p.Provider_ID = f.Provider_ID 
        GROUP BY p.Provider_ID ORDER BY Total_Donated DESC LIMIT 10
        """
        r7 = pd.read_sql_query(q7, conn)
        st.dataframe(r7)
        if not r7.empty:
            fig = px.bar(r7, x="Total_Donated", y="Name", orientation="h")
            st.plotly_chart(fig, use_container_width=True)

        # 8. How many food claims have been made for each food item?
        st.subheader(
            "8. How many food claims have been made for each food item?"
        )
        q8 = """
        SELECT f.Food_Name, COUNT(c.Claim_ID) AS Total_Claims FROM food_listings f 
        LEFT JOIN claims c ON f.Food_ID = c.Food_ID 
        GROUP BY f.Food_ID, f.Food_Name ORDER BY Total_Claims DESC;
        """
        r8 = pd.read_sql_query(q8, conn)
        st.dataframe(r8)
        if not r8.empty:
            fig = px.bar(
                r8.head(10),
                x="Total_Claims",
                y="Food_Name",
                orientation="h",
                title="Top 10 Most Claimed Food Items",
                text="Total_Claims",
            )
            st.plotly_chart(fig, use_container_width=True)

        # 9. Which provider has had the highest number of successful food claims?
        st.subheader(
            "9. Which provider has had the highest number of successful food claims?"
        )
        q9 = """
        SELECT p.Name, COUNT(c.Claim_ID) AS Successful_Claims FROM providers p 
        JOIN food_listings f ON p.Provider_ID = f.Provider_ID 
        JOIN claims c ON f.Food_ID = c.Food_ID WHERE c.Status = 'Completed' 
        GROUP BY p.Provider_ID, p.Name ORDER BY Successful_Claims DESC LIMIT 1;
        """
        r9 = pd.read_sql_query(q9, conn)
        st.dataframe(r9)
        if not r9.empty:
            st.metric(
                label=f"🏆 Top Provider: {r9.iloc[0]['Name']}",
                value=int(r9.iloc[0]["Successful_Claims"]),
            )

        # 10. Percentage of Completed vs Pending vs Cancelled Claims
        st.subheader(
            "10. Percentage of Completed vs Pending vs Cancelled Claims"
        )
        q10 = """
        SELECT Status, ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims), 2) AS Percentage 
        FROM claims GROUP BY Status;
        """
        r10 = pd.read_sql_query(q10, conn)
        st.dataframe(r10)
        if not r10.empty:
            fig = px.pie(
                r10,
                names="Status",
                values="Percentage",
                title="Claim Status Distribution",
                hole=0.3,
            )
            st.plotly_chart(fig, use_container_width=True)

        # 11. Average Quantity of Food Claimed per Receiver
        st.subheader("11. Average Quantity of Food Claimed per Receiver")
        q11 = """
        SELECT r.Name, ROUND(AVG(f.Quantity), 2) AS Avg_Quantity_Claimed FROM receivers r 
        JOIN claims c ON r.Receiver_ID = c.Receiver_ID 
        JOIN food_listings f ON c.Food_ID = f.Food_ID 
        GROUP BY r.Receiver_ID, r.Name ORDER BY Avg_Quantity_Claimed DESC;
        """
        r11 = pd.read_sql_query(q11, conn)
        st.dataframe(r11)
        if not r11.empty:
            fig = px.bar(
                r11.head(10),
                x="Avg_Quantity_Claimed",
                y="Name",
                orientation="h",
                title="Top 10 Receivers by Average Quantity Claimed",
                text="Avg_Quantity_Claimed",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Average Quantity overall
        st.subheader("Average Quantity of Food Claimed")
        q_avg = """
        SELECT ROUND(AVG(Quantity), 2) AS Avg_Quantity FROM food_listings f 
        JOIN claims c ON f.Food_ID = c.Food_ID;
        """
        r_avg = pd.read_sql_query(q_avg, conn)
        avg_val = (
            r_avg.iloc[0, 0]
            if not r_avg.empty and r_avg.iloc[0, 0] is not None
            else 0
        )
        st.metric(label="Average Quantity Claimed", value=avg_val)

        # 12. Which Meal Type is Claimed the Most?
        st.subheader("12. Which Meal Type is Claimed the Most?")
        q12 = """
        SELECT f.Meal_Type, COUNT(c.Claim_ID) AS Total_Claims FROM food_listings f 
        JOIN claims c ON f.Food_ID = c.Food_ID 
        GROUP BY f.Meal_Type ORDER BY Total_Claims DESC;
        """
        r12 = pd.read_sql_query(q12, conn)
        st.dataframe(r12)
        if not r12.empty:
            fig = px.pie(
                r12,
                names="Meal_Type",
                values="Total_Claims",
                title="Meal Type Claim Distribution",
                hole=0.3,
            )
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error executing insights: {e}")

# Close connection cleanly at the end of the script cycle
conn.close()
