import sqlite3

def fix_departments():
    print("Fixing departments...")
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # 1. Reassign all students from the long department names to the short ones
    cursor.execute("""
        UPDATE core_student 
        SET department_id = (SELECT dept_id FROM core_department WHERE dept_name = 'CSE') 
        WHERE department_id = (SELECT dept_id FROM core_department WHERE dept_name = 'Computer Science & Engineering')
    """)
    
    cursor.execute("""
        UPDATE core_student 
        SET department_id = (SELECT dept_id FROM core_department WHERE dept_name = 'EEE') 
        WHERE department_id = (SELECT dept_id FROM core_department WHERE dept_name = 'Electrical & Electronic Engineering')
    """)
    
    cursor.execute("""
        UPDATE core_student 
        SET department_id = (SELECT dept_id FROM core_department WHERE dept_name = 'Pharmacy') 
        WHERE department_id = (SELECT dept_id FROM core_department WHERE dept_name = 'Mechanical Engineering')
    """)
    
    cursor.execute("""
        UPDATE core_student 
        SET department_id = (SELECT dept_id FROM core_department WHERE dept_name = 'BBA') 
        WHERE department_id = (SELECT dept_id FROM core_department WHERE dept_name = 'Business Administration')
    """)

    # 2. Delete the long department names
    cursor.execute("""
        DELETE FROM core_department 
        WHERE dept_name IN (
            'Computer Science & Engineering', 
            'Electrical & Electronic Engineering', 
            'Mechanical Engineering', 
            'Business Administration'
        )
    """)
        
    conn.commit()
    conn.close()
    print("Successfully cleaned up the departments!")

if __name__ == '__main__':
    fix_departments()
