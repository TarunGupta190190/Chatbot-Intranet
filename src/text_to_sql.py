import pandas as pd
import streamlit as st
from db import DB
import requests

class LLMHandler:
    def __init__(self) -> None:
        pass

    def query_llm_for_sql(self, prompt):

        # Call your LLM API (Ollama)
        response = requests.post(
            "http://10.13.5.8:11434/api/generate",
            json={"model": "deepseek-coder-v2", "prompt": prompt, "stream": False}
        )
        return response.json()["response"].strip()

    def query_llm(self, prompt):
        response = requests.post(
            "http://10.13.5.8:11434/api/generate",
            json={"model": "deepseek-coder-v2", "prompt": prompt, "stream": False}
        )
        return response.json()["response"].strip()

        # API_URL = "https://api-inference.huggingface.co/models/defog/sqlcoder-7b-2"
        # headers = {"Authorization": f"Bearer {st.secrets['HF_API_TOKEN']}"}
        # st.code(headers, language='sq')
        # payload = {
        #     "inputs": f"Convert this to SQL:\n{prompt}",
        #     "parameters": {"max_new_tokens": 100},
        # }
        # response = requests.post(API_URL, headers=headers, json=payload)
        # st.code(response, language='sq')
        # result = response.json()
        # return result[0]["generated_text"] if isinstance(result, list) else str(result)

# Get schema for prompt
# cursor = conn.cursor()
# cursor.execute("PRAGMA table_info(tenant_data)")
# schema = [f"{row[1]} ({row[2]})" for row in cursor.fetchall()]
# schema_str = ", ".join(schema)

# st.subheader("Ask a question about the data:")
# user_question = st.text_input("Enter your question:")

# if user_question:
#     sql_query = query_llm_for_sql(user_question, schema_str)
#     st.code(sql_query, language='sql')
#     try:
#         result = pd.read_sql_query(sql_query, conn)
#         st.dataframe(result)
#     except Exception as e:
#         st.error(f"Error executing SQL: {e}")

# conn.close()
