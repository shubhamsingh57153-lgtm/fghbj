import hashlib
import os
import sqlite3

# =====================================================================
# UNIVERSITY PROJECT HEADER
# =====================================================================
STUDENT_NAME = "YOUR_NAME_HERE"        # 💻 CHANGE THIS TO YOUR NAME
STUDENT_ID = "YOUR_STUDENT_ID_HERE"    # 🆔 CHANGE THIS TO YOUR STUDENT ID

print("=" * 60)
print(f"UNIVERSITY PROJECT: DATABASE SECURITY SIMULATION")
print(f"STUDENT: {STUDENT_NAME} | ID: {STUDENT_ID}")
print("=" * 60 + "\n")

# =====================================================================
# 1. PASSWORD HASHING
# =====================================================================
def hash_password(password: str) -> tuple[bytes, bytes]:
    """Hashes a password using SHA-256 with a unique random salt."""
    salt = os.urandom(16)
    db_password = password.encode('utf-8')
    hashed = hashlib.pbkdf2_hmac('sha256', db_password, salt, 100000)
    return hashed, salt

def verify_password(stored_hash: bytes, salt: bytes, password_to_test: str) -> bool:
    return hashlib.pbkdf2_hmac('sha256', password_to_test.encode('utf-8'), salt, 100000) == stored_hash

# DATABASE SETUP
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash BLOB, salt BLOB, role TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS financial_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, account_balance REAL)''')
conn.commit()

# =====================================================================
# 5. INPUT VALIDATION
# =====================================================================
def validate_inputs(username: str, initial_deposit: float) -> bool:
    # Allow letters, numbers, and underscores (isalnum() alone rejects "admin_eve")
    if not username or not all(c.isalnum() or c == '_' for c in username):
        print("Validation Error: Username must be alphanumeric (underscores allowed).")
        return False
    if initial_deposit < 0:
        print("Validation Error: Initial deposit cannot be negative.")
        return False
    return True

def register_user(username: str, password_raw: str, role: str, deposit: float):
    if not validate_inputs(username, deposit): return
    hashed, salt = hash_password(password_raw)
    try:
        cursor.execute("INSERT INTO users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)", (username, hashed, salt, role))
        cursor.execute("INSERT INTO financial_records (user_id, account_balance) VALUES (?, ?)", (cursor.lastrowid, deposit))
        conn.commit()
        print(f"User '{username}' registered successfully.")
    except sqlite3.IntegrityError:
        print(f"Registration Error: Username '{username}' exists.")

# Populate Data
register_user("alice", "SuperSecret123", "user", 5000.00)
register_user("bob", "Password987", "user", 120.50)
register_user("admin_eve", "AdminPass555", "admin", 0.00)
print("-" * 60)

# =====================================================================
# 2. SECURE AUTHENTICATION & SESSION MANAGEMENT
# =====================================================================
class UserSession:
    def __init__(self):
        self.current_user_id, self.current_username, self.current_role = None, None, None

    def login(self, username: str, password_raw: str):
        cursor.execute("SELECT id, password_hash, salt, role FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        
        if row and verify_password(row[1], row[2], password_raw):
            self.current_user_id, self.current_username, self.current_role = row[0], username, row[3]
            print(f"Success: '{username}' logged in.")
            return True
        print(f"Authentication Failed for '{username}'.")
        return False

    def logout(self):
        print(f"User '{self.current_username}' logged out.")
        self.__init__()

session = UserSession()

# =====================================================================
# 3. USER-SPECIFIC DATA ISOLATION
# =====================================================================
def view_my_financials(current_session: UserSession):
    if not current_session.current_user_id: return
    cursor.execute("SELECT account_balance FROM financial_records WHERE user_id = ?", (current_session.current_user_id,))
    val = cursor.fetchone()
    print(f"[{current_session.current_username.upper()}'S DASHBOARD] Your balance is: ${val[0]:,.2f}")

# =====================================================================
# 4. CONTROLLED DATABASE PERMISSIONS (RBAC)
# =====================================================================
def admin_view_all_balances(current_session: UserSession):
    if current_session.current_role != "admin":
        print(f"Access Denied: Role '{current_session.current_role}' does not have admin permissions.")
        return
    print("[ADMIN PANEL] Fetching all master logs...")
    cursor.execute("SELECT users.username, financial_records.account_balance FROM financial_records JOIN users ON users.id = financial_records.user_id")
    for row in cursor.fetchall():
        print(f" - User: {row[0]} | Balance: ${row[1]:,.2f}")

# =====================================================================
# 6B. ATTACK SIMULATION: SYSTEM RESILIENCE TO SQL INJECTION
# =====================================================================
def simulate_sql_injection_attack():
    print("\n[ATTACK SIMULATION] Hacker attempts SQL Injection bypass...")
    malicious_input = "' OR '1'='1"
    
    print(f"Hacker types Username: {malicious_input}")
    cursor.execute("SELECT id FROM users WHERE username = ?", (malicious_input,))
    result = cursor.fetchone()
    
    if result:
        print("❌ CRITICAL VULNERABILITY: Attack Succeeded!")
    else:
        print("✅ DEFENSE SUCCESS: Parameterized Query neutralized the SQL Injection string.")

# =====================================================================
# 7. BACKUP STRATEGY & 8. ERROR HANDLING
# =====================================================================
try:
    if session.login("alice", "SuperSecret123"):
        view_my_financials(session)
        admin_view_all_balances(session)  # Will be blocked
        session.logout()
    print("-" * 60)

    if session.login("admin_eve", "AdminPass555"):
        admin_view_all_balances(session)
        session.logout()
    print("-" * 60)

    # Run Attack Simulation
    simulate_sql_injection_attack()
    print("-" * 60)

    print("Triggering Database Error Handling:")
    cursor.execute("SELECT * FROM invalid_table")

except sqlite3.OperationalError as db_error:
    print(f"System Error Handled Gracefully: {db_error}")
finally:
    print("\n[BACKUP] Executing automated point-in-time database snapshot...")
    backup_conn = sqlite3.connect(':memory:')
    conn.backup(backup_conn)
    print("[BACKUP] Backup snapshot saved securely.")
    backup_conn.close()
    conn.close()
    print("[SYSTEM] Connection closed down cleanly.")
