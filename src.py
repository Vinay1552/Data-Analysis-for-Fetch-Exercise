
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns


# Load the CSV files
users = pd.read_csv('USER_TAKEHOME.csv')
transactions = pd.read_csv('TRANSACTION_TAKEHOME.csv')
products = pd.read_csv('PRODUCTS_TAKEHOME.csv')


# 1. Check for missing values
print("Missing Values in Users:")
print(users.isnull().sum())
print("\nMissing Values in Transactions:")
print(transactions.isnull().sum())
print("\nMissing Values in Products:")
print(products.isnull().sum())

# 2. Check for duplicates in primary keys
# Users: ID should be unique
print("\nDuplicate IDs in Users:", users['ID'].duplicated().sum())
# Products: BARCODE should be unique (assuming each barcode represents one product)
print("Duplicate BARCODEs in Products:", products['BARCODE'].duplicated().sum())
# Transactions: RECEIPT_ID may not be unique if multiple items per receipt, check uniqueness of RECEIPT_ID + BARCODE
transactions['receipt_barcode'] = transactions['RECEIPT_ID'] + '_' + transactions['BARCODE'].astype(str)
print("Duplicate RECEIPT_ID + BARCODE in Transactions:", transactions['receipt_barcode'].duplicated().sum())

# 3. Check data types
print("\nUsers Data Types:")
print(users.dtypes)
print("\nTransactions Data Types:")
print(transactions.dtypes)
print("\nProducts Data Types:")
print(products.dtypes)



# Find rows where FINAL_QUANTITY contains alphabetic characters
alpha_quantities = transactions[transactions['FINAL_QUANTITY'].str.contains('[a-zA-Z]', na=True)]
print("\nRows with alphabetic characters in FINAL_QUANTITY:")
print(alpha_quantities[['FINAL_QUANTITY']].head())
print(f"Total rows with alphabetic characters: {len(alpha_quantities)}")

# Replace 'zero' with 0 in FINAL_QUANTITY
transactions.loc[transactions['FINAL_QUANTITY'] == 'zero', 'FINAL_QUANTITY'] = '0'

# Convert FINAL_QUANTITY and FINAL_SALE to numeric type
transactions['FINAL_QUANTITY'] = pd.to_numeric(transactions['FINAL_QUANTITY'], errors='coerce')

transactions['FINAL_SALE'] = pd.to_numeric(transactions['FINAL_SALE'], errors='coerce')

# 4. Check for invalid values
# Transactions: FINAL_QUANTITY and FINAL_SALE should be non-negative
print("\nNegative FINAL_QUANTITY:", (transactions['FINAL_QUANTITY'] < 0).sum())
print("Negative FINAL_SALE:", (transactions['FINAL_SALE'] < 0).sum())

# 5. Referential integrity
# Check if all USER_ID in Transactions exist in Users
missing_users = transactions[~transactions['USER_ID'].isin(users['ID'])]
print("\nTransactions with USER_ID not in Users:", len(missing_users))
# Check if all BARCODE in Transactions exist in Products
missing_products = transactions[~transactions['BARCODE'].isin(products['BARCODE'])]
print("Transactions with BARCODE not in Products:", len(missing_products))


# Convert date columns to datetime for analysis
users['CREATED_DATE'] = pd.to_datetime(users['CREATED_DATE'])
users['BIRTH_DATE'] = pd.to_datetime(users['BIRTH_DATE'])
transactions['PURCHASE_DATE'] = pd.to_datetime(transactions['PURCHASE_DATE'])
transactions['SCAN_DATE'] = pd.to_datetime(transactions['SCAN_DATE'])


# --- Visualization 1: Transactions Over Time ---
plt.figure(figsize=(12, 6))
transactions['SCAN_DATE'].dt.date.value_counts().sort_index().plot(kind='line')
plt.title('Number of Transactions Scanned Over Time')
plt.xlabel('Date')
plt.ylabel('Number of Transactions')
plt.grid(True)
plt.show()

# --- Visualization 2: Bar Chart of Top 10 Product Categories ---
plt.figure(figsize=(10, 6))
plt.yscale('log')
products['CATEGORY_1'].value_counts().head(10).plot(kind='bar', color='skyblue')
plt.title('Top 10 Product Categories')
plt.xlabel('Category')
plt.ylabel('Number of Products')
plt.xticks(rotation=45)
plt.show()

# 6. Examine categorical and date fields
print("\nUnique Values in Users - STATE:", users['STATE'].nunique())
print("Unique Values in Users - LANGUAGE:", users['LANGUAGE'].nunique())
print("Unique Values in Users - GENDER:", users['GENDER'].nunique())
print("Unique Values in Products - CATEGORY_1:", products['CATEGORY_1'].nunique())

# Date ranges (assuming dates are in 'YYYY-MM-DD' format)
users['CREATED_DATE'] = pd.to_datetime(users['CREATED_DATE'])
users['BIRTH_DATE'] = pd.to_datetime(users['BIRTH_DATE'])
transactions['PURCHASE_DATE'] = pd.to_datetime(transactions['PURCHASE_DATE'])
transactions['SCAN_DATE'] = pd.to_datetime(transactions['SCAN_DATE'])

print("\nCREATED_DATE Range:", users['CREATED_DATE'].min(), "to", users['CREATED_DATE'].max())
print("BIRTH_DATE Range:", users['BIRTH_DATE'].min(), "to", users['BIRTH_DATE'].max())
print("PURCHASE_DATE Range:", transactions['PURCHASE_DATE'].min(), "to", transactions['PURCHASE_DATE'].max())
print("SCAN_DATE Range:", transactions['SCAN_DATE'].min(), "to", transactions['SCAN_DATE'].max())


conn = sqlite3.connect(':memory:')

# Load dataframes into SQLite tables
users.to_sql('users', conn, index=False)
transactions.to_sql('transactions', conn, index=False)
products.to_sql('products', conn, index=False)


result1 = pd.read_sql_query("""
    SELECT p.BRAND, COUNT(DISTINCT t.RECEIPT_ID) AS receipt_count
    FROM transactions t
    JOIN products p ON t.BARCODE = p.BARCODE
    JOIN users u ON t.USER_ID = u.ID
    WHERE date(u.BIRTH_DATE, '+21 years') <= (SELECT MAX(SCAN_DATE) FROM transactions)
    GROUP BY p.BRAND
    ORDER BY receipt_count DESC
    LIMIT 5
""", conn)
print("Top 5 Brands by Receipts Scanned (Users 21+):\n", result1)


result2 = pd.read_sql_query("""
    SELECT p.BRAND, SUM(t.FINAL_SALE) AS total_sales
    FROM transactions t
    JOIN products p ON t.BARCODE = p.BARCODE
    JOIN users u ON t.USER_ID = u.ID
    WHERE u.CREATED_DATE <= date((SELECT MAX(SCAN_DATE) FROM transactions), '-6 months')
    GROUP BY p.BRAND
    ORDER BY total_sales DESC
    LIMIT 5
""", conn)
print("\nTop 5 Brands by Sales (Accounts 6+ Months):\n", result2)


result3 = pd.read_sql_query("""
    SELECT t.USER_ID, COUNT(DISTINCT t.RECEIPT_ID) AS receipt_count
    FROM transactions t
    GROUP BY t.USER_ID
    ORDER BY receipt_count DESC
    LIMIT 10
""", conn)
print("\nPower Users:\n", result3)
