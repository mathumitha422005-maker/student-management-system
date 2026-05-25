import sqlite3
import csv
import os

# ============================================================
#                   ADMIN CREDENTIALS
# ============================================================
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Lambda — calculate grade from marks
get_grade = lambda marks: (
    "O"  if marks >= 90 else
    "A+" if marks >= 80 else
    "A"  if marks >= 70 else
    "B+" if marks >= 60 else
    "B"  if marks >= 50 else
    "F"
)

# ============================================================
#                   STUDENT CLASS
# ============================================================
class Student:
    def __init__(self, regno, name, phone, city, department, year, semester):
        self.regno      = regno
        self.name       = name
        self.phone      = phone
        self.city       = city
        self.department = department
        self.year       = year
        self.semester   = semester

    def view_details(self):
        print("\n==============================")
        print("      STUDENT DETAILS         ")
        print("==============================")
        print(f"Regno      : {self.regno}")
        print(f"Name       : {self.name}")
        print(f"Phone      : {self.phone}")
        print(f"City       : {self.city}")
        print(f"Department : {self.department}")
        print(f"Year       : {self.year}")
        print(f"Semester   : {self.semester}")
        print("==============================")

    def view_marks(self, cursor):
        cursor.execute("""
            SELECT s.name, m.subject_code, m.subject_name, m.marks, m.grade, m.semester
            FROM students s
            JOIN marks m ON s.regno = m.regno
            WHERE s.regno = ?
        """, (self.regno,))
        marks = cursor.fetchall()
        if not marks:
            print("No marks found!")
        else:
            print("\n==============================")
            print("          MARKS               ")
            print("==============================")
            for m in marks:
                print(f"Subject : {m[2]} | Marks : {m[3]} | Grade : {m[4]}")
                print("------------------------------")

    def view_attendance(self, cursor):
        cursor.execute("""
            SELECT s.name, a.subject_name, a.total_classes, a.attended, a.date, a.status
            FROM students s
            JOIN attendance a ON s.regno = a.regno
            WHERE s.regno = ?
        """, (self.regno,))
        records = cursor.fetchall()
        if not records:
            print("No attendance records found!")
        else:
            print("\n==============================")
            print("        ATTENDANCE            ")
            print("==============================")
            for r in records:
                pct = (r[3]/r[2]*100) if r[2] > 0 else 0
                print(f"Subject    : {r[1]}")
                print(f"Attended   : {r[3]}/{r[2]} ({pct:.1f}%)")
                print(f"Date       : {r[4]} | Status : {r[5]}")
                print("------------------------------")

    def view_fees(self, cursor):
        cursor.execute("""
            SELECT f.amount, f.status, f.date, f.semester
            FROM students s
            JOIN fees f ON s.regno = f.regno
            WHERE s.regno = ?
        """, (self.regno,))
        fees = cursor.fetchall()
        if not fees:
            print("No fee records found!")
        else:
            print("\n==============================")
            print("           FEES               ")
            print("==============================")
            for f in fees:
                print(f"Amount   : Rs.{f[0]} | Status : {f[1]}")
                print(f"Date     : {f[2]} | Semester : {f[3]}")
                print("------------------------------")

    def view_result(self, cursor):
        cursor.execute("""
            SELECT m.subject_name, m.marks, m.grade
            FROM students s
            JOIN marks m ON s.regno = m.regno
            WHERE s.regno = ? AND m.semester = ?
        """, (self.regno, self.semester))
        results = cursor.fetchall()
        if not results:
            print("No results found!")
        else:
            print("\n==============================")
            print("          RESULT              ")
            print("==============================")
            total = 0
            for r in results:
                print(f"Subject : {r[0]} | Marks : {r[1]} | Grade : {r[2]}")
                total += r[1]
            avg = total / len(results)
            print(f"------------------------------")
            print(f"Total   : {total} | Average : {avg:.1f}")
            print("==============================")

# ============================================================
#                   COLLEGE CLASS
# ============================================================
class College:
    def __init__(self):
        self.is_logged_in = False
        self.conn   = sqlite3.connect("students.db")
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                regno TEXT PRIMARY KEY, name TEXT, phone TEXT,
                city TEXT, department TEXT, year TEXT,
                semester TEXT, password TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS marks (
                regno TEXT, subject_code TEXT, subject_name TEXT,
                marks INTEGER, grade TEXT, semester TEXT,
                FOREIGN KEY (regno) REFERENCES students(regno)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                regno TEXT, subject_code TEXT, subject_name TEXT,
                date TEXT, status TEXT, total_classes INTEGER, attended INTEGER,
                FOREIGN KEY (regno) REFERENCES students(regno)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS fees (
                regno TEXT, amount INTEGER, status TEXT,
                date TEXT, semester INTEGER,
                FOREIGN KEY (regno) REFERENCES students(regno)
            )
        """)
        self.conn.commit()

    def generate_regno(self, department, year):
        self.cursor.execute(
            "SELECT COUNT(*) FROM students WHERE department=? AND year=?",
            (department, year)
        )
        count     = self.cursor.fetchone()[0] + 1
        dept_code = department[:2].upper()
        return f"SNS{year}{dept_code}{count:03d}"

    def admin_login(self, username, password):
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            self.is_logged_in = True
            print("Admin Login Successful!")
            return True
        print("Invalid credentials!")
        return False

    def admin_logout(self):
        self.is_logged_in = False

    def find_student(self, regno, password):
        self.cursor.execute(
            "SELECT * FROM students WHERE regno=? AND password=?",
            (regno, password)
        )
        s = self.cursor.fetchone()
        if s:
            return Student(s[0], s[1], s[2], s[3], s[4], s[5], s[6])
        return None

    def add_student(self):
        if not self.is_logged_in:
            print("Access Denied!")
            return
        print("\n--- ADD STUDENT ---")
        name = input("Name: ")
        while True:
            phone = input("Phone (10 digits): ")
            if len(phone) == 10 and phone.isdigit():
                break
            print("Invalid phone!")
        city       = input("City: ")
        department = input("Department (CSE/IT/ECE/EEE/MECH): ").upper()
        year       = input("Year (1/2/3/4): ")
        semester   = input("Semester: ")
        while True:
            password = input("Password (min 4 chars): ")
            if len(password) >= 4:
                break
            print("Too short!")
        regno = self.generate_regno(department, year)
        self.cursor.execute(
            "INSERT INTO students VALUES (?,?,?,?,?,?,?,?)",
            (regno, name, phone, city, department, year, semester, password)
        )
        self.conn.commit()
        print(f"Student Added! Regno: {regno}")

    def bulk_add_students(self, csv_file):
        if not self.is_logged_in:
            print("Access Denied!")
            return
        if not os.path.exists(csv_file):
            print(f"File not found: {csv_file}")
            return
        print(f"Importing from {csv_file}...")
        count = 0
        with open(csv_file, 'r', newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                regno = self.generate_regno(row['department'].upper(), row['year'])
                try:
                    self.cursor.execute(
                        "INSERT INTO students VALUES (?,?,?,?,?,?,?,?)",
                        (regno, row['name'], row['phone'], row['city'],
                         row['department'].upper(), row['year'], row['semester'], row['password'])
                    )
                    count += 1
                    print(f"Added: {row['name']} | Regno: {regno}")
                except Exception as e:
                    print(f"Error: {row['name']} — {e}")
        self.conn.commit()
        print(f"Total {count} students added!")

    def bulk_add_marks(self, csv_file):
        if not self.is_logged_in:
            print("Access Denied!")
            return
        if not os.path.exists(csv_file):
            print(f"File not found: {csv_file}")
            return
        print(f"Importing marks from {csv_file}...")
        count = 0
        with open(csv_file, 'r', newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                marks = int(row['marks'])
                if marks < 0 or marks > 100:
                    print(f"Invalid marks {marks} for {row['regno']} — skipping!")
                    continue
                grade = get_grade(marks)
                try:
                    self.cursor.execute(
                        "INSERT INTO marks VALUES (?,?,?,?,?,?)",
                        (row['regno'], row['subject_code'], row['subject_name'],
                         marks, grade, row['semester'])
                    )
                    count += 1
                    print(f"{row['regno']} | {row['subject_name']} | {marks} | {grade}")
                except Exception as e:
                    print(f"Error: {e}")
        self.conn.commit()
        print(f"Total {count} marks added!")

    def promote_students(self, department, current_year):
        if not self.is_logged_in:
            print("Access Denied!")
            return
        next_year     = str(int(current_year) + 1)
        next_semester = str(int(current_year) * 2 + 1)
        self.cursor.execute(
            "SELECT COUNT(*) FROM students WHERE department=? AND year=?",
            (department, current_year)
        )
        count = self.cursor.fetchone()[0]
        if count == 0:
            print(f"No students in {department} Year {current_year}!")
            return
        confirm = input(f"Promote {count} students to Year {next_year}? (yes/no): ")
        if confirm.lower() != "yes":
            print("Cancelled!")
            return
        self.cursor.execute(
            "UPDATE students SET year=?, semester=? WHERE department=? AND year=?",
            (next_year, next_semester, department, current_year)
        )
        self.conn.commit()
        print(f"{count} students promoted to Year {next_year}!")

    def view_all_students(self):
        self.cursor.execute("SELECT * FROM students")
        students = self.cursor.fetchall()
        if not students:
            print("No students found!")
            return
        # Lambda — sort by name
        sorted_students = sorted(students, key=lambda s: s[1])
        print("\n==============================")
        print("       ALL STUDENTS           ")
        print("==============================")
        for s in sorted_students:
            print(f"Regno : {s[0]} | Name : {s[1]} | Dept : {s[4]} | Year : {s[5]}")
        print("==============================")

    def search_student(self):
        regno = input("Enter regno: ")
        self.cursor.execute("SELECT * FROM students WHERE regno=?", (regno,))
        s = self.cursor.fetchone()
        if s:
            print(f"\nRegno : {s[0]} | Name : {s[1]}")
            print(f"Dept  : {s[4]} | Year : {s[5]} | Sem : {s[6]}")
        else:
            print("Student not found!")

    def update_marks(self):
        if not self.is_logged_in:
            print("Access Denied!")
            return
        regno = input("Enter regno: ")
        self.cursor.execute("SELECT * FROM students WHERE regno=?", (regno,))
        if not self.cursor.fetchone():
            print("Student not found!")
            return
        subject_code = input("Subject code: ")
        subject_name = input("Subject name: ")
        semester     = input("Semester: ")
        while True:
            try:
                marks = int(input("Marks (0-100): "))
                if 0 <= marks <= 100:
                    break
                print("Invalid marks!")
            except ValueError:
                print("Enter a number!")
        grade = get_grade(marks)
        self.cursor.execute(
            "INSERT INTO marks VALUES (?,?,?,?,?,?)",
            (regno, subject_code, subject_name, marks, grade, semester)
        )
        self.conn.commit()
        print(f"Marks updated! Grade: {grade}")

    def update_attendance(self):
        if not self.is_logged_in:
            print("Access Denied!")
            return
        regno = input("Enter regno: ")
        self.cursor.execute("SELECT * FROM students WHERE regno=?", (regno,))
        if not self.cursor.fetchone():
            print("Student not found!")
            return
        subject_code  = input("Subject code: ")
        subject_name  = input("Subject name: ")
        date          = input("Date (DD-MM-YYYY): ")
        status        = input("Present/Absent: ")
        total_classes = int(input("Total classes: "))
        attended      = int(input("Attended: "))
        self.cursor.execute(
            "INSERT INTO attendance VALUES (?,?,?,?,?,?,?)",
            (regno, subject_code, subject_name, date, status, total_classes, attended)
        )
        self.conn.commit()
        print("Attendance updated!")

    def update_fees(self):
        if not self.is_logged_in:
            print("Access Denied!")
            return
        regno = input("Enter regno: ")
        self.cursor.execute("SELECT * FROM students WHERE regno=?", (regno,))
        if not self.cursor.fetchone():
            print("Student not found!")
            return
        amount   = int(input("Fee amount: Rs."))
        status   = input("Status (Paid/Pending): ")
        date     = input("Date (DD-MM-YYYY): ")
        semester = int(input("Semester: "))
        self.cursor.execute(
            "INSERT INTO fees VALUES (?,?,?,?,?)",
            (regno, amount, status, date, semester)
        )
        self.conn.commit()
        print("Fee record updated!")

    def delete_student(self):
        if not self.is_logged_in:
            print("Access Denied!")
            return
        regno = input("Enter regno to delete: ")
        self.cursor.execute("SELECT * FROM students WHERE regno=?", (regno,))
        s = self.cursor.fetchone()
        if not s:
            print("Student not found!")
            return
        confirm = input(f"Delete {s[1]}? (yes/no): ")
        if confirm.lower() == "yes":
            self.cursor.execute("DELETE FROM students WHERE regno=?", (regno,))
            self.cursor.execute("DELETE FROM marks WHERE regno=?", (regno,))
            self.cursor.execute("DELETE FROM attendance WHERE regno=?", (regno,))
            self.cursor.execute("DELETE FROM fees WHERE regno=?", (regno,))
            self.conn.commit()
            print("Student deleted!")
        else:
            print("Cancelled!")

    def view_department_wise(self):
        dept = input("Enter department: ").upper()
        self.cursor.execute(
            "SELECT * FROM students WHERE department=?", (dept,)
        )
        students = self.cursor.fetchall()
        if not students:
            print(f"No students in {dept}!")
            return
        # Lambda — sort by year then name
        sorted_students = sorted(students, key=lambda s: (s[5], s[1]))
        print(f"\n--- {dept} STUDENTS ---")
        for s in sorted_students:
            print(f"Regno : {s[0]} | Name : {s[1]} | Year : {s[5]}")

    def view_failed_students(self):
        self.cursor.execute("""
            SELECT s.name, s.regno, m.subject_name, m.marks
            FROM students s JOIN marks m ON s.regno = m.regno
        """)
        all_marks = self.cursor.fetchall()
        # Lambda — filter failed marks
        failed = list(filter(lambda m: m[3] < 50, all_marks))
        if not failed:
            print("No failed students!")
        else:
            print("\n--- FAILED STUDENTS ---")
            for f in failed:
                print(f"{f[0]} | {f[1]} | {f[2]} | Marks: {f[3]}")

    def close(self):
        self.conn.close()

# ============================================================
#                   MENU FUNCTIONS
# ============================================================
def student_menu(student, college):
    while True:
        print(f"\n--- WELCOME {student.name.upper()} ---")
        print("1. View Details")
        print("2. View Marks")
        print("3. View Attendance")
        print("4. View Fees")
        print("5. View Result")
        print("6. Logout")
        choice = input("Choice: ")
        if choice == "1": student.view_details()
        elif choice == "2": student.view_marks(college.cursor)
        elif choice == "3": student.view_attendance(college.cursor)
        elif choice == "4": student.view_fees(college.cursor)
        elif choice == "5": student.view_result(college.cursor)
        elif choice == "6":
            print("Logged out!")
            break
        else: print("Invalid choice!")

def admin_menu(college):
    while True:
        print("\n==============================")
        print("       ADMIN PANEL            ")
        print("==============================")
        print("1.  Add Student (manual)")
        print("2.  Bulk Add Students (CSV)")
        print("3.  Bulk Add Marks (CSV)")
        print("4.  View All Students")
        print("5.  Search Student")
        print("6.  Update Marks")
        print("7.  Update Attendance")
        print("8.  Update Fees")
        print("9.  Delete Student")
        print("10. View Department Wise")
        print("11. View Failed Students")
        print("12. Promote Students")
        print("13. Logout")
        print("==============================")
        choice = input("Enter your choice: ")
        if choice == "1": college.add_student()
        elif choice == "2":
            f = input("CSV filename: ")
            college.bulk_add_students(f)
        elif choice == "3":
            f = input("CSV filename: ")
            college.bulk_add_marks(f)
        elif choice == "4": college.view_all_students()
        elif choice == "5": college.search_student()
        elif choice == "6": college.update_marks()
        elif choice == "7": college.update_attendance()
        elif choice == "8": college.update_fees()
        elif choice == "9": college.delete_student()
        elif choice == "10": college.view_department_wise()
        elif choice == "11": college.view_failed_students()
        elif choice == "12":
            dept = input("Department: ").upper()
            year = input("Current year: ")
            college.promote_students(dept, year)
        elif choice == "13":
            college.admin_logout()
            print("Admin logged out!")
            break
        else: print("Invalid choice!")

def main():
    college = College()
    while True:
        print("\n==============================")
        print("  STUDENT MANAGEMENT SYSTEM   ")
        print("==============================")
        print("1. Admin Login")
        print("2. Student Login")
        print("3. Exit")
        print("==============================")
        choice = input("Enter your choice: ")
        if choice == "1":
            username = input("Username: ")
            password = input("Password: ")
            if college.admin_login(username, password):
                admin_menu(college)
        elif choice == "2":
            regno    = input("Regno: ")
            password = input("Password: ")
            student  = college.find_student(regno, password)
            if student:
                print(f"Welcome {student.name}!")
                student_menu(student, college)
            else:
                print("Invalid regno or password!")
        elif choice == "3":
            college.close()
            print("Thank you!")
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()
