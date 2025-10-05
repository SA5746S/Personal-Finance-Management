import sqlite3
from datetime import datetime
import hashlib

# ---------------------- DATABASE SETUP ----------------------
conn = sqlite3.connect("finance.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT,
    category TEXT,
    amount REAL,
    date TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    category TEXT,
    limit_amount REAL,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")
conn.commit()

# ---------------------- HELPER FUNCTIONS ----------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------------- USER FUNCTIONS ----------------------
def register():
    username = input("Enter Username: ")
    password = input("Enter Password: ")
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                       (username, hash_password(password)))
        conn.commit()
        print("Registration Successful!")
    except sqlite3.IntegrityError:
        print("Username already exists!")

def login():
    username = input("Enter Username: ")
    password = input("Enter Password: ")
    cursor.execute("SELECT id FROM users WHERE username=? AND password=?", 
                   (username, hash_password(password)))
    user = cursor.fetchone()
    if user:
        print("Login Successful!")
        return user[0]
    else:
        print("Invalid credentials!")
        return None

# ---------------------- TRANSACTION FUNCTIONS ----------------------
def add_transaction(user_id):
    t_type = input("Type (income/expense): ").lower()
    category = input("Category: ")
    amount = float(input("Amount: "))
    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO transactions (user_id, type, category, amount, date) VALUES (?, ?, ?, ?, ?)",
                   (user_id, t_type, category, amount, date))
    conn.commit()
    print(f"{t_type.capitalize()} added successfully!")

def view_transactions(user_id):
    cursor.execute("SELECT id, type, category, amount, date FROM transactions WHERE user_id=?", (user_id,))
    transactions = cursor.fetchall()
    if not transactions:
        print("No transactions found.")
    else:
        print("ID | Type | Category | Amount | Date")
        for t in transactions:
            print(t)

def delete_transaction():
    transaction_id = int(input("Enter Transaction ID to delete: "))
    cursor.execute("DELETE FROM transactions WHERE id=?", (transaction_id,))
    conn.commit()
    print("Transaction deleted successfully!")

# ---------------------- BUDGET FUNCTIONS ----------------------
def set_budget(user_id):
    category = input("Enter Category: ")
    limit_amount = float(input("Enter Budget Limit: "))
    cursor.execute("INSERT OR REPLACE INTO budgets (user_id, category, limit_amount) VALUES (?, ?, ?)",
                   (user_id, category, limit_amount))
    conn.commit()
    print(f"Budget set for {category}: {limit_amount}")

def check_budget(user_id):
    cursor.execute("""
        SELECT b.category, b.limit_amount, IFNULL(SUM(t.amount),0) 
        FROM budgets b 
        LEFT JOIN transactions t ON b.category=t.category AND t.user_id=b.user_id AND t.type='expense'
        WHERE b.user_id=?
        GROUP BY b.category
    """, (user_id,))
    results = cursor.fetchall()
    if not results:
        print("No budgets set.")
        return
    for category, limit, spent in results:
        print(f"{category}: Spent {spent} / Budget {limit}")
        if spent > limit:
            print(f"⚠️  You have exceeded your budget for {category}!")

# ---------------------- REPORT FUNCTIONS ----------------------
def monthly_report(user_id):
    month = int(input("Enter month (1-12): "))
    year = int(input("Enter year (YYYY): "))
    cursor.execute("""
        SELECT type, SUM(amount) 
        FROM transactions 
        WHERE user_id=? AND strftime('%m', date)=? AND strftime('%Y', date)=?
        GROUP BY type
    """, (user_id, f"{month:02}", str(year)))
    results = cursor.fetchall()
    income = sum(amount for t, amount in results if t=='income')
    expense = sum(amount for t, amount in results if t=='expense')
    savings = income - expense
    print(f"Monthly Report ({month}/{year}) -> Income: {income}, Expense: {expense}, Savings: {savings}")

# ---------------------- MAIN MENU ----------------------
def user_menu(user_id):
    while True:
        print("\n1. Add Transaction  2. View Transactions  3. Delete Transaction")
        print("4. Set Budget  5. Check Budget  6. Monthly Report  7. Logout")
        choice = input("Choose an option: ")
        if choice == '1':
            add_transaction(user_id)
        elif choice == '2':
            view_transactions(user_id)
        elif choice == '3':
            delete_transaction()
        elif choice == '4':
            set_budget(user_id)
        elif choice == '5':
            check_budget(user_id)
        elif choice == '6':
            monthly_report(user_id)
        elif choice == '7':
            break
        else:
            print("Invalid choice!")

def main():
    print("=== Welcome to Personal Finance Manager ===")
    while True:
        print("\n1. Register  2. Login  3. Exit")
        choice = input("Choose an option: ")
        if choice == '1':
            register()
        elif choice == '2':
            user_id = login()
            if user_id:
                user_menu(user_id)
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()
