"""
Irrigation Payroll Tracker - GUI Version
Tracks employee pay, invoices, and commissions.
Author: Emmanuel Diaz
GUI Version
"""

import os
import csv
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import List, Optional
from datetime import datetime


class Invoice:
    """Represents an invoice with commission calculation"""

    def __init__(self, number: str, customer: str, date: str, employee_name: str,
                 status: str, credit_card_used: bool, total: float, tip: float,
                 materials: float, fees: float):
        self.number = number
        self.customer = customer
        self.date = date
        self.employee_name = employee_name
        self.status = status
        self.credit_card_used = credit_card_used
        self.total = total
        self.tip = tip
        self.materials = materials
        self.fees = fees
        self.commission = self.calculate_commission()

    def calculate_commission(self) -> float:
        """Calculate commission based on invoice details"""
        return self.calculate_commission_static(
            self.credit_card_used, self.total, self.tip, self.materials, self.fees
        )

    @staticmethod
    def calculate_commission_static(credit_card_used: bool, total: float,
                                    tip: float, materials: float, fees: float) -> float:
        """Static method to calculate commission"""
        if credit_card_used:
            # Credit card used formula
            commission = ((total - materials - fees) / 2) + tip
        else:
            # Credit card NOT used
            if materials < 35:
                # Low materials case: don't subtract materials from commission base
                commission = ((total - fees) / 2) + tip
            else:
                # High materials case (>=35): subtract materials but add them back
                commission = ((total - materials - fees) / 2) + tip + materials

        return commission


class Employee:
    """Represents an employee with pay tracking"""

    def __init__(self, emp_id: int, name: str, weekly_pay: float = 0.0,
                 year_to_date_pay: float = 0.0):
        self.id = emp_id
        self.name = name
        self.weekly_pay = max(0, weekly_pay)
        self.year_to_date_pay = max(0, year_to_date_pay)

    def get_invoice_filename(self) -> str:
        """Generate invoice filename for this employee"""
        safe_name = self.name.strip().lower().replace(' ', '_')
        return f"invoices/{safe_name}_{self.id}.csv"

    def get_archived_invoice_filename(self, date_str: str) -> str:
        """Generate archived invoice filename for this employee with date"""
        safe_name = self.name.strip().lower().replace(' ', '_')
        # Replace slashes with dashes for filename safety
        safe_date = date_str.replace('/', '-')
        return f"archived_invoices/{safe_name}_{self.id}_week_{safe_date}.csv"

    def get_payment_history_filename(self) -> str:
        """Generate payment history filename for this employee"""
        safe_name = self.name.strip().lower().replace(' ', '_')
        return f"payment_history/{safe_name}_{self.id}_payments.csv"

    def add_weekly_pay(self, amount: float):
        """Add amount to year-to-date pay"""
        self.year_to_date_pay += amount

    def close_out_week(self):
        """Add weekly pay to year-to-date, then reset weekly pay"""
        self.year_to_date_pay += self.weekly_pay
        self.weekly_pay = 0

    def edit_pay(self, new_weekly_pay: float):
        """Set weekly pay to a new value"""
        self.weekly_pay = max(0, new_weekly_pay)

    def __str__(self) -> str:
        """CSV format representation"""
        return f"{self.id},{self.name},{self.weekly_pay:.2f},{self.year_to_date_pay:.2f}"


class PayrollTrackerGUI:
    """Main GUI Application"""

    def __init__(self, root):
        self.root = root
        self.root.title("Employee Payroll Tracker - THRIVE Outdoor Solutions")
        self.root.geometry("900x700")  # Increased height from 600 to 700

        # Set theme colors (green to match THRIVE branding)
        self.bg_color = "#f0f0f0"
        self.accent_color = "#8BC34A"  # Green color matching logo
        self.dark_accent = "#689F38"

        self.employees: List[Employee] = []
        self.logo_image = None
        self.load_employees()
        self.load_logo()

        # Create main container
        self.create_widgets()

    def load_logo(self):
        """Try to load logo image if available"""
        try:
            from PIL import Image, ImageTk
            if os.path.exists("logo.png"):
                img = Image.open("logo.png")
                # Resize to fit in header (max height 50px)
                img.thumbnail((200, 50), Image.Resampling.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(img)
        except ImportError:
            # PIL not available, will use text only
            self.logo_image = None
        except Exception:
            self.logo_image = None

    def create_widgets(self):
        """Create all GUI widgets"""
        # Title
        title_frame = tk.Frame(self.root, bg=self.accent_color, height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        # Add logo if available, otherwise text only
        if self.logo_image:
            logo_label = tk.Label(
                title_frame,
                image=self.logo_image,
                bg=self.accent_color
            )
            logo_label.pack(side=tk.LEFT, padx=20, pady=5)

        title_label = tk.Label(
            title_frame,
            text="THRIVE Employee Payroll Tracker" if not self.logo_image else "Employee Payroll Tracker",
            font=("Arial", 20, "bold"),
            bg=self.accent_color,
            fg="white"
        )
        if self.logo_image:
            title_label.pack(side=tk.LEFT, pady=15, padx=10)
        else:
            title_label.pack(pady=15, expand=True)

        # Main content area
        content_frame = tk.Frame(self.root, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Left panel - Menu buttons
        left_panel = tk.Frame(content_frame, bg=self.bg_color, width=250)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        left_panel.pack_propagate(False)

        menu_label = tk.Label(
            left_panel,
            text="Menu",
            font=("Arial", 16, "bold"),
            bg=self.bg_color
        )
        menu_label.pack(pady=(0, 10))

        # Menu buttons
        buttons = [
            ("👥 View Weekly Pay", self.view_weekly_pay),
            ("📊 View YTD Pay", self.view_ytd),
            ("✏️ Edit Employee", self.edit_employee_info),
            ("📄 Manage Invoices", self.manage_invoices),
            ("📁 View Archived Invoices", self.view_archived_invoices),
            ("💰 Close Out Week", self.close_out_week),
            ("➕ Add Employee", self.add_employee),
            ("❓ Help", self.show_help),
            ("ℹ️ About", self.show_about),
        ]

        for text, command in buttons:
            btn = tk.Button(
                left_panel,
                text=text,
                command=command,
                font=("Arial", 11),
                bg="white",
                fg="black",
                relief=tk.RAISED,
                bd=2,
                cursor="hand2",
                width=20,
                height=2
            )
            btn.pack(pady=3, fill=tk.X)  # Reduced from pady=5 to pady=3

        # Right panel - Display area
        self.right_panel = tk.Frame(content_frame, bg="white", relief=tk.SUNKEN, bd=2)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Welcome message
        self.show_welcome()

    def show_welcome(self):
        """Display welcome screen"""
        self.clear_right_panel()

        welcome_frame = tk.Frame(self.right_panel, bg="white")
        welcome_frame.pack(expand=True)

        welcome_text = tk.Label(
            welcome_frame,
            text="Welcome to THRIVE Payroll Tracker\n\n" +
                 f"Employees Loaded: {len(self.employees)}\n\n" +
                 "Select an option from the menu to get started.",
            font=("Arial", 14),
            bg="white",
            justify=tk.CENTER
        )
        welcome_text.pack(pady=50)

    def center_window(self, window):
        """Center a window on the screen"""
        window.update_idletasks()

        # Get window dimensions
        window_width = window.winfo_width()
        window_height = window.winfo_height()

        # Get screen dimensions
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        # Calculate position
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        # Set position
        window.geometry(f'+{x}+{y}')

    def clear_right_panel(self):
        """Clear the right display panel"""
        for widget in self.right_panel.winfo_children():
            widget.destroy()

    def view_weekly_pay(self):
        """View weekly pay for all employees"""
        self.clear_right_panel()

        if not self.employees:
            self.show_message("No employees found.")
            return

        # Title
        title = tk.Label(
            self.right_panel,
            text="Weekly Pay Report",
            font=("Arial", 16, "bold"),
            bg="white"
        )
        title.pack(pady=10)

        # Treeview
        columns = ("ID", "Name", "Weekly Pay")
        tree = ttk.Treeview(self.right_panel, columns=columns, show="headings", height=15)

        tree.heading("ID", text="ID")
        tree.heading("Name", text="Name")
        tree.heading("Weekly Pay", text="Weekly Pay")

        tree.column("ID", width=80)
        tree.column("Name", width=200)
        tree.column("Weekly Pay", width=120, anchor=tk.E)

        total_weekly = 0
        for emp in self.employees:
            tree.insert("", tk.END, values=(emp.id, emp.name, f"${emp.weekly_pay:.2f}"))
            total_weekly += emp.weekly_pay

        tree.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Total
        total_label = tk.Label(
            self.right_panel,
            text=f"Total Weekly Pay: ${total_weekly:.2f}",
            font=("Arial", 12, "bold"),
            bg="white"
        )
        total_label.pack(pady=10)

    def view_ytd(self):
        """View year-to-date pay for all employees"""
        self.clear_right_panel()

        if not self.employees:
            self.show_message("No employees found.")
            return

        # Title
        title = tk.Label(
            self.right_panel,
            text="Year-To-Date (YTD) Pay Report",
            font=("Arial", 16, "bold"),
            bg="white"
        )
        title.pack(pady=10)

        # Treeview
        columns = ("ID", "Name", "YTD Pay", "Paid On")
        tree = ttk.Treeview(self.right_panel, columns=columns, show="headings", height=15)

        tree.heading("ID", text="ID")
        tree.heading("Name", text="Name")
        tree.heading("YTD Pay", text="YTD Pay")
        tree.heading("Paid On", text="Paid On")

        tree.column("ID", width=80)
        tree.column("Name", width=180)
        tree.column("YTD Pay", width=120, anchor=tk.E)
        tree.column("Paid On", width=150, anchor=tk.CENTER)

        total_ytd = 0
        for emp in self.employees:
            last_paid_date = self.get_last_payment_date(emp)
            tree.insert("", tk.END, values=(emp.id, emp.name, f"${emp.year_to_date_pay:.2f}", last_paid_date))
            total_ytd += emp.year_to_date_pay

        tree.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Total
        total_label = tk.Label(
            self.right_panel,
            text=f"Total YTD Pay: ${total_ytd:.2f}",
            font=("Arial", 12, "bold"),
            bg="white"
        )
        total_label.pack(pady=10)

    def manage_invoices(self):
        """Manage invoices for employees"""
        self.clear_right_panel()

        if not self.employees:
            self.show_message("No employees found.")
            return

        frame = tk.Frame(self.right_panel, bg="white")
        frame.pack(expand=True)

        tk.Label(
            frame,
            text="Manage Invoices",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=10)

        tk.Label(frame, text="Select Employee:", bg="white", font=("Arial", 11)).pack(pady=5)

        emp_var = tk.StringVar()
        emp_combo = ttk.Combobox(
            frame,
            textvariable=emp_var,
            values=[f"{emp.id} - {emp.name}" for emp in self.employees],
            state="readonly",
            width=30
        )
        emp_combo.pack(pady=5)

        def view_invoices():
            if not emp_var.get():
                messagebox.showwarning("Warning", "Please select an employee first.")
                return

            emp_id = int(emp_var.get().split(" - ")[0])
            emp = self.find_employee(emp_id)
            self.view_employee_invoices(emp)

        def add_invoice():
            if not emp_var.get():
                messagebox.showwarning("Warning", "Please select an employee first.")
                return

            emp_id = int(emp_var.get().split(" - ")[0])
            emp = self.find_employee(emp_id)
            self.add_invoice_dialog(emp)

        tk.Button(
            frame,
            text="View Invoices",
            command=view_invoices,
            bg=self.accent_color,
            fg="white",
            width=20,
            height=2
        ).pack(pady=10)

        tk.Button(
            frame,
            text="Add New Invoice",
            command=add_invoice,
            bg=self.dark_accent,
            fg="white",
            width=20,
            height=2
        ).pack(pady=5)

    def view_archived_invoices(self):
        """View archived invoices for employees"""
        self.clear_right_panel()

        if not self.employees:
            self.show_message("No employees found.")
            return

        frame = tk.Frame(self.right_panel, bg="white")
        frame.pack(expand=True)

        tk.Label(
            frame,
            text="View Archived Invoices",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=10)

        tk.Label(frame, text="Select Employee:", bg="white", font=("Arial", 11)).pack(pady=5)

        emp_var = tk.StringVar()
        emp_combo = ttk.Combobox(
            frame,
            textvariable=emp_var,
            values=[f"{emp.id} - {emp.name}" for emp in self.employees],
            state="readonly",
            width=30
        )
        emp_combo.pack(pady=5)

        def show_archives():
            if not emp_var.get():
                messagebox.showwarning("Warning", "Please select an employee first.")
                return

            emp_id = int(emp_var.get().split(" - ")[0])
            emp = self.find_employee(emp_id)
            self.show_employee_archives(emp)

        tk.Button(
            frame,
            text="View Archives",
            command=show_archives,
            bg=self.accent_color,
            fg="white",
            width=20,
            height=2
        ).pack(pady=20)

    def show_employee_archives(self, emp: Employee):
        """Show list of archived invoice files for an employee"""
        self.clear_right_panel()

        tk.Label(
            self.right_panel,
            text=f"Archived Invoices for {emp.name}",
            font=("Arial", 14, "bold"),
            bg="white"
        ).pack(pady=10)

        # Get all archived files for this employee
        safe_name = emp.name.strip().lower().replace(' ', '_')
        archive_pattern = f"{safe_name}_{emp.id}_week_"

        archived_files = []
        if os.path.exists("archived_invoices"):
            for filename in os.listdir("archived_invoices"):
                if filename.startswith(archive_pattern) and filename.endswith(".csv"):
                    # Extract date from filename
                    date_part = filename.replace(archive_pattern, "").replace(".csv", "")
                    archived_files.append((date_part, f"archived_invoices/{filename}"))

        if not archived_files:
            tk.Label(
                self.right_panel,
                text="No archived invoices found.",
                font=("Arial", 11),
                bg="white"
            ).pack(pady=20)
            tk.Button(
                self.right_panel,
                text="Back",
                command=self.view_archived_invoices,
                width=10
            ).pack(pady=10)
            return

        # Sort by date (most recent first)
        archived_files.sort(reverse=True)

        # Create listbox with scrollbar
        list_frame = tk.Frame(self.right_panel, bg="white")
        list_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(
            list_frame,
            font=("Arial", 11),
            yscrollcommand=scrollbar.set,
            height=15
        )

        for date_str, filepath in archived_files:
            display_date = date_str.replace('-', '/')
            listbox.insert(tk.END, f"Week ending: {display_date}")

        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        def view_selected_archive():
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                date_str, filepath = archived_files[index]
                self.view_archived_invoice_details(emp, filepath, date_str)

        tk.Button(
            self.right_panel,
            text="View Selected Archive",
            command=view_selected_archive,
            bg=self.accent_color,
            fg="white",
            width=20,
            height=2
        ).pack(pady=10)

        tk.Button(
            self.right_panel,
            text="Back",
            command=self.view_archived_invoices,
            width=10
        ).pack(pady=5)

    def view_archived_invoice_details(self, emp: Employee, filepath: str, date_str: str):
        """View details of a specific archived invoice file"""
        self.clear_right_panel()

        display_date = date_str.replace('-', '/')
        tk.Label(
            self.right_panel,
            text=f"Archived Invoices - {emp.name}",
            font=("Arial", 14, "bold"),
            bg="white"
        ).pack(pady=5)

        tk.Label(
            self.right_panel,
            text=f"Week ending: {display_date}",
            font=("Arial", 11, "italic"),
            bg="white",
            fg="gray"
        ).pack()

        # Treeview
        columns = ("Invoice", "Customer", "Date", "Status", "Total", "Commission")
        tree = ttk.Treeview(self.right_panel, columns=columns, show="headings", height=15)

        tree.heading("Invoice", text="Invoice#")
        tree.heading("Customer", text="Customer")
        tree.heading("Date", text="Date")
        tree.heading("Status", text="Status")
        tree.heading("Total", text="Total")
        tree.heading("Commission", text="Commission")

        tree.column("Invoice", width=80)
        tree.column("Customer", width=120)
        tree.column("Date", width=90)
        tree.column("Status", width=80)
        tree.column("Total", width=80, anchor=tk.E)
        tree.column("Commission", width=90, anchor=tk.E)

        totals = {'sales': 0, 'commission': 0, 'count': 0}

        try:
            with open(filepath, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header

                for row in reader:
                    if len(row) >= 9:
                        tree.insert("", tk.END, values=(
                            row[0], row[1], row[2], row[3],
                            f"${float(row[4]):.2f}",
                            f"${float(row[8]):.2f}"
                        ))
                        totals['sales'] += float(row[4])
                        totals['commission'] += float(row[8])
                        totals['count'] += 1
        except Exception as e:
            messagebox.showerror("Error", f"Error reading archived invoices: {e}")
            return

        tree.pack(fill=tk.BOTH, expand=True, pady=10)

        # Summary
        summary_frame = tk.Frame(self.right_panel, bg="white")
        summary_frame.pack(pady=10)

        summary_text = f"Total Invoices: {totals['count']}  |  " + \
                       f"Total Sales: ${totals['sales']:,.2f}  |  " + \
                       f"Total Commission: ${totals['commission']:,.2f}"

        tk.Label(
            summary_frame,
            text=summary_text,
            font=("Arial", 10, "bold"),
            bg="white"
        ).pack()

        tk.Button(
            self.right_panel,
            text="Back to Archives",
            command=lambda: self.show_employee_archives(emp),
            width=15
        ).pack(pady=5)

    def view_employee_invoices(self, emp: Employee):
        """View all invoices for a specific employee"""
        self.clear_right_panel()

        tk.Label(
            self.right_panel,
            text=f"Invoices for {emp.name}",
            font=("Arial", 14, "bold"),
            bg="white"
        ).pack(pady=10)

        tk.Label(
            self.right_panel,
            text="Double-click an invoice to edit it | Press 'P' for Paid | Press 'U' for Unpaid",
            font=("Arial", 9, "italic"),
            bg="white",
            fg="gray"
        ).pack()

        filename = emp.get_invoice_filename()

        if not os.path.exists(filename):
            self.show_message(f"No invoices found for {emp.name}")
            tk.Button(
                self.right_panel,
                text="Back",
                command=self.manage_invoices,
                width=10
            ).pack(pady=10)
            return

        # Treeview
        columns = ("Invoice", "Customer", "Date", "Status", "Total", "Commission")
        tree = ttk.Treeview(self.right_panel, columns=columns, show="headings", height=15)

        tree.heading("Invoice", text="Invoice#")
        tree.heading("Customer", text="Customer")
        tree.heading("Date", text="Date")
        tree.heading("Status", text="Status")
        tree.heading("Total", text="Total")
        tree.heading("Commission", text="Commission")

        tree.column("Invoice", width=80)
        tree.column("Customer", width=120)
        tree.column("Date", width=90)
        tree.column("Status", width=80)
        tree.column("Total", width=80, anchor=tk.E)
        tree.column("Commission", width=90, anchor=tk.E)

        totals = {'sales': 0, 'commission': 0, 'count': 0}
        invoice_data = []

        try:
            with open(filename, 'r') as f:
                reader = csv.reader(f)
                next(reader)

                for row in reader:
                    if len(row) >= 9:
                        tree.insert("", tk.END, values=(
                            row[0], row[1], row[2], row[3],
                            f"${float(row[4]):.2f}",
                            f"${float(row[8]):.2f}"
                        ))
                        invoice_data.append(row)
                        totals['sales'] += float(row[4])
                        totals['commission'] += float(row[8])
                        totals['count'] += 1
        except Exception as e:
            messagebox.showerror("Error", f"Error reading invoices: {e}")
            return

        tree.pack(fill=tk.BOTH, expand=True)

        # FIXED: Bind double-click event with proper string conversion
        def on_double_click(event):
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                # Convert the invoice number from the tree to string for comparison
                invoice_number = str(item['values'][0])
                for inv_row in invoice_data:
                    # Ensure both sides are strings for comparison
                    if str(inv_row[0]) == invoice_number:
                        self.edit_invoice_dialog(emp, inv_row)
                        break

        tree.bind("<Double-Button-1>", on_double_click)

        # Bind keyboard shortcuts
        def on_key_press(event):
            selection = tree.selection()
            if not selection:
                return

            item = tree.item(selection[0])
            # Convert to string for comparison
            invoice_number = str(item['values'][0])

            for inv_row in invoice_data:
                if str(inv_row[0]) == invoice_number:
                    if event.char.lower() == 'p':
                        self.toggle_invoice_status(emp, inv_row, "Paid")
                    elif event.char.lower() == 'u':
                        self.toggle_invoice_status(emp, inv_row, "Unpaid")
                    break

        tree.bind("<Key>", on_key_press)
        tree.focus_set()

        # Summary
        summary_frame = tk.Frame(self.right_panel, bg="white")
        summary_frame.pack(pady=10)

        summary_text = f"Total Invoices: {totals['count']}  |  " + \
                       f"Total Sales: ${totals['sales']:,.2f}  |  " + \
                       f"Total Commission: ${totals['commission']:,.2f}"

        tk.Label(
            summary_frame,
            text=summary_text,
            font=("Arial", 10, "bold"),
            bg="white"
        ).pack()

        tk.Button(
            self.right_panel,
            text="Back",
            command=self.manage_invoices,
            width=10
        ).pack(pady=5)

    def toggle_invoice_status(self, emp: Employee, invoice_row: list, new_status: str):
        """Toggle invoice status between Paid and Unpaid"""
        filename = emp.get_invoice_filename()
        invoice_number = invoice_row[0]
        old_status = invoice_row[3]

        if old_status == new_status:
            messagebox.showinfo("Info", f"Invoice is already marked as {new_status}.")
            return

        # Read all invoices
        invoices = []
        try:
            with open(filename, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)
                for row in reader:
                    if row[0] == invoice_number:
                        row[3] = new_status
                    invoices.append(row)
        except Exception as e:
            messagebox.showerror("Error", f"Error reading invoices: {e}")
            return

        # Write back all invoices
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(invoices)

            messagebox.showinfo("Success", f"Invoice #{invoice_number} status changed to {new_status}.")
            self.view_employee_invoices(emp)

        except Exception as e:
            messagebox.showerror("Error", f"Error updating invoice: {e}")

    def add_invoice_dialog(self, emp: Employee):
        """Dialog to add a new invoice"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Add Invoice - {emp.name}")
        dialog.geometry("450x800")  # Increased height for new field
        self.center_window(dialog)  # Center the dialog

        fields = {}

        tk.Label(dialog, text=f"New Invoice for {emp.name}", font=("Arial", 14, "bold")).pack(pady=10)

        # Invoice Number
        tk.Label(dialog, text="Invoice Number:", font=("Arial", 10, "bold")).pack(pady=(10, 2))
        fields['number'] = tk.Entry(dialog, width=30)
        fields['number'].pack(pady=2)

        # Customer
        tk.Label(dialog, text="Customer:", font=("Arial", 10, "bold")).pack(pady=(5, 2))
        fields['customer'] = tk.Entry(dialog, width=30)
        fields['customer'].pack(pady=2)

        # Date
        tk.Label(dialog, text="Date (MM/DD/YYYY):", font=("Arial", 10, "bold")).pack(pady=(5, 2))
        fields['date'] = tk.Entry(dialog, width=30)
        fields['date'].insert(0, datetime.now().strftime("%m/%d/%Y"))
        fields['date'].pack(pady=2)

        # Status
        tk.Label(dialog, text="Status:", font=("Arial", 10, "bold")).pack(pady=(5, 2))
        fields['status'] = ttk.Combobox(dialog, values=["Paid", "Unpaid"], state="readonly", width=28)
        fields['status'].set("Paid")
        fields['status'].pack(pady=2)

        # Manual Commission Override Checkbox
        fields['manual_override'] = tk.BooleanVar(value=False)
        manual_check = tk.Checkbutton(
            dialog,
            text="✓ Manual Commission Override",
            variable=fields['manual_override'],
            font=("Arial", 10, "bold"),
            fg=self.dark_accent
        )
        manual_check.pack(pady=10)

        # Separator
        ttk.Separator(dialog, orient='horizontal').pack(fill='x', padx=20, pady=5)

        # Credit Card
        fields['cc'] = tk.BooleanVar(value=False)
        fields['cc_check'] = tk.Checkbutton(dialog, text="Credit Card Used", variable=fields['cc'])
        fields['cc_check'].pack(pady=5)

        # Helper function to clear placeholder on focus
        def on_entry_click(event, entry):
            """Clear the entry field when clicked if it contains default value"""
            if entry.get() in ["0.00", "0"]:
                entry.delete(0, tk.END)
                entry.config(fg='black')

        def on_focus_out(event, entry):
            """Restore default value if field is empty"""
            if entry.get() == "":
                entry.insert(0, "0.00")
                entry.config(fg='grey')

        # Total
        fields['total_label'] = tk.Label(dialog, text="Total Sale:", font=("Arial", 10, "bold"))
        fields['total_label'].pack(pady=(5, 2))
        fields['total'] = tk.Entry(dialog, width=30, fg='grey')
        fields['total'].insert(0, "0.00")
        fields['total'].bind('<FocusIn>', lambda e: on_entry_click(e, fields['total']))
        fields['total'].bind('<FocusOut>', lambda e: on_focus_out(e, fields['total']))
        fields['total'].pack(pady=2)

        # Tip
        fields['tip_label'] = tk.Label(dialog, text="Tip:", font=("Arial", 10, "bold"))
        fields['tip_label'].pack(pady=(5, 2))
        fields['tip'] = tk.Entry(dialog, width=30, fg='grey')
        fields['tip'].insert(0, "0.00")
        fields['tip'].bind('<FocusIn>', lambda e: on_entry_click(e, fields['tip']))
        fields['tip'].bind('<FocusOut>', lambda e: on_focus_out(e, fields['tip']))
        fields['tip'].pack(pady=2)

        # Materials
        fields['materials_label'] = tk.Label(dialog, text="Materials/Parts:", font=("Arial", 10, "bold"))
        fields['materials_label'].pack(pady=(5, 2))
        fields['materials'] = tk.Entry(dialog, width=30, fg='grey')
        fields['materials'].insert(0, "0.00")
        fields['materials'].bind('<FocusIn>', lambda e: on_entry_click(e, fields['materials']))
        fields['materials'].bind('<FocusOut>', lambda e: on_focus_out(e, fields['materials']))
        fields['materials'].pack(pady=2)

        # Fees
        fields['fees_label'] = tk.Label(dialog, text="Fees (permit/backflow):", font=("Arial", 10, "bold"))
        fields['fees_label'].pack(pady=(5, 2))
        fields['fees'] = tk.Entry(dialog, width=30, fg='grey')
        fields['fees'].insert(0, "0.00")
        fields['fees'].bind('<FocusIn>', lambda e: on_entry_click(e, fields['fees']))
        fields['fees'].bind('<FocusOut>', lambda e: on_focus_out(e, fields['fees']))
        fields['fees'].pack(pady=2)

        # Separator
        ttk.Separator(dialog, orient='horizontal').pack(fill='x', padx=20, pady=5)

        # Manual Commission Entry (hidden by default)
        fields['manual_commission_label'] = tk.Label(
            dialog,
            text="Manual Commission Amount:",
            font=("Arial", 10, "bold"),
            fg=self.dark_accent
        )
        fields['manual_commission'] = tk.Entry(dialog, width=30, fg='grey')
        fields['manual_commission'].insert(0, "0.00")
        fields['manual_commission'].bind('<FocusIn>', lambda e: on_entry_click(e, fields['manual_commission']))
        fields['manual_commission'].bind('<FocusOut>', lambda e: on_focus_out(e, fields['manual_commission']))

        # Calculate and display commission preview
        commission_label = tk.Label(dialog, text="Commission: $0.00", font=("Arial", 11, "bold"), fg=self.dark_accent)
        commission_label.pack(pady=10)

        def toggle_manual_mode(*args):
            """Toggle between manual and automatic commission calculation"""
            if fields['manual_override'].get():
                # Manual mode - disable formula fields
                fields['cc_check'].config(state=tk.DISABLED)
                fields['total'].config(state=tk.DISABLED, bg='#d3d3d3')
                fields['tip'].config(state=tk.DISABLED, bg='#d3d3d3')
                fields['materials'].config(state=tk.DISABLED, bg='#d3d3d3')
                fields['fees'].config(state=tk.DISABLED, bg='#d3d3d3')

                # Show manual commission field
                fields['manual_commission_label'].pack(pady=(5, 2))
                fields['manual_commission'].pack(pady=2)

                # Update commission display with manual value
                update_commission()
            else:
                # Auto mode - enable formula fields
                fields['cc_check'].config(state=tk.NORMAL)
                fields['total'].config(state=tk.NORMAL, bg='white')
                fields['tip'].config(state=tk.NORMAL, bg='white')
                fields['materials'].config(state=tk.NORMAL, bg='white')
                fields['fees'].config(state=tk.NORMAL, bg='white')

                # Hide manual commission field
                fields['manual_commission_label'].pack_forget()
                fields['manual_commission'].pack_forget()

                # Update commission display with calculated value
                update_commission()

        def update_commission(*args):
            try:
                if fields['manual_override'].get():
                    # Use manual commission
                    commission = float(fields['manual_commission'].get() or 0)
                    commission_label.config(text=f"Commission: ${commission:.2f} (Manual)")
                else:
                    # Use calculated commission
                    cc_used = fields['cc'].get()
                    total = float(fields['total'].get() or 0)
                    tip = float(fields['tip'].get() or 0)
                    materials = float(fields['materials'].get() or 0)
                    fees = float(fields['fees'].get() or 0)

                    commission = Invoice.calculate_commission_static(cc_used, total, tip, materials, fees)
                    commission_label.config(text=f"Commission: ${commission:.2f} (Calculated)")
            except ValueError:
                commission_label.config(text="Commission: $0.00")

        # Bind manual override checkbox
        fields['manual_override'].trace_add('write', toggle_manual_mode)

        # Bind all fields to update commission
        for field_name, field_widget in fields.items():
            if field_name == 'cc':
                field_widget.trace_add('write', update_commission)
            elif field_name == 'manual_commission':
                field_widget.bind('<KeyRelease>', update_commission)
            elif hasattr(field_widget, 'bind') and field_name in ['total', 'tip', 'materials', 'fees']:
                field_widget.bind('<KeyRelease>', update_commission)

        def save_invoice():
            try:
                number = fields['number'].get().strip()
                customer = fields['customer'].get().strip()
                date = fields['date'].get().strip()
                status = fields['status'].get()

                if not number or not customer:
                    messagebox.showwarning("Warning", "Please enter invoice number and customer name.")
                    return

                # Determine commission based on mode
                if fields['manual_override'].get():
                    # Manual commission mode
                    commission = float(fields['manual_commission'].get())
                    # Set formula fields to 0 for storage
                    total = 0.0
                    tip = 0.0
                    materials = 0.0
                    fees = 0.0
                    cc_used = False
                else:
                    # Calculated commission mode
                    cc_used = fields['cc'].get()
                    total = float(fields['total'].get())
                    tip = float(fields['tip'].get())
                    materials = float(fields['materials'].get())
                    fees = float(fields['fees'].get())

                    # Calculate commission using formula
                    invoice = Invoice(number, customer, date, emp.name, status, cc_used, total, tip, materials, fees)
                    commission = invoice.commission

                filename = emp.get_invoice_filename()
                os.makedirs("invoices", exist_ok=True)
                file_exists = os.path.exists(filename)

                with open(filename, 'a', newline='') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(["Invoice#", "Customer", "Date", "Status", "Total", "Tip", "Materials", "Fees",
                                         "Commission"])

                    writer.writerow([number, customer, date, status, f"{total:.2f}", f"{tip:.2f}",
                                     f"{materials:.2f}", f"{fees:.2f}", f"{commission:.2f}"])

                emp.weekly_pay += commission
                self.save_employees()
                self.load_employees()

                mode_text = "Manual" if fields['manual_override'].get() else "Calculated"
                messagebox.showinfo("Success", f"Invoice added!\nCommission: ${commission:.2f} ({mode_text})")
                dialog.destroy()
                self.view_employee_invoices(emp)

            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers for amounts.")

        tk.Button(dialog, text="Save Invoice", command=save_invoice, bg=self.accent_color, fg="white", width=15).pack(
            pady=20)

    def edit_invoice_dialog(self, emp: Employee, invoice_row: list):
        """Dialog to edit an existing invoice"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit Invoice - {emp.name}")
        dialog.geometry("450x700")
        self.center_window(dialog)  # Center the dialog

        fields = {}

        # Parse existing data
        old_invoice_number = invoice_row[0]
        old_customer = invoice_row[1]
        old_date = invoice_row[2]
        old_status = invoice_row[3]
        old_total = float(invoice_row[4])
        old_tip = float(invoice_row[5])
        old_materials = float(invoice_row[6])
        old_fees = float(invoice_row[7])
        old_commission = float(invoice_row[8])

        tk.Label(dialog, text=f"Edit Invoice #{old_invoice_number}", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(dialog, text=f"Employee: {emp.name}", font=("Arial", 10, "italic")).pack()

        # Invoice Number
        tk.Label(dialog, text="Invoice Number:", font=("Arial", 10, "bold")).pack(pady=(10, 2))
        fields['number'] = tk.Entry(dialog, width=30)
        fields['number'].insert(0, old_invoice_number)
        fields['number'].pack(pady=2)

        # Customer
        tk.Label(dialog, text="Customer:", font=("Arial", 10, "bold")).pack(pady=(5, 2))
        fields['customer'] = tk.Entry(dialog, width=30)
        fields['customer'].insert(0, old_customer)
        fields['customer'].pack(pady=2)

        # Date
        tk.Label(dialog, text="Date (MM/DD/YYYY):", font=("Arial", 10, "bold")).pack(pady=(5, 2))
        fields['date'] = tk.Entry(dialog, width=30)
        fields['date'].insert(0, old_date)
        fields['date'].pack(pady=2)

        # Status
        tk.Label(dialog, text="Status:", font=("Arial", 10, "bold")).pack(pady=(5, 2))
        fields['status'] = ttk.Combobox(dialog, values=["Paid", "Unpaid"], state="readonly", width=28)
        fields['status'].set(old_status)
        fields['status'].pack(pady=2)

        # Credit Card
        fields['cc'] = tk.BooleanVar(value=False)
        tk.Checkbutton(dialog, text="Credit Card Used", variable=fields['cc']).pack(pady=5)

        # Helper function to select all text on focus
        def on_entry_focus(event, entry):
            """Select all text when field is clicked"""
            entry.select_range(0, tk.END)
            entry.icursor(tk.END)

        # Total
        tk.Label(dialog, text="Total Sale:", font=("Arial", 10, "bold")).pack(pady=(5, 2))
        fields['total'] = tk.Entry(dialog, width=30)
        fields['total'].insert(0, str(old_total))
        fields['total'].bind('<FocusIn>', lambda e: on_entry_focus(e, fields['total']))
        fields['total'].pack(pady=2)

        # Tip
        tk.Label(dialog, text="Tip:", font=("Arial", 10, "bold")).pack(pady=(5, 2))
        fields['tip'] = tk.Entry(dialog, width=30)
        fields['tip'].insert(0, str(old_tip))
        fields['tip'].bind('<FocusIn>', lambda e: on_entry_focus(e, fields['tip']))
        fields['tip'].pack(pady=2)

        # Materials
        tk.Label(dialog, text="Materials/Parts:", font=("Arial", 10, "bold")).pack(pady=(5, 2))
        fields['materials'] = tk.Entry(dialog, width=30)
        fields['materials'].insert(0, str(old_materials))
        fields['materials'].bind('<FocusIn>', lambda e: on_entry_focus(e, fields['materials']))
        fields['materials'].pack(pady=2)

        # Fees
        tk.Label(dialog, text="Fees (permit/backflow):", font=("Arial", 10, "bold")).pack(pady=(5, 2))
        fields['fees'] = tk.Entry(dialog, width=30)
        fields['fees'].insert(0, str(old_fees))
        fields['fees'].bind('<FocusIn>', lambda e: on_entry_focus(e, fields['fees']))
        fields['fees'].pack(pady=2)

        # Commission preview
        commission_label = tk.Label(dialog, text=f"Commission: ${old_commission:.2f}", font=("Arial", 11, "bold"),
                                    fg=self.dark_accent)
        commission_label.pack(pady=10)

        def update_commission(*args):
            try:
                cc_used = fields['cc'].get()
                total = float(fields['total'].get() or 0)
                tip = float(fields['tip'].get() or 0)
                materials = float(fields['materials'].get() or 0)
                fees = float(fields['fees'].get() or 0)

                commission = Invoice.calculate_commission_static(cc_used, total, tip, materials, fees)
                commission_label.config(text=f"Commission: ${commission:.2f}")
            except ValueError:
                commission_label.config(text="Commission: $0.00")

        # Bind all fields
        for field_name, field_widget in fields.items():
            if field_name == 'cc':
                field_widget.trace_add('write', update_commission)
            elif hasattr(field_widget, 'bind'):
                field_widget.bind('<KeyRelease>', update_commission)

        def save_changes():
            try:
                new_number = fields['number'].get().strip()
                new_customer = fields['customer'].get().strip()
                new_date = fields['date'].get().strip()
                new_status = fields['status'].get()
                cc_used = fields['cc'].get()
                new_total = float(fields['total'].get())
                new_tip = float(fields['tip'].get())
                new_materials = float(fields['materials'].get())
                new_fees = float(fields['fees'].get())

                if not new_number or not new_customer:
                    messagebox.showwarning("Warning", "Invoice number and customer name cannot be empty.")
                    return

                filename = emp.get_invoice_filename()

                # Calculate new commission
                new_invoice = Invoice(new_number, new_customer, new_date, emp.name, new_status, cc_used, new_total,
                                      new_tip, new_materials, new_fees)
                new_commission = new_invoice.commission

                # Read all invoices
                invoices = []
                header = None
                with open(filename, 'r') as f:
                    reader = csv.reader(f)
                    header = next(reader)

                    for row in reader:
                        if row[0] == old_invoice_number:
                            # Update this invoice
                            invoices.append([new_number, new_customer, new_date, new_status,
                                             f"{new_total:.2f}", f"{new_tip:.2f}", f"{new_materials:.2f}",
                                             f"{new_fees:.2f}", f"{new_commission:.2f}"])
                        else:
                            invoices.append(row)

                # Write back
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                    writer.writerows(invoices)

                # Update employee's weekly pay
                commission_diff = new_commission - old_commission
                emp.weekly_pay += commission_diff
                self.save_employees()
                self.load_employees()

                messagebox.showinfo("Success", f"Invoice updated!\nNew Commission: ${new_commission:.2f}")
                dialog.destroy()
                self.view_employee_invoices(emp)

            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers for amounts.")

        tk.Button(dialog, text="Save Changes", command=save_changes, bg=self.accent_color, fg="white", width=15).pack(
            pady=20)

    def edit_employee_info(self):
        """Edit employee information (ID or Name)"""
        self.clear_right_panel()

        if not self.employees:
            self.show_message("No employees found.")
            return

        frame = tk.Frame(self.right_panel, bg="white")
        frame.pack(expand=True)

        tk.Label(
            frame,
            text="Edit Employee Info",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=10)

        tk.Label(frame, text="Select Employee:", bg="white", font=("Arial", 11)).pack(pady=5)

        emp_var = tk.StringVar()
        emp_combo = ttk.Combobox(
            frame,
            textvariable=emp_var,
            values=[f"{emp.id} - {emp.name}" for emp in self.employees],
            state="readonly",
            width=30
        )
        emp_combo.pack(pady=5)

        def edit_selected():
            if not emp_var.get():
                messagebox.showwarning("Warning", "Please select an employee first.")
                return

            emp_id = int(emp_var.get().split(" - ")[0])
            emp = self.find_employee(emp_id)

            # Dialog for editing
            dialog = tk.Toplevel(self.root)
            dialog.title(f"Edit {emp.name}")
            dialog.geometry("400x250")
            self.center_window(dialog)  # Center the dialog

            tk.Label(dialog, text=f"Edit Employee: {emp.name}", font=("Arial", 12, "bold")).pack(pady=10)

            # New ID
            tk.Label(dialog, text="New ID:", font=("Arial", 10)).pack(pady=5)
            id_entry = tk.Entry(dialog, width=30)
            id_entry.insert(0, str(emp.id))
            id_entry.pack(pady=2)

            # New Name
            tk.Label(dialog, text="New Name:", font=("Arial", 10)).pack(pady=5)
            name_entry = tk.Entry(dialog, width=30)
            name_entry.insert(0, emp.name)
            name_entry.pack(pady=2)

            def save_employee():
                try:
                    new_id = int(id_entry.get().strip())
                    new_name = name_entry.get().strip()

                    if not new_name:
                        messagebox.showwarning("Warning", "Name cannot be empty.")
                        return

                    # Check if new ID conflicts with another employee
                    if new_id != emp.id:
                        for e in self.employees:
                            if e.id == new_id:
                                messagebox.showerror("Error", f"ID {new_id} is already used by {e.name}.")
                                return

                    # Rename invoice file if name or ID changed
                    old_filename = emp.get_invoice_filename()
                    emp.id = new_id
                    emp.name = new_name
                    new_filename = emp.get_invoice_filename()

                    if old_filename != new_filename and os.path.exists(old_filename):
                        os.rename(old_filename, new_filename)

                    self.save_employees()
                    self.load_employees()

                    messagebox.showinfo("Success", f"Employee updated to ID {new_id}, Name: {new_name}")
                    dialog.destroy()
                    self.view_weekly_pay()

                except ValueError:
                    messagebox.showerror("Error", "Please enter a valid ID number.")

            tk.Button(dialog, text="Save", command=save_employee, bg=self.accent_color, fg="white", width=15).pack(
                pady=15)

        tk.Button(
            frame,
            text="Edit Selected Employee",
            command=edit_selected,
            bg=self.accent_color,
            fg="white",
            width=20,
            height=2
        ).pack(pady=20)

    def add_employee(self):
        """Add a new employee"""
        self.clear_right_panel()

        frame = tk.Frame(self.right_panel, bg="white")
        frame.pack(expand=True)

        tk.Label(
            frame,
            text="Add New Employee",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=10)

        tk.Label(frame, text="Employee ID:", bg="white", font=("Arial", 11)).pack(pady=(10, 2))
        id_entry = tk.Entry(frame, width=30)
        id_entry.pack(pady=5)

        tk.Label(frame, text="Employee Name:", bg="white", font=("Arial", 11)).pack(pady=(10, 2))
        name_entry = tk.Entry(frame, width=30)
        name_entry.pack(pady=5)

        def save_new_employee():
            try:
                emp_id = int(id_entry.get().strip())
                emp_name = name_entry.get().strip()

                if not emp_name:
                    messagebox.showwarning("Warning", "Name cannot be empty.")
                    return

                # Check if ID already exists
                if self.find_employee(emp_id):
                    messagebox.showerror("Error", f"Employee ID {emp_id} already exists.")
                    return

                new_emp = Employee(emp_id, emp_name)
                self.employees.append(new_emp)

                # Create employee CSV file
                filename = new_emp.get_invoice_filename()
                os.makedirs("invoices", exist_ok=True)

                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Invoice#", "Customer", "Date", "Status", "Total", "Tip", "Materials", "Fees",
                                     "Commission"])

                self.save_employees()
                self.load_employees()

                messagebox.showinfo("Success", f"Employee {emp_name} (ID: {emp_id}) added successfully!")
                self.view_weekly_pay()

            except ValueError:
                messagebox.showerror("Error", "Please enter a valid ID number.")

        tk.Button(
            frame,
            text="Add Employee",
            command=save_new_employee,
            bg=self.accent_color,
            fg="white",
            width=15,
            height=2
        ).pack(pady=20)

    def close_out_week(self):
        """Close out week for an employee"""
        self.clear_right_panel()

        if not self.employees:
            self.show_message("No employees found.")
            return

        frame = tk.Frame(self.right_panel, bg="white")
        frame.pack(expand=True)

        tk.Label(
            frame,
            text="Close Out Week",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=10)

        tk.Label(frame, text="Select Employee:", bg="white", font=("Arial", 11)).pack(pady=5)

        emp_var = tk.StringVar()
        emp_combo = ttk.Combobox(
            frame,
            textvariable=emp_var,
            values=[f"{emp.id} - {emp.name}" for emp in self.employees],
            state="readonly",
            width=30
        )
        emp_combo.pack(pady=5)

        def process_closeout():
            if not emp_var.get():
                messagebox.showwarning("Warning", "Please select an employee first.")
                return

            emp_id = int(emp_var.get().split(" - ")[0])
            emp = self.find_employee(emp_id)

            if emp.weekly_pay <= 0:
                messagebox.showinfo("Info", f"No commission or weekly pay to close out for {emp.name}.")
                return

            # Create dialog to ask for payment date
            date_dialog = tk.Toplevel(self.root)
            date_dialog.title("Enter Payment Date")
            date_dialog.geometry("350x200")
            self.center_window(date_dialog)
            date_dialog.transient(self.root)
            date_dialog.grab_set()

            tk.Label(
                date_dialog,
                text=f"Close Out Week for {emp.name}",
                font=("Arial", 12, "bold")
            ).pack(pady=10)

            tk.Label(
                date_dialog,
                text=f"Weekly Pay: ${emp.weekly_pay:.2f}",
                font=("Arial", 11)
            ).pack(pady=5)

            tk.Label(
                date_dialog,
                text="When will this payment be made?",
                font=("Arial", 10, "bold")
            ).pack(pady=(10, 5))

            tk.Label(
                date_dialog,
                text="Payment Date (MM/DD/YYYY):",
                font=("Arial", 10)
            ).pack(pady=(5, 2))

            date_entry = tk.Entry(date_dialog, width=25)
            date_entry.insert(0, datetime.now().strftime("%m/%d/%Y"))
            date_entry.pack(pady=5)
            date_entry.focus_set()
            date_entry.select_range(0, tk.END)

            result = {'confirmed': False, 'date': None}

            def confirm_closeout():
                payment_date = date_entry.get().strip()

                # Validate date format
                try:
                    datetime.strptime(payment_date, "%m/%d/%Y")
                    result['confirmed'] = True
                    result['date'] = payment_date
                    date_dialog.destroy()
                except ValueError:
                    messagebox.showerror("Invalid Date", "Please enter date in MM/DD/YYYY format.")

            def cancel_closeout():
                date_dialog.destroy()

            button_frame = tk.Frame(date_dialog)
            button_frame.pack(pady=15)

            tk.Button(
                button_frame,
                text="Confirm Close Out",
                command=confirm_closeout,
                bg=self.accent_color,
                fg="white",
                width=15
            ).pack(side=tk.LEFT, padx=5)

            tk.Button(
                button_frame,
                text="Cancel",
                command=cancel_closeout,
                width=10
            ).pack(side=tk.LEFT, padx=5)

            # Wait for dialog to close
            self.root.wait_window(date_dialog)

            if result['confirmed']:
                # Record payment in history with custom date
                self.record_payment(emp, emp.weekly_pay, result['date'])

                # Archive current invoices with custom date
                self.archive_invoices(emp, result['date'])

                emp.add_weekly_pay(emp.weekly_pay)
                weekly_amount = emp.weekly_pay
                emp.edit_pay(0)
                self.save_employees()
                self.load_employees()

                messagebox.showinfo(
                    "Success",
                    f"Weekly payout of ${weekly_amount:.2f} processed for {emp.name}.\n\n" +
                    f"Payment Date: {result['date']}\n" +
                    "Weekly pay reset to $0.00.\nInvoices archived and cleared."
                )
                self.close_out_week()

        tk.Button(
            frame,
            text="Process Close Out",
            command=process_closeout,
            bg=self.accent_color,
            fg="white",
            width=20,
            height=2
        ).pack(pady=20)

    def record_payment(self, emp: Employee, amount: float, payment_date: str = None):
        """Record a payment in the employee's payment history"""
        filename = emp.get_payment_history_filename()
        os.makedirs("payment_history", exist_ok=True)

        file_exists = os.path.exists(filename)
        if payment_date is None:
            payment_date = datetime.now().strftime("%m/%d/%Y")

        try:
            with open(filename, 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Date", "Amount"])
                writer.writerow([payment_date, f"{amount:.2f}"])
        except Exception as e:
            messagebox.showerror("Error", f"Error recording payment: {e}")

    def archive_invoices(self, emp: Employee, payment_date: str = None):
        """Archive current invoices and clear the active invoice file"""
        current_filename = emp.get_invoice_filename()

        if not os.path.exists(current_filename):
            return  # No invoices to archive

        # Create archive filename with payment date
        if payment_date is None:
            archive_date = datetime.now().strftime("%m-%d-%Y")
        else:
            # Convert MM/DD/YYYY to MM-DD-YYYY for filename
            archive_date = payment_date.replace('/', '-')
        archived_filename = emp.get_archived_invoice_filename(archive_date)
        os.makedirs("archived_invoices", exist_ok=True)

        try:
            # Copy current invoices to archive
            import shutil
            shutil.copy2(current_filename, archived_filename)

            # Clear the current invoice file but keep the header
            with open(current_filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Invoice#", "Customer", "Date", "Status", "Total", "Tip",
                                 "Materials", "Fees", "Commission"])
        except Exception as e:
            messagebox.showerror("Error", f"Error archiving invoices: {e}")

    def get_last_payment_date(self, emp: Employee) -> str:
        """Get the last payment date for an employee"""
        filename = emp.get_payment_history_filename()

        if not os.path.exists(filename):
            return "Never Paid"

        try:
            with open(filename, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                rows = list(reader)
                if rows:
                    # Return the last payment date
                    return rows[-1][0]
                else:
                    return "Never Paid"
        except Exception:
            return "Never Paid"

    def show_help(self):
        """Display help information"""
        self.clear_right_panel()

        help_text = """
HELP MENU - HOW TO USE EMPLOYEE PAYROLL TRACKER

1) View Weekly Pay
   Displays all employees and their current weekly pay.

2) View Year-to-Date (YTD) Pay
   Shows the total earnings for each employee for the year,
   including the last payment date.

3) Edit Employee Info
   Allows you to update an employee's ID or name if needed.

4) Manage Invoices
   Lets you view, add, edit, or change invoice status for each employee.
   These are the current active invoices for the week.

5) View Archived Invoices
   Browse and view invoices from previous weeks that have been paid out.
   Invoices are automatically archived when you close out a week.

6) Close Out Week
   Adds the employee's current weekly pay to their YTD total,
   resets weekly pay to $0, records the payment date,
   and archives all current invoices for future reference.

7) Add New Employee
   Registers a new employee and creates their individual CSV file.

8) Help
   Displays this help menu explaining all options.

9) About
   Displays program details, author information, and GitHub link.

Commission Calculation:
- Credit Card Used: ((Total - Materials - Fees) / 2) + Tip
- No Credit Card, Materials < $35: ((Total - Fees) / 2) + Tip
- No Credit Card, Materials ≥ $35: ((Total - Materials - Fees) / 2) + Tip + Materials
        """

        text_widget = scrolledtext.ScrolledText(
            self.right_panel,
            wrap=tk.WORD,
            font=("Courier", 10),
            bg="white",
            padx=10,
            pady=10
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)

    def show_about(self):
        """Display about information"""
        self.clear_right_panel()

        frame = tk.Frame(self.right_panel, bg="white")
        frame.pack(expand=True)

        about_text = """
EMPLOYEE PAYROLL TRACKER

Version: 2.0.0 (GUI)
Developed by: Emmanuel Diaz
Company: THRIVE Outdoor Solutions

Description: 
Tracks irrigation employees' weekly commissions, 
invoices, and year-to-date earnings.

GitHub: https://github.com/Ediazpy
        """

        tk.Label(
            frame,
            text=about_text,
            font=("Arial", 11),
            bg="white",
            justify=tk.CENTER
        ).pack(pady=20)

        def open_github():
            webbrowser.open("https://github.com/Ediazpy")

        tk.Button(
            frame,
            text="🔗 Visit GitHub",
            command=open_github,
            bg=self.accent_color,
            fg="white",
            width=15,
            height=2
        ).pack(pady=10)

    def show_message(self, message: str):
        """Display a simple message in the right panel"""
        self.clear_right_panel()

        label = tk.Label(
            self.right_panel,
            text=message,
            font=("Arial", 12),
            bg="white"
        )
        label.pack(expand=True)

    def find_employee(self, emp_id: int) -> Optional[Employee]:
        """Find employee by ID"""
        for emp in self.employees:
            if emp.id == emp_id:
                return emp
        return None

    def load_employees(self):
        """Load employees from CSV file"""
        self.employees.clear()

        if not os.path.exists("employees.csv"):
            return

        try:
            with open("employees.csv", 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header

                for row in reader:
                    if not row or not row[0].strip():
                        continue

                    if len(row) >= 4:
                        try:
                            emp_id = int(row[0].strip())
                            name = row[1].strip()
                            weekly_pay = float(row[2].strip())
                            ytd_pay = float(row[3].strip())

                            self.employees.append(Employee(emp_id, name, weekly_pay, ytd_pay))
                        except ValueError:
                            continue

        except IOError:
            pass

    def save_employees(self):
        """Save employees to CSV file"""
        try:
            with open("employees.csv", 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Name", "Weekly_Pay($)", "Year_To_Date_Pay($)"])

                for emp in self.employees:
                    writer.writerow([emp.id, emp.name, f"{emp.weekly_pay:.2f}",
                                     f"{emp.year_to_date_pay:.2f}"])
        except IOError as e:
            messagebox.showerror("Error", f"Error saving employees: {e}")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = PayrollTrackerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()