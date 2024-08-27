#Hotel Booking Management System

import mysql.connector
import random #generate random values
import string
from datetime import datetime, timedelta
import hashlib #hashing passwords
import re #for regular expressions

#function for creating tables and connections
def create_database_and_tables(db_connection):
    try:
        cursor = db_connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS hotelbooking;")
        cursor.execute("USE hotelbooking;")
    except mysql.connector.Error as err:
        print(f"Database error: {err}")

    #table for customer details
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Customers (
        customer_id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(50) NOT NULL,
        phone VARCHAR(15) NOT NULL,
        email VARCHAR(50) NOT NULL,
        user_id VARCHAR(20) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL
    );
    """)
    #table for room details
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Rooms (
        room_id INT PRIMARY KEY AUTO_INCREMENT,
        room_no VARCHAR(10) NOT NULL,
        category VARCHAR(20) NOT NULL,
        rate_per_day DECIMAL(10, 2) NOT NULL,
        occupancy_status ENUM('Occupied', 'Unoccupied') DEFAULT 'Unoccupied',
        hourly_rate DECIMAL(10, 2)
    );
    """)
    #bookings details are stored in bookings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Bookings (
        booking_id VARCHAR(10) PRIMARY KEY,
        customer_id INT,
        room_id INT,
        date_of_booking DATE NOT NULL,
        date_of_occupancy DATE NOT NULL,
        no_of_days INT,
        advance_received DECIMAL(10, 2),
        tax DECIMAL(10, 2),
        housekeeping_charges DECIMAL(10, 2),
        misc_charges DECIMAL(10, 2),
        total_amount DECIMAL(10, 2),
        FOREIGN KEY (customer_id) REFERENCES Customers(customer_id),
        FOREIGN KEY (room_id) REFERENCES Rooms(room_id)
    );
    """)

    print("Database and tables created successfully.")


# Admin Module is given in a class
class Admin:
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.admin_credentials = {
            'admin': 'admin@123'  # Predefined username and password
        }

    #function for admin to login with the predefined username and password
    def admin_login(self, user_id, password):
        if user_id in self.admin_credentials and self.admin_credentials[user_id] == password:
            print("Admin login successful!")
            return True
        else:
            print("Invalid user_id or password.")
            return False

    #function for adding rooms by admin
    def add_room(self, room_no, category_index, rate_per_day, hourly_rate=None):
        # Define the categories
        categories = ['Single', 'Double', 'Suite', 'Convention Halls', 'Ballrooms']
        # Validate the category index
        if category_index < 1 or category_index > len(categories):
            print("Invalid category index.")
            return
        # Get the selected category
        category = categories[category_index - 1]

        cursor = self.db_connection.cursor()
        query = "INSERT INTO Rooms (room_no, category, rate_per_day, hourly_rate) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (room_no, category, rate_per_day, hourly_rate))
        self.db_connection.commit()
        print("Room created successfully.")

    #display_rooms() displays all the details of rooms
    def display_rooms(self):
        cursor = self.db_connection.cursor()
        query = "SELECT * FROM Rooms ORDER BY category, rate_per_day"
        cursor.execute(query)
        rooms = cursor.fetchall()
        print("Category-wise List of Rooms and Their Rates:")
        print(f"{'room_id':<10} {'room_no':<10} {'category':<20} {'rate_per_day':<15} {'occupancy_status':<20} {'hourly_rate':<10}")
        for room in rooms:
            print(room)


    #function to store details of occupied rooms
    def occupied_rooms(self):
        cursor = self.db_connection.cursor()
        future_date = datetime.now() + timedelta(days=2)
        query = "SELECT room_no FROM Rooms INNER JOIN Bookings ON Rooms.room_id = Bookings.room_id WHERE date_of_occupancy <= %s"
        cursor.execute(query, (future_date,))
        rooms = cursor.fetchall()
        print("Rooms Occupied for the Next Two Days:")
        for room in rooms:
            print(room)

    #function to search rooms
    def search_room(self, booking_id):
        cursor = self.db_connection.cursor()
        query = """SELECT Customers.name, Customers.phone, Customers.email, Rooms.room_no, Bookings.date_of_booking,
                   Bookings.date_of_occupancy, Bookings.no_of_days, Bookings.total_amount
                   FROM Bookings
                   INNER JOIN Customers ON Bookings.customer_id = Customers.customer_id
                   INNER JOIN Rooms ON Bookings.room_id = Rooms.room_id
                   WHERE Bookings.booking_id = %s"""
        cursor.execute(query, (booking_id,))
        result = cursor.fetchone()
        print("Customer Details Based on Booking ID:")
        print(result)

    #function to update the status of room as unoccupied
    def update_to_unoccupied(self, room_no):
        cursor = self.db_connection.cursor()
        query = "UPDATE Rooms SET occupancy_status = 'Unoccupied' WHERE room_no = %s"
        cursor.execute(query, (room_no,))
        self.db_connection.commit()
        print(f"Room {room_no} status updated to Unoccupied.")

#function to display unoccupied rooms
    def unoccupied_rooms(self):
        cursor = self.db_connection.cursor()
        query = "SELECT room_no FROM Rooms WHERE occupancy_status = 'Unoccupied'"
        cursor.execute(query)
        rooms = cursor.fetchall()
        print("Unoccupied Rooms:")
        for room in rooms:
            print(room)

#store_to_file function stores the booking detais to a file "booking_records.txt"
    def store_to_file(self, filename="booking_records.txt"):
        cursor = self.db_connection.cursor()
        query = "SELECT * FROM Bookings"
        cursor.execute(query)
        bookings = cursor.fetchall()
        with open(filename, 'w') as file:
            for booking in bookings:
                file.write(str(booking) + "\n")
        print(f"All booking records stored in {filename}.")


#Customer Module
class Customer:
    def __init__(self, db_connection):
        self.db_connection = db_connection
    #function for validating name with only letters
    def validate_name(self, name):
        return bool(re.match(r'^[A-Za-z\s]+$', name))
    #phone number validation
    def validate_phone(self, phone):
        # Check if the phone number is exactly 10 digits and starts with 6, 7, 8, or 9
        return phone.isdigit() and len(phone) == 10 and phone[0] in '6789'
    #email validation
    def validate_email(self, email):
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))
    #userid validation(eg:abc123)
    def validate_user_id(self, user_id):
        return bool(re.match(r'^[A-Za-z0-9_]+$', user_id))
    #password validation(eg:Abcd@1234)
    def validate_password(self, password):
        return len(password) >= 8 and any(char.isdigit() for char in password) and any(
            char.isalpha() for char in password)

#function for registration of customer
    def register_customer(self, name, phone, email, user_id, password):
        if not self.validate_name(name):
            print("Invalid name. Only alphabetic characters and spaces are allowed.")
            return
        if not self.validate_phone(phone):
            print("Invalid phone number. It should be numeric and have 10 or 15 digits.")
            return
        if not self.validate_email(email):
            print("Invalid email format.")
            return
        if not self.validate_user_id(user_id):
            print("Invalid user ID. It should contain only alphanumeric characters and underscores.")
            return
        if not self.validate_password(password):
            print("Password must be at least 8 characters long and contain both letters and numbers.")
            return

        cursor = self.db_connection.cursor()
        # Directly store the password without hashing
        query = "INSERT INTO Customers (name, phone, email, user_id, password) VALUES (%s, %s, %s, %s, %s)"
        try:
            cursor.execute(query, (name, phone, email, user_id, password))
            self.db_connection.commit()
            print("Customer registered successfully.")
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    #customer login function
    def logincus(self, user_id, password):
        try:
            cursor = self.db_connection.cursor()
            query = "SELECT customer_id FROM Customers WHERE user_id = %s AND password = %s"
            cursor.execute(query, (user_id, password))
            result = cursor.fetchone()
            if result:
                print("Login successful!")
                return result[0]
            else:
                print("Invalid user_id or password.")
                return None
        except mysql.connector.Error as err:
            print(f"Error while logging in: {err}")

    #function for customers to view unoccupied rooms
    def view_unoccupied_rooms(self):
        cursor = self.db_connection.cursor()
        query = "SELECT room_no, category, rate_per_day FROM Rooms WHERE occupancy_status = 'Unoccupied'"
        cursor.execute(query)
        rooms = cursor.fetchall()
        print("Unoccupied Rooms:")
        print(f"{'room_no':<10} {'category':<20} {'rate_per_day':<15}")
        print("------------------------------------------------------")
        for room in rooms:
            room_no, category, rate_per_day = room
            print(
                f"{room_no:<10} {category:<20} {rate_per_day:<15.2f}")

    #function for customer to choose the room
    def choose_room(self, category):
        cursor = self.db_connection.cursor()
        query = "SELECT room_no, rate_per_day, hourly_rate FROM Rooms WHERE category = %s AND occupancy_status = 'Unoccupied'"
        cursor.execute(query, (category,))
        rooms = cursor.fetchall()

        if not rooms:
            print(f"No rooms available in the category '{category}' at the moment. Please check other categories.")
            return None  # Return None to indicate no rooms are available

        print(f"Available {category} Rooms:")
        print(f"{'room_no':<10} {'rate_per_day':<15} {'hourly_rate':<10}")
        print("---------------------------------------------------------------")
        for room in rooms:
            room_no,rate_per_day,hourly_rate = room
            print(f"{room_no:<10}{rate_per_day:<15.2f} {hourly_rate if hourly_rate is not None else 'N/A':<10}")

        room_no = input("Enter the room number you want to book: ")
        return room_no

    #payment function for customer
    def payment_method(self, room_no, customer_id, no_of_days, advance):
        cursor = self.db_connection.cursor()
        query = "SELECT room_id, rate_per_day, hourly_rate FROM Rooms WHERE room_no = %s"
        cursor.execute(query, (room_no,))
        room = cursor.fetchone()

        room_id = room[0]
        rate_per_day = float(room[1])  # Convert to float
        hourly_rate = float(room[2]) if room[2] else 0  # Convert to float if not None

        tax = rate_per_day * no_of_days * 0.18
        housekeeping_charges = 200.00
        misc_charges = 150.00
        total_amount = rate_per_day * no_of_days + tax + housekeeping_charges + misc_charges - advance

        booking_id = ''.join(random.choices(string.ascii_uppercase, k=2)) + ''.join(random.choices(string.digits, k=5))

        query = """INSERT INTO Bookings (booking_id, customer_id, room_id, date_of_booking, date_of_occupancy,
                    no_of_days, advance_received, tax, housekeeping_charges, misc_charges, total_amount)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query, (booking_id, customer_id, room_id, datetime.now(), datetime.now(), no_of_days,
                               advance, tax, housekeeping_charges, misc_charges, total_amount))
        self.db_connection.commit()

        query = "UPDATE Rooms SET occupancy_status = 'Occupied' WHERE room_no = %s"
        cursor.execute(query, (room_no,))
        self.db_connection.commit()

        print(f"Booking successful! Your Booking ID is {booking_id}. Total amount due: {total_amount}")

# Main Function
def main():
    db_connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='faith',
        database='hotelbooking'
    )

    create_database_and_tables(db_connection)
    #admin page
    while True:
        print("---------------------------------Welcome User---------------------------:)")
        print("*-------------------------Hotel Management System------------------------*")
        print("1. Admin Login")
        print("2. Customer Menu")
        print("3. Exit")
        user_type = int(input("Enter your choice: "))
        if user_type == 1:
            admin = Admin(db_connection)
            # Admin login
            user_id = input("Enter admin user ID: ")
            password = input("Enter admin password: ")
            if admin.admin_login(user_id, password):
                while True:
                    print("\nAdmin Menu")
                    print("1. Create Room")
                    print("2. Display Rooms")
                    print("3. List Occupied Rooms")
                    print("4. Search Room by Booking ID")
                    print("5. Display Unoccupied Rooms")
                    print("6. Update Room to Unoccupied")
                    print("7. Store Records to File")
                    print("8. Exit")
                    choice = int(input("Enter your choice: "))

                    if choice == 1:
                        room_no = input("Enter room number: ")

                        # Display category options
                        print("Select room category:")
                        print("1. Single Room")
                        print("2. Double Room")
                        print("3. Suite")
                        print("4. Convention Halls")
                        print("5. Ballrooms")
                        category_index = int(input("Enter the room category number from above options: "))

                        rate_per_day = float(input("Enter rate per day: "))
                        hourly_rate = input("Enter hourly rate (optional): ")
                        hourly_rate = float(hourly_rate) if hourly_rate else None

                        admin.add_room(room_no, category_index, rate_per_day, hourly_rate)
                    elif choice == 2:
                        admin.display_rooms()
                    elif choice == 3:
                        admin.occupied_rooms()
                    elif choice == 4:
                        booking_id = input("Enter booking ID: ") #autogenerated bookingid
                        admin.search_room(booking_id)
                    elif choice == 5:
                        admin.unoccupied_rooms()
                    elif choice == 6:
                        room_no = input("Enter room number to update to unoccupied: ")
                        admin.update_to_unoccupied(room_no)
                    elif choice == 7:
                        admin.store_to_file()
                    elif choice == 8:
                        break
                    else:
                        print("Invalid choice, please try again.")
        #customer page
        elif user_type == 2:
            customer = Customer(db_connection)
            while True:
                print("\n........Hey Customer....!")
                print("1. Register")
                print("2. Login")
                print("3. Exit")
                choice = int(input("Enter your choice: "))

                if choice == 1:
                    name = input("Enter your name: ")
                    phone = input("Enter your phone number(starts with 6,7,8,9 and should have 10 digits: ")
                    email = input("Enter your email(example@gmail.com): ")
                    user_id = input("Enter a user ID(both alphanumeric characters): ")
                    password = input("Enter a password(both alphanumeric with atleast one uppercase and one special character): ")
                    customer.register_customer(name, phone, email, user_id, password)
                elif choice == 2:
                    user_id = input("Enter your user ID: ")
                    password = input("Enter your password: ")
                    customer_id = customer.logincus(user_id, password)
                    if customer_id:
                        while True:
                            print("\nCustomer Menu:")
                            print("1. View Available Rooms")
                            print("2. Book a Room")
                            print("3. Exit")
                            choice = int(input("Enter your choice: "))

                            if choice == 1:
                                customer.view_unoccupied_rooms()
                            elif choice == 2:
                                category = input("Enter the room category you want to book(single,double,suite,convention halls,ballrooms): ")
                                room_no = customer.choose_room(category)
                                if room_no:
                                    no_of_days = int(input("Enter number of days to book: "))
                                    advance = float(input("Enter advance amount  you wish to pay: "))
                                    customer.payment_method(room_no, customer_id, no_of_days, advance)
                                else:
                                    print("Booking could not be completed. Please try again with a different category.")
                            elif choice == 3:
                                break
                            else:
                                print("Invalid choice, please try again.")
                elif choice == 3:
                    break
                else:
                    print("Invalid choice, please try again.")
        elif user_type == 3:
            print("System exiting...!")
            break
        else:
            print("Invalid choice, please try again.")

    db_connection.close()

#ensures that the main function is implemented first
if __name__ == "__main__":
    main()
