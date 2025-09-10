import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from datetime import datetime, date

# MySQL Connection Configuration
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",  # Replace with your MySQL password
    database="bus_reservation"
)
cursor = conn.cursor()

# Create required tables if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS buses (
    bus_id INT AUTO_INCREMENT PRIMARY KEY,
    source VARCHAR(100),
    destination VARCHAR(100),
    date DATE,
    departure_time TIME,
    total_seats INT,
    available_seats INT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    bus_id INT,
    passenger_name VARCHAR(100),
    seats_booked INT,
    status VARCHAR(20),
    booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bus_id) REFERENCES buses(bus_id)
)
""")

conn.commit()

# Insert sample bus data if table is empty
cursor.execute("SELECT COUNT(*) FROM buses")
if cursor.fetchone()[0] == 0:
    sample_buses = [
        ("Pune", "Mumbai", "2025-05-01", "09:00:00", 40, 40),
        ("Pune", "Mumbai", "2025-05-01", "14:00:00", 40, 40),
        ("Pune", "Nashik", "2025-05-01", "11:00:00", 30, 30),
        ("Mumabi", "Nagpur", "2025-05-02", "08:30:00", 50, 50),
    ]
    cursor.executemany("""
        INSERT INTO buses (source, destination, date, departure_time, total_seats, available_seats)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, sample_buses)
    conn.commit()

# GUI Setup
root = tk.Tk()
root.title("🚌 Bus Reservation System")
root.geometry("700x700")
root.configure(bg="#f0f4f7")

style = ttk.Style()
style.configure("TLabel", font=("Segoe UI", 12), background="#f0f4f7")
style.configure("TButton", font=("Segoe UI", 11), padding=6)
style.configure("TCombobox", padding=4)

main_frame = tk.Frame(root, bg="#ffffff", bd=2, relief="groove")
main_frame.pack(pady=20, padx=20, fill="both", expand=True)

# --- Title ---
tk.Label(main_frame, text="Bus Reservation Form", font=("Segoe UI", 16, "bold"), bg="#ffffff").pack(pady=10)

# --- Passenger Name ---
tk.Label(main_frame, text="Passenger Name:").pack()
name_entry = ttk.Entry(main_frame)
name_entry.pack(pady=5)

# --- Source ---
cursor.execute("SELECT DISTINCT source FROM buses")
sources = [row[0] for row in cursor.fetchall()]
source_var = tk.StringVar()
tk.Label(main_frame, text="Source:").pack()
source_menu = ttk.Combobox(main_frame, textvariable=source_var, values=sources, state="readonly")
source_menu.pack(pady=5)

# --- Destination ---
cursor.execute("SELECT DISTINCT destination FROM buses")
destinations = [row[0] for row in cursor.fetchall()]
destination_var = tk.StringVar()
tk.Label(main_frame, text="Destination:").pack()
destination_menu = ttk.Combobox(main_frame, textvariable=destination_var, values=destinations, state="readonly")
destination_menu.pack(pady=5)

# --- Date ---
tk.Label(main_frame, text="Date (YYYY-MM-DD):").pack()
date_entry = ttk.Entry(main_frame)
date_entry.insert(0, "2025-05-01")  # Pre-fill example date for testing
date_entry.pack(pady=5)

# --- Seats ---
tk.Label(main_frame, text="Number of Seats:").pack()
seats_entry = ttk.Entry(main_frame)
seats_entry.pack(pady=5)

# --- Results Frame ---
result_frame = tk.LabelFrame(main_frame, text="Available Buses", bg="#ffffff")
result_frame.pack(pady=15, padx=10, fill="both", expand=True)

# --- Show Available Buses ---
def show_buses():
    for widget in result_frame.winfo_children():
        widget.destroy()

    source = source_var.get()
    destination = destination_var.get()
    date_value = date_entry.get()

    cursor.execute("SELECT * FROM buses WHERE source=%s AND destination=%s AND date=%s",
                   (source, destination, date_value))
    buses = cursor.fetchall()
    if not buses:
        tk.Label(result_frame, text="No buses available.", bg="#ffffff").pack()
        return

    for bus in buses:
        bus_id, src, dst, dt, dep, total, avail = bus
        display = f"Bus ID: {bus_id} | Departure: {dep} | Seats Available: {avail}"
        ttk.Button(result_frame, text=display, command=lambda b=bus_id: book_ticket(b)).pack(pady=4)

# --- Book Ticket ---
def book_ticket(bus_id):
    name = name_entry.get()
    if not name or not seats_entry.get().isdigit():
        messagebox.showerror("Error", "Enter a valid name and number of seats.")
        return

    seats = int(seats_entry.get())
    cursor.execute("SELECT available_seats FROM buses WHERE bus_id=%s", (bus_id,))
    available = cursor.fetchone()[0]

    if available >= seats:
        cursor.execute("INSERT INTO bookings (bus_id, passenger_name, seats_booked, status) VALUES (%s, %s, %s, 'confirmed')",
                       (bus_id, name, seats))
        cursor.execute("UPDATE buses SET available_seats = available_seats - %s WHERE bus_id = %s", (seats, bus_id))
        conn.commit()
        messagebox.showinfo("Booking Confirmed", f"{seats} seats booked successfully.")
    else:
        cursor.execute("INSERT INTO bookings (bus_id, passenger_name, seats_booked, status) VALUES (%s, %s, %s, 'waiting')",
                       (bus_id, name, seats))
        conn.commit()
        messagebox.showinfo("Waiting List", "Not enough seats. Added to waiting list.")

# --- Cancel Ticket ---
tk.Label(main_frame, text="\nCancel Booking (Enter Booking ID):").pack()
cancel_entry = ttk.Entry(main_frame)
cancel_entry.pack(pady=5)

def cancel_ticket():
    cancel_id = cancel_entry.get()
    if not cancel_id.isdigit():
        messagebox.showerror("Error", "Enter a valid Booking ID.")
        return

    cursor.execute("SELECT status, bus_id, seats_booked FROM bookings WHERE booking_id=%s", (cancel_id,))
    result = cursor.fetchone()
    if not result:
        messagebox.showerror("Error", "Booking ID not found.")
        return

    status, bus_id, seats = result
    cursor.execute("DELETE FROM bookings WHERE booking_id=%s", (cancel_id,))
    if status == "confirmed":
        cursor.execute("UPDATE buses SET available_seats = available_seats + %s WHERE bus_id = %s", (seats, bus_id))
    conn.commit()
    messagebox.showinfo("Cancelled", "Booking cancelled successfully.")

# --- Buttons ---
tk.Button(main_frame, text="Search Buses", command=show_buses, bg="#007acc", fg="white", font=("Segoe UI", 11), padx=10, pady=5).pack(pady=10)
tk.Button(main_frame, text="Cancel Ticket", command=cancel_ticket, bg="#cc0000", fg="white", font=("Segoe UI", 11), padx=10, pady=5).pack(pady=5)

# --- Close App ---
def close():
    conn.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", close)
root.mainloop()
