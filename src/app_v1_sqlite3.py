import pandas as pd
import requests
import streamlit as st
from db import DB as sqldb
from text_to_sql import text_to_sql

import re

sqldb = sqldb()
text_to_sql =  text_to_sql()
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-coder:16b-v2"


st.title("📊 Tenants Information System")
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
    
    # Show available tables
    st.subheader("Available Tables in Database")
    tables = sqldb.get_table_names()
    selected_table = st.selectbox("Select a table to view:", tables)
    if selected_table:
        table_data = sqldb.get_table_data(selected_table)
        st.dataframe(table_data.head(20))

    # # Store in database
    # # Add analysis section
    # st.header("Database Analysis")
    # analysis = sqldb.analyze_table()
    # st.write(f"Total Records: {analysis['total_records']}")
    # st.write(f"Total Columns: {analysis['total_columns']}")

    # st.subheader("Column Statistics")
    # st.dataframe(analysis['column_stats'])

    # st.success("Data successfully added to the database!")
    
    # Show database schema
    st.subheader("Database Schema")
    db_schema = sqldb.get_table_schema()
    schema_df = pd.DataFrame(db_schema, columns=['cid', 'name', 'type', 'notnull', 'dflt_value', 'pk'])
    st.dataframe(schema_df[['name', 'type']])
    
    # Show latest records
    st.subheader("Latest Records in Database")
    latest_data = sqldb.get_latest_records()
    st.dataframe(latest_data)

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

        

        schema = [f"{row[1]} ({row[2]})" for row in db_schema]
        schema_str = ", ".join(schema)
        prompt = f"""
        You are an assistant that converts user questions into SQL queries for a SQLite database.
        The main table is called tenant_data. Here is the schema:
        {schema_str}
        Return only the SQL query as plain text. Do not include any code block formatting, triple backticks, or language tags. Output only the SQL statement.


        User question: "{user_question}"
        """
        st.info(f"Generating SQL for \"{user_question}\"")
        sql_query = text_to_sql.query_llm_for_sql(prompt)
        sql_query = sql_query.replace("```sql", "").replace("```", "")
        
        st.code(sql_query, language='sq')
        try:
            result = pd.read_sql_query(sql_query, conn)
            st.dataframe(result)
        except Exception as e:
            st.error(f"Error executing SQL: {e}")

        st.markdown("⚠️ For safety, you must copy and run the code manually to verify it.")

    # Close database connection when done
    conn.close()
