import sqlite3

def add_departments():
    print("Connecting to database...")
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    departments = ['CSE', 'EEE', 'Pharmacy', 'BBA']
    
    for dept in departments:
        print(f"Adding department: {dept}")
        cursor.execute("INSERT INTO core_department (dept_name) VALUES (?)", (dept,))
        
    conn.commit()
    conn.close()
    print("Successfully added all departments!")

if __name__ == '__main__':
    add_departments()
