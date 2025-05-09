import sqlite3
import pandas as pd
from datetime import datetime, timedelta

class DB:
    def __init__(self):
        self.conn = sqlite3.connect('clients.db')
        # self.conn = sqlite3.connect('tenants_data.db')
        self.cursor = self.conn.cursor()

    # Function to map Pandas data types to SQLite data types
    def get_sqlite_type(self,dtype):
        if dtype == 'object':  # String-like column
            return 'TEXT'
        elif dtype == 'int64':  # Integer column
            return 'INTEGER'
        elif dtype == 'float64':  # Float column
            return 'REAL'
        else:
            return 'TEXT'  # Default to TEXT

    # # Function to create SQLite table dynamically
    # def create_table_from_csv(df):
    #     # Connect to SQLite database (this creates the database if it doesn't exist)
    #     conn = sqlite3.connect('clients.db')
    #     cursor = conn.cursor()

    #     # Dynamically create table schema based on CSV headers and their data types
    #     columns = df.columns
    #     column_definitions = []

    #     for col in columns:
    #         # Get the data type of each column in the dataframe
    #         col_type = get_sqlite_type(df[col].dtype)
    #         column_definitions.append(f"{col} {col_type}")

    #     # Join all column definitions into a single string for SQL
    #     create_table_query = f"CREATE TABLE IF NOT EXISTS clients ({', '.join(column_definitions)});"

    #     # Execute the create table query
    #     cursor.execute(create_table_query)
    #     conn.commit()
    #     return conn, cursor

    # # Function to insert CSV data into the SQLite table
    # def insert_data_to_db(df, cursor):
        # for index, row in df.iterrows():
        #     cursor.execute(f'''
        #     INSERT INTO clients ({', '.join(df.columns)})
        #     VALUES ({', '.join('?' for _ in df.columns)})
        #     ''', tuple(row))
        
        # cursor.connection.commit()

    def init_db(self, df):
        """Initialize the database connection"""
        
        self.cursor = self.conn.cursor()
        # Create tenants table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tenants (
                tenant_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_name TEXT UNIQUE NOT NULL
            )
        ''')
        # Create tenant_data table
        base_cols = [
            'data_id INTEGER PRIMARY KEY AUTOINCREMENT',
            'tenant_id INTEGER NOT NULL',
            'data_date DATE NOT NULL',
            # 'tenant_name TEXT NOT NULL'
        ]
        # Add columns from CSV (all as TEXT for simplicity, or infer types if you wish)
        dynamic_cols = []
        for col, dtype in df.dtypes.items():
            sql_type = self.get_sqlite_type(dtype)
            dynamic_cols.append(f'"{col}" {sql_type}')

        all_cols = base_cols + dynamic_cols + ['FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)']
        create_sql = f'CREATE TABLE IF NOT EXISTS tenant_data ({", ".join(all_cols)})'
        self.cursor.execute(create_sql)
        self.conn.commit()
        
        return self.conn

    # def create_table(conn, df):
    #     """Create or update the main table with the DataFrame"""
    #     # Get column names and their SQLite data types
    #     columns = []
    #     for col, dtype in df.dtypes.items():
    #         sql_type = DB.get_sqlite_type(dtype)
    #         columns.append(f'"{col}" {sql_type}')
        
    #     # Create table if it doesn't exist
    #     create_table_sql = f"""
    #     CREATE TABLE IF NOT EXISTS tenants_data (
    #         {', '.join(columns)}
    #     )
    #     """
        
    #     cursor = conn.cursor()
    #     cursor.execute(create_table_sql)
    #     conn.commit()
        
    #     # Insert data
    #     df.to_sql('tenants_data', conn, if_exists='append', index=False)
    #     return 'tenants_data'

    def get_table_names(self):
        """Get all table names from the database"""
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [table[0] for table in self.cursor.fetchall()]

    def get_table_data(self, table_name):
        """Get all data from the main table"""
        query = f"SELECT * FROM {table_name}"
        return pd.read_sql_query(query, self.conn)

    def get_latest_records(self, limit=5):
        """Get the latest records from the table"""
        query = "SELECT * FROM tenant_data ORDER BY ROWID DESC LIMIT ?"
        return pd.read_sql_query(query, self.conn, params=(limit,))

    def get_table_schema(self):
        """Get the schema of the tenant_data table"""
        self.cursor.execute("PRAGMA table_info(tenant_data)")
        columns = self.cursor.fetchall()
        return columns

    def get_or_create_tenant(self, tenant_name):
        self.cursor.execute("SELECT tenant_id FROM tenants WHERE tenant_name = ?", (tenant_name,))
        row = self.cursor.fetchone()
        if row:
            return row[0]
        self.cursor.execute("INSERT INTO tenants (tenant_name) VALUES (?)", (tenant_name,))
        self.conn.commit()
        return self.cursor.lastrowid

    def insert_tenant_data(self, tenant_id, data_date, data_dict):
        tenant_name_query = f'''
            select tenant_name from tenants where tenant_id = {tenant_id}
        '''
        self.cursor.execute(tenant_name_query)
        tenant_name = self.cursor.fetchone()
        columns = ', '.join(['tenant_id', 'Date','Tenant'] +  list(data_dict.keys()))
        placeholders = ', '.join(['?'] * (3 + len(data_dict)))
        values = [tenant_id, data_date, tenant_name[0]] + list(data_dict.values())
        self.cursor.execute(f"INSERT INTO tenant_data ({columns}) VALUES ({placeholders})", values)
        self.conn.commit()

    def get_tenant_data(self, tenant_name=None):
        query = '''
            SELECT * FROM tenant_data d
            JOIN tenants t ON d.tenant_id = t.tenant_id
        '''
        if tenant_name:
            query += " WHERE t.tenant_name = ?"
            return pd.read_sql_query(query, self.conn, params=(tenant_name,))
        return pd.read_sql_query(query, self.conn)

    def map_day_to_date(self, day_num, date=None):
        # 3 = today, 2 = yesterday, 1 = 2 days ago
        if date is not None:
            if isinstance(date, str):
                today = datetime.strptime(date, "%Y-%m-%d").date()
            else:
                today = date
        else:
            today = datetime.today().date()
        if day_num == 3:
            return today
        elif day_num == 2:
            return today - timedelta(days=1)
        elif day_num == 1:
            return today - timedelta(days=2)
        else:
            return None
    
    def tenant_data_exists(self, tenant_id, data_date):
        self.cursor.execute(
            "SELECT 1 FROM tenant_data WHERE tenant_id = ? AND data_date = ?",
            (tenant_id, data_date)
        )
        return self.cursor.fetchone() is not None

    # def recreate_tenant_data_table(self,conn, csv_columns):
    #     cursor = conn.cursor()
    #     # Drop the table if it exists
    #     cursor.execute("DROP TABLE IF EXISTS tenant_data")
    #     # Always include these columns
    #     base_cols = [
    #         'data_id INTEGER PRIMARY KEY AUTOINCREMENT',
    #         'tenant_id INTEGER NOT NULL',
    #         'data_date DATE NOT NULL'
    #     ]
    #     # Add columns from CSV (all as TEXT for simplicity, or infer types if you wish)
    #     dynamic_cols = [f'"{col}" TEXT' for col in csv_columns if col not in ['tenant_id', 'data_date']]
    #     all_cols = base_cols + dynamic_cols + ['FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)']
    #     create_sql = f'CREATE TABLE tenant_data ({", ".join(all_cols)})'
    #     cursor.execute(create_sql)
    #     conn.commit()

if __name__ == "__main__":

    db = DB()
    # db.init_db()
    # db.create_table(db.init_db(), df)
    # # After reading the CSV
    # csv_headers = list(df.columns)
    # db.recreate_tenant_data_table(db.init_db(), csv_headers)
    # # Now insert data row by row, including tenant_id and data_date
    # db.insert_data_to_db(df, db.init_db())
    # db.get_table_names(db.init_db())
    # db.get_table_data(db.init_db())
    # db.get_latest_records(db.init_db())
