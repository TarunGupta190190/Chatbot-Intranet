import pandas as pd
import requests
import streamlit as st
import os
import re

### Inhouse inbuild modules
from db import DB as sqldb
from text_to_sql import LLMHandler


sqldb = sqldb()
text_to_sql = LLMHandler()
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-coder:16b-v2"

tenant_data_dir = "tenant_data_files"
tenant_data_dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__),tenant_data_dir))
os.makedirs(tenant_data_dir_path, exist_ok=True)

st.title("ðŸ“Š Tenants Information System")
uploaded_file = st.file_uploader("Upload your daily CSV")

if uploaded_file:
    
    filename = uploaded_file.name
    match = re.search(r'\d{4}-\d{2}-\d{2}', filename)
    if match:
        current_date = match.group(0)
        st.info(f"Using date from file name: {current_date} as the current date.")
    else:
        st.warning("No date found in the file name. Please use a filename like YYYY-MM-DD_tenants.csv.")
        current_date = None

    # Read CSV into DataFrame
    df = pd.read_csv(uploaded_file)
    st.subheader("CSV Preview")
    st.dataframe(df.head(20))
    
    # Show CSV schema
    st.subheader("CSV Schema")
    schema_df = pd.DataFrame({
        'Column': df.columns,
        'Data Type': df.dtypes.astype(str)
    })
    st.dataframe(schema_df)
    
    # Initialize database connection
    conn = sqldb.init_db(df)

    for idx, row in df.iterrows():
        row_tenant_value = row['Tenant']
        if pd.isna(row_tenant_value):
            continue
        if not row_tenant_value.isnumeric():
            tenant_id = sqldb.get_or_create_tenant(row_tenant_value)
        else:
            # For each day column (assuming columns '1', '2', '3' exist for days)
            if row_tenant_value in ['1', '2', '3'] and tenant_id is not None:
                data_date = sqldb.map_day_to_date(int(row_tenant_value), current_date)
                data_dict = row.drop('Tenant').to_dict()
                if not sqldb.tenant_data_exists(tenant_id, data_date):
                    sqldb.insert_tenant_data(tenant_id, data_date, data_dict)
        
    st.success("Data successfully added to the database!")
    

    # # Store in database
    # # Add analysis section
    # st.header("Database Analysis")
    # analysis = sqldb.analyze_table()
    # st.write(f"Total Records: {analysis['total_records']}")
    # st.write(f"Total Columns: {analysis['total_columns']}")

    # st.subheader("Column Statistics")
    # st.dataframe(analysis['column_stats'])

    # st.success("Data successfully added to the database!")
    

    user_question = st.text_input("Ask a question about the data:")

    if user_question:
        # Get all data for analysis
        all_data = sqldb.get_table_data("tenant_data")
        column_list = ', '.join(all_data.columns)
        # prompt = f"""
        #             You are a Python assistant. Given a Pandas DataFrame with these columns: {column_list},
        #             and this user question: "{user_question}", generate Python code using pandas that answers it.

        #             Do not load CSV or display plots. Just return the Python code for analysis.
        #             """
        # result = query_llm(prompt)
        # st.code(result, language='python')

        

        schema = [f"{row[1]} ({row[2]})" for row in schema_df]
        schema_str = ", ".join(schema)

        prompt = f"""
        You are an assistant that converts user questions into SQL queries for a MySQL database.

        The primary database is tenants_info. There are two tables:
        1. tenants_info.tenants â€” contains all tenants with:
            - 'Tenant' (tenant name, e.g., 'eab')
            - 'tenant_id' (unique ID)
        
        2. tenants_info.tenant_data â€” contains tenant-specific daily data, with:
            - 'tenant_id' (foreign key to tenants)
            - 'date' column (of DATE type) indicating the day of the record.
            - 'flows' column that corresponds to the number or count of flows
            - 'past_24hours_incidents' column that corresponds to the count of open incidents in last 24 hr
            - 'access_frm_uac' column that corresponds to the count of open incident for access from unauthorized countries
            - 'access_to_uac' column that corresponds to the count of open incident for access to unauthorized countries
            - 'access_to_ano_ip' column that corresponds to the count of open incident for access to anonymous IP
            - 'access_from_ano_ip' column that corresponds to the count of open incident for access from anonymous IP
            - 'access_to_pub_vpn' column that corresponds to the count of open incident for access to public VPN
            - 'access_from_pub_vpn' column that corresponds to the count of open incident for access from public VPN
            - 'ahq' column that corresponds to the count of open incident for auth hash quality
            - 'ahs' column that corresponds to the count of open incident for auth hash security
            - 'apq' column that corresponds to the count of open incident for auth protocol quality
            - 'comp_pass' column that corresponds to the count of open incident for compromised password
            - 'comp_user' column that corresponds to the count of open incident for compromised user
            - 'wp' column that corresponds to the count of open incident for weak password

            - 'NHI' column that corresponds to the count of non human identity
        
        If the user asks for data for a tenant by name, join with the tenants table to get tenant_id.
        If the user mentions a tenant by name (e.g., "eab"), first fetch its tenant_id from the tenants table and use it to filter tenant_data.
        If the user asks for recent data (e.g., "last 3 days"), filter using date >= CURDATE() - INTERVAL 3 DAY.

        If they ask for a percentage difference over time (e.g., "1% difference in the last 3 days"), compare the most recent and oldest values in the last 3 days for each numeric column, and return only the column names where the percent change is close to 1%.
        Numeric columns are:
        {", ".join(schema_str)}

        Assume you can use information_schema or metadata to dynamically find numeric columns if needed.

        Always return the SQL query as plain text, with no code formatting or extra explanation.

        User question: "{user_question}"
        """

        st.info(f"Generating SQL for \"{user_question}\"")
        sql_query = text_to_sql.query_llm_for_sql(prompt)
        sql_query = sql_query.replace("```sql", "").replace("```", "")
        
        st.code(sql_query, language='sq')
        try:
            result = sqldb.run_query(sql_query)
            st.dataframe(result)
        except Exception as e:
            st.error(f"Error executing SQL: {e}")

        st.markdown("âš ï¸ For safety, you must copy and run the code manually to verify it.")

    # Close database connection when done
    conn.close()

    st.subheader("Available Tenant CSV Files")
    tenant_files = os.listdir(tenant_data_dir)
    selected_tenant_file = st.selectbox("Select a tenant file to view:", tenant_files)
    if selected_tenant_file:
        tenant_df = pd.read_csv(os.path.join(tenant_data_dir, selected_tenant_file))
        st.dataframe(tenant_df)
