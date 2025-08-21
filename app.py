
import os
import datetime as dt
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Local Food Wastage Management System", page_icon="🍽️", layout="wide")

st.sidebar.title("Navigation")
st.sidebar.info("Use the tabs at the top to switch between features.")

st.title("🍽️ Local Food Wastage Management System")
st.caption("Upload CSVs → Manage data (CRUD) → Analyze with 15+ SQL queries.")

def get_engine():
    try:
        url = st.secrets.get("db", {}).get("url") if "db" in st.secrets else None
    except:
        url = None
    
    if not url:
        db_path = os.path.join(os.getcwd(), "food.db")
        url = f"sqlite:///{db_path}"
    return create_engine(url, pool_pre_ping=True)

engine = get_engine()

with engine.begin() as conn:
    conn.exec_driver_sql("""
    CREATE TABLE IF NOT EXISTS providers (
        Provider_ID   INTEGER PRIMARY KEY,
        Name          VARCHAR(100) NOT NULL,
        Type          VARCHAR(50),
        Address       VARCHAR(255),
        City          VARCHAR(50),
        Contact       VARCHAR(50)
    );
    """)
    conn.exec_driver_sql("""
    CREATE TABLE IF NOT EXISTS receivers (
        Receiver_ID   INTEGER PRIMARY KEY,
        Name          VARCHAR(100) NOT NULL,
        Type          VARCHAR(50),
        City          VARCHAR(50),
        Contact       VARCHAR(50)
    );
    """)
    conn.exec_driver_sql("""
    CREATE TABLE IF NOT EXISTS food_listings (
        Food_ID       INTEGER PRIMARY KEY,
        Food_Name     VARCHAR(100) NOT NULL,
        Quantity      INTEGER NOT NULL,
        Expiry_Date   DATE NOT NULL,
        Provider_ID   INTEGER NOT NULL,
        Provider_Type VARCHAR(50),
        Location      VARCHAR(50),
        Food_Type     VARCHAR(50),
        Meal_Type     VARCHAR(50)
    );
    """)
    conn.exec_driver_sql("""
    CREATE TABLE IF NOT EXISTS claims (
        Claim_ID     INTEGER PRIMARY KEY,
        Food_ID      INTEGER NOT NULL,
        Receiver_ID  INTEGER NOT NULL,
        Status       VARCHAR(20) NOT NULL,
        Timestamp    DATETIME NOT NULL
    );
    """)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📥 CSV Import", "📦 Food Listings (CRUD)", "👥 Providers & Receivers (CRUD)", "🧾 Claims (CRUD)", "📊 Analysis & Reports"])

with tab1:
    st.subheader("Import CSVs")
    st.caption("Upload: providers_data.csv, receivers_data.csv, food_listings_data.csv, claims_data.csv")
    files = st.file_uploader("Upload CSV(s)", type=["csv"], accept_multiple_files=True)
    if files:
        with engine.begin() as conn:
            for f in files:
                name = f.name.lower()
                df = pd.read_csv(f)
                if 'providers' in name:
                    df.to_sql("providers", conn, if_exists="replace", index=False)
                    st.success(f"Loaded providers: {df.shape}")
                elif 'receivers' in name:
                    df.to_sql("receivers", conn, if_exists="replace", index=False)
                    st.success(f"Loaded receivers: {df.shape}")
                elif 'food' in name and 'list' in name:
                    if 'Expiry_Date' in df.columns:
                        df['Expiry_Date'] = pd.to_datetime(df['Expiry_Date']).dt.date
                    df.to_sql("food_listings", conn, if_exists="replace", index=False)
                    st.success(f"Loaded food_listings: {df.shape}")
                elif 'claim' in name:
                    if 'Timestamp' in df.columns:
                        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                    df.to_sql("claims", conn, if_exists="replace", index=False)
                    st.success(f"Loaded claims: {df.shape}")
                else:
                    st.warning(f"Unknown CSV: {f.name}")
        st.toast("CSV import completed.", icon="✅")

with tab2:
    st.subheader("Food Listings: View / Create / Update / Delete")
    with st.expander("View & Filter Listings", expanded=True):
        city = st.text_input("Filter by City (Location)")
        meal = st.selectbox("Filter by Meal Type", ["", "Breakfast", "Lunch", "Dinner", "Snacks"])
        ftype = st.selectbox("Filter by Food Type", ["", "Vegetarian", "Non-Vegetarian", "Vegan"])
        base_q = "SELECT * FROM food_listings WHERE 1=1"
        params = {}
        if city:
            base_q += " AND Location = :city"
            params["city"] = city
        if meal:
            base_q += " AND Meal_Type = :meal"
            params["meal"] = meal
        if ftype:
            base_q += " AND Food_Type = :ftype"
            params["ftype"] = ftype
        df = pd.read_sql(text(base_q), engine, params=params)
        st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.markdown("**Create / Update / Delete**")
    colA, colB = st.columns(2)

    with colA:
        st.markdown("**Create New Listing**")
        with st.form("create_food"):
            Food_ID = st.number_input("Food_ID", min_value=1, step=1)
            Food_Name = st.text_input("Food_Name")
            Quantity = st.number_input("Quantity", min_value=1, step=1)
            Expiry_Date = st.date_input("Expiry_Date", value=dt.date.today())
            Provider_ID = st.number_input("Provider_ID", min_value=1, step=1)
            Provider_Type = st.text_input("Provider_Type")
            Location = st.text_input("Location")
            Food_Type = st.selectbox("Food_Type", ["Vegetarian", "Non-Vegetarian", "Vegan"])
            Meal_Type = st.selectbox("Meal_Type", ["Breakfast", "Lunch", "Dinner", "Snacks"])
            submitted = st.form_submit_button("Create")
        if submitted:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO food_listings (Food_ID, Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type)
                    VALUES (:Food_ID, :Food_Name, :Quantity, :Expiry_Date, :Provider_ID, :Provider_Type, :Location, :Food_Type, :Meal_Type)
                """), dict(Food_ID=Food_ID, Food_Name=Food_Name, Quantity=Quantity, Expiry_Date=str(Expiry_Date),
                             Provider_ID=Provider_ID, Provider_Type=Provider_Type, Location=Location, Food_Type=Food_Type, Meal_Type=Meal_Type))
            st.success("Created.")

    with colB:
        st.markdown("**Update / Delete Listing**")
        edit_id = st.number_input("Target Food_ID", min_value=1, step=1, key="edit_food_id")
        with st.form("update_food"):
            new_qty = st.number_input("New Quantity", min_value=1, step=1, key="new_qty")
            new_exp = st.date_input("New Expiry_Date", value=dt.date.today(), key="new_exp")
            new_loc = st.text_input("New Location", key="new_loc")
            update_btn = st.form_submit_button("Update")
        if update_btn:
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE food_listings
                    SET Quantity=:q, Expiry_Date=:e, Location=:l
                    WHERE Food_ID=:id
                """), dict(q=new_qty, e=str(new_exp), l=new_loc, id=edit_id))
            st.success("Updated.")

        if st.button("Delete Listing"):
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM food_listings WHERE Food_ID=:id"), dict(id=edit_id))
            st.success("Deleted.")

with tab3:
    st.subheader("Providers & Receivers")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Providers**")
        pdf = pd.read_sql("SELECT * FROM providers", engine)
        st.dataframe(pdf, use_container_width=True)
        with st.form("prov_form"):
            Provider_ID = st.number_input("Provider_ID", min_value=1, step=1)
            Name = st.text_input("Name")
            Type = st.text_input("Type (Restaurant / Grocery Store / etc.)")
            Address = st.text_input("Address")
            City = st.text_input("City")
            Contact = st.text_input("Contact")
            prov_action = st.selectbox("Action", ["Create/Replace", "Delete"])
            prov_submit = st.form_submit_button("Submit")
        if prov_submit:
            with engine.begin() as conn:
                if prov_action == "Create/Replace":
                    df = pd.DataFrame([{
                        "Provider_ID": Provider_ID, "Name": Name, "Type": Type,
                        "Address": Address, "City": City, "Contact": Contact
                    }])
                    df.to_sql("providers", conn, if_exists="append", index=False)
                    st.success("Provider added.")
                else:
                    conn.execute(text("DELETE FROM providers WHERE Provider_ID=:id"), dict(id=Provider_ID))
                    st.success("Provider deleted.")

    with col2:
        st.markdown("**Receivers**")
        rdf = pd.read_sql("SELECT * FROM receivers", engine)
        st.dataframe(rdf, use_container_width=True)
        with st.form("recv_form"):
            Receiver_ID = st.number_input("Receiver_ID", min_value=1, step=1, key="rid")
            NameR = st.text_input("Name", key="rname")
            TypeR = st.text_input("Type (NGO / Community Center / Individual)", key="rtype")
            CityR = st.text_input("City", key="rcity")
            ContactR = st.text_input("Contact", key="rcontact")
            recv_action = st.selectbox("Action", ["Create/Replace", "Delete"], key="ract")
            recv_submit = st.form_submit_button("Submit", type="primary")
        if recv_submit:
            with engine.begin() as conn:
                if recv_action == "Create/Replace":
                    df = pd.DataFrame([{
                        "Receiver_ID": Receiver_ID, "Name": NameR, "Type": TypeR,
                        "City": CityR, "Contact": ContactR
                    }])
                    df.to_sql("receivers", conn, if_exists="append", index=False)
                    st.success("Receiver added.")
                else:
                    conn.execute(text("DELETE FROM receivers WHERE Receiver_ID=:id"), dict(id=Receiver_ID))
                    st.success("Receiver deleted.")

with tab4:
    st.subheader("Claims")
    cdf = pd.read_sql("SELECT * FROM claims", engine)
    st.dataframe(cdf, use_container_width=True)

    with st.form("claim_form"):
        Claim_ID = st.number_input("Claim_ID", min_value=1, step=1)
        Food_ID = st.number_input("Food_ID", min_value=1, step=1)
        Receiver_ID = st.number_input("Receiver_ID", min_value=1, step=1)
        Status = st.selectbox("Status", ["Pending", "Completed", "Cancelled"])
        Timestamp = st.text_input("Timestamp (YYYY-MM-DD HH:MM:SS)", value=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        action = st.selectbox("Action", ["Create/Replace", "Update Status", "Delete"])
        claim_submit = st.form_submit_button("Submit", type="primary")
    if claim_submit:
        with engine.begin() as conn:
            if action == "Create/Replace":
                conn.execute(text("""
                    INSERT INTO claims (Claim_ID, Food_ID, Receiver_ID, Status, Timestamp)
                    VALUES (:Claim_ID, :Food_ID, :Receiver_ID, :Status, :Timestamp)
                """), dict(Claim_ID=Claim_ID, Food_ID=Food_ID, Receiver_ID=Receiver_ID, Status=Status, Timestamp=Timestamp))
                st.success("Claim added.")
            elif action == "Update Status":
                conn.execute(text("""
                    UPDATE claims SET Status=:Status, Timestamp=:Timestamp WHERE Claim_ID=:Claim_ID
                """), dict(Status=Status, Timestamp=Timestamp, Claim_ID=Claim_ID))
                st.success("Claim updated.")
            else:
                conn.execute(text("DELETE FROM claims WHERE Claim_ID=:id"), dict(id=Claim_ID))
                st.success("Claim deleted.")

with tab5:
    st.subheader("Analysis & Reports (15+ Queries)")

    q_tabs = st.tabs([
        "1️⃣ Providers per City", "2️⃣ Receivers per City", "3️⃣ Provider Type Most Listings",
        "4️⃣ Provider Contacts by City", "5️⃣ Top Receivers by Claims",
        "6️⃣ Total Non-Expired Quantity", "7️⃣ Listings by City",
        "8️⃣ Common Food Types", "9️⃣ Claims per Food Item",
        "🔟 Top Providers by Completed Claims", "1️⃣1️⃣ Claim Status %",
        "1️⃣2️⃣ Avg Quantity per Receiver", "1️⃣3️⃣ Most Claimed Meal Type",
        "1️⃣4️⃣ Total Quantity by Provider", "1️⃣5️⃣ Near-Expiry Items",
        "1️⃣6️⃣ Unclaimed/Not Completed"
    ])

    with q_tabs[0]:
        df = pd.read_sql("SELECT City, COUNT(*) AS total_providers FROM providers GROUP BY City ORDER BY total_providers DESC", engine)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.bar_chart(df.set_index("City"))

    with q_tabs[1]:
        df = pd.read_sql("SELECT City, COUNT(*) AS total_receivers FROM receivers GROUP BY City ORDER BY total_receivers DESC", engine)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.bar_chart(df.set_index("City"))

    with q_tabs[2]:
        df = pd.read_sql("""
            SELECT COALESCE(p.Type, fl.Provider_Type) AS Provider_Type,
                   COUNT(*) AS total_listings
            FROM food_listings fl
            LEFT JOIN providers p ON p.Provider_ID = fl.Provider_ID
            GROUP BY COALESCE(p.Type, fl.Provider_Type)
            ORDER BY total_listings DESC
        """, engine)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.bar_chart(df.set_index("Provider_Type"))

    with q_tabs[3]:
        city = st.text_input("City", key="contact_city")
        if city:
            df = pd.read_sql(text("SELECT Name, Contact, Type, Address FROM providers WHERE City=:city ORDER BY Name"), engine, params={"city": city})
            st.dataframe(df, use_container_width=True)

    with q_tabs[4]:
        df = pd.read_sql("""
            SELECT r.Receiver_ID, r.Name, COUNT(*) AS total_claims
            FROM receivers r
            JOIN claims c ON r.Receiver_ID = c.Receiver_ID
            GROUP BY r.Receiver_ID, r.Name
            ORDER BY total_claims DESC
        """, engine)
        st.dataframe(df, use_container_width=True)

    with q_tabs[5]:
        df = pd.read_sql("""
            SELECT SUM(Quantity) AS total_available_quantity
            FROM food_listings
            WHERE DATE(Expiry_Date) >= DATE('now')
        """, engine)
        st.metric("Total Non-Expired Quantity", int(df.iloc[0,0]) if not df.empty and pd.notna(df.iloc[0,0]) else 0)

    with q_tabs[6]:
        df = pd.read_sql("""
            SELECT Location AS City, COUNT(*) AS listings_count
            FROM food_listings
            GROUP BY Location
            ORDER BY listings_count DESC
        """, engine)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.bar_chart(df.set_index("City"))

    with q_tabs[7]:
        df = pd.read_sql("""
            SELECT Food_Type, COUNT(*) AS occurrences
            FROM food_listings
            GROUP BY Food_Type
            ORDER BY occurrences DESC
        """, engine)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.bar_chart(df.set_index("Food_Type"))

    with q_tabs[8]:
        df = pd.read_sql("""
            SELECT fl.Food_ID, fl.Food_Name, COUNT(c.Claim_ID) AS total_claims
            FROM food_listings fl
            LEFT JOIN claims c ON c.Food_ID = fl.Food_ID
            GROUP BY fl.Food_ID, fl.Food_Name
            ORDER BY total_claims DESC, fl.Food_ID
        """, engine)
        st.dataframe(df, use_container_width=True)

    with q_tabs[9]:
        df = pd.read_sql("""
            SELECT p.Provider_ID, p.Name, COUNT(*) AS completed_claims
            FROM providers p
            JOIN food_listings fl ON fl.Provider_ID = p.Provider_ID
            JOIN claims c ON c.Food_ID = fl.Food_ID
            WHERE c.Status = 'Completed'
            GROUP BY p.Provider_ID, p.Name
            ORDER BY completed_claims DESC
        """, engine)
        st.dataframe(df, use_container_width=True)

    with q_tabs[10]:
        df = pd.read_sql("""
            SELECT Status,
                   COUNT(*) AS cnt,
                   ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM claims), 2) AS pct
            FROM claims
            GROUP BY Status
            ORDER BY cnt DESC
        """, engine)
        st.dataframe(df, use_container_width=True)

    with q_tabs[11]:
        df = pd.read_sql("""
            SELECT r.Receiver_ID, r.Name,
                   ROUND(AVG(fl.Quantity), 2) AS avg_quantity_per_claim
            FROM receivers r
            JOIN claims c ON c.Receiver_ID = r.Receiver_ID
            JOIN food_listings fl ON fl.Food_ID = c.Food_ID
            GROUP BY r.Receiver_ID, r.Name
            ORDER BY avg_quantity_per_claim DESC
        """, engine)
        st.dataframe(df, use_container_width=True)

    with q_tabs[12]:
        df = pd.read_sql("""
            SELECT fl.Meal_Type, COUNT(*) AS claims_count
            FROM claims c
            JOIN food_listings fl ON fl.Food_ID = c.Food_ID
            GROUP BY fl.Meal_Type
            ORDER BY claims_count DESC
        """, engine)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.bar_chart(df.set_index("Meal_Type"))

    with q_tabs[13]:
        df = pd.read_sql("""
            SELECT p.Provider_ID, p.Name, SUM(fl.Quantity) AS total_quantity_donated
            FROM providers p
            JOIN food_listings fl ON fl.Provider_ID = p.Provider_ID
            GROUP BY p.Provider_ID, p.Name
            ORDER BY total_quantity_donated DESC
        """, engine)
        st.dataframe(df, use_container_width=True)

    with q_tabs[14]:
        days = st.number_input("Days Ahead", min_value=1, max_value=30, value=2, step=1)
        df = pd.read_sql(text("""
            SELECT Food_ID, Food_Name, Quantity, Expiry_Date, Location
            FROM food_listings
            WHERE DATE(Expiry_Date) BETWEEN DATE('now') AND DATE('now', '+' || :days || ' day')
            ORDER BY Expiry_Date ASC
        """), engine, params={"days": days})
        st.dataframe(df, use_container_width=True)

    with q_tabs[15]:
        df = pd.read_sql("""
            SELECT fl.Food_ID, fl.Food_Name, fl.Quantity, fl.Expiry_Date, fl.Location
            FROM food_listings fl
            LEFT JOIN claims c ON c.Food_ID = fl.Food_ID AND c.Status = 'Completed'
            WHERE c.Claim_ID IS NULL
            ORDER BY fl.Expiry_Date
        """, engine)
        st.dataframe(df, use_container_width=True)
