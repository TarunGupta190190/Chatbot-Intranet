import mysql.connector
import pandas as pd
from datetime import datetime, timedelta

class DB:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host='10.13.5.8',
            port=3306,
            user='tg',
            password='AuthMind@2024',
            database='tenants_info',
            autocommit=True
        )
        self.cursor = self.conn.cursor()

    def get_mysql_type(self, dtype):
        if dtype == 'object':
            return 'VARCHAR(255)'
        elif dtype == 'int64':
            return 'INT'
        elif dtype == 'float64':
            return 'FLOAT'
        else:
            return 'VARCHAR(255)'

    def init_db(self, df):
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tenants (
                tenant_id INT PRIMARY KEY AUTO_INCREMENT,
                Tenant VARCHAR(255) UNIQUE NOT NULL
            )
        ''')
        base_cols = [
            'data_id INT PRIMARY KEY AUTO_INCREMENT',
            'tenant_id INT NOT NULL',
            'date DATE NOT NULL'
        ]
        dynamic_cols = []
        for col, dtype in df.dtypes.items():
            if col == 'Tenant':
                continue  # Skip the Tenant column
            sql_type = self.get_mysql_type(dtype)
            dynamic_cols.append(f'`{col}` {sql_type}')
        all_cols = base_cols + dynamic_cols + ['FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)']
        create_sql = f'CREATE TABLE IF NOT EXISTS tenant_data ({", ".join(all_cols)})'
        self.cursor.execute(create_sql)
        self.conn.commit()
        return self.conn

    def get_table_names(self):
        self.cursor.execute("SHOW TABLES;")
        return [table[0] for table in self.cursor.fetchall()]

    def get_table_data(self, table_name):
        query = f"SELECT * FROM {table_name}"
        return pd.read_sql(query, self.conn)

    def get_latest_records(self, limit=5):
        query = "SELECT * FROM tenant_data ORDER BY data_id DESC LIMIT %s"
        self.cursor.execute(query, (limit,))
        columns = [desc[0] for desc in self.cursor.description]
        rows = self.cursor.fetchall()
        return pd.DataFrame(rows, columns=columns)

    def get_table_schema(self):
        self.cursor.execute("DESCRIBE tenant_data")
        columns = self.cursor.fetchall()
        return columns

    def get_or_create_tenant(self, tenant_name):
        self.cursor.execute("SELECT tenant_id FROM tenants WHERE Tenant = %s", (tenant_name,))
        row = self.cursor.fetchone()
        if row:
            return row[0]
        self.cursor.execute("INSERT INTO tenants (Tenant) VALUES (%s)", (tenant_name,))
        self.conn.commit()
        return self.cursor.lastrowid

    def insert_tenant_data(self, tenant_id, data_date, data_dict):
        columns = ', '.join(['tenant_id', 'date'] + list(data_dict.keys()))
        placeholders = ', '.join(['%s'] * (2 + len(data_dict)))
        values = [tenant_id, data_date] + list(data_dict.values())
        self.cursor.execute(f"INSERT INTO tenant_data ({columns}) VALUES ({placeholders})", values)
        self.conn.commit()

    def get_tenant_data(self, tenant_name=None):
        query = '''
            SELECT * FROM tenant_data d
            JOIN tenants t ON d.tenant_id = t.tenant_id
        '''
        if tenant_name:
            query += " WHERE t.Tenant = %s"
            return pd.read_sql(query, self.conn, params=(tenant_name,))
        return pd.read_sql(query, self.conn)

    def map_day_to_date(self, day_num, date=None):
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
            "SELECT 1 FROM tenant_data WHERE tenant_id = %s AND date = %s",
            (tenant_id, data_date)
        )
        return self.cursor.fetchone() is not None

    def run_query(self, query, params=None):
        """
        Execute an arbitrary SQL query and return the results as a pandas DataFrame.
        :param query: SQL query string
        :param params: Optional tuple/list of parameters for parameterized queries
        :return: pandas DataFrame with the results
        """
        if params is not None:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        columns = [desc[0] for desc in self.cursor.description]
        rows = self.cursor.fetchall()
        return pd.DataFrame(rows, columns=columns)

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

