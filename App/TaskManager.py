import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import random
import pandas as pd
import keyboard

df = pd.read_csv("./CSV/PVN.csv", header=None)
pvn_values = df.iloc[:, 0].dropna().astype(str).str.strip().tolist()

class TaskApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Manager")
        self.root.geometry("1250x420")
        
        # Initialize the database
        self.init_database()
        
        # Create GUI
        self.create_widgets()
        self.setup_enter_navigation()
        self.load_tasks()
        self.root.bind('<Escape>', self.clear_selection)

    def init_database(self):
        db_folder = './Database'
        os.makedirs(db_folder, exist_ok=True)
        
        self.conn = sqlite3.connect('./Database/tasks.db')
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                FullName TEXT NOT NULL,
                ItemGroup TEXT,
                ItemSuplier TEXT,
                ItemStatus TEXT DEFAULT 'pending',
                DateCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                InStock INTEGER,
                pvn_id INTEGER,
                FOREIGN KEY(pvn_id) REFERENCES PVN(id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS barcode (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                barcode INTEGER,
                is_primary INTEGER,
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS price (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                price DECIMAL(10, 2),
                currency TEXT DEFAULT 'EUR',
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS PVN (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                price_id INTEGER,
                pvn INTEGER,
                FOREIGN KEY(price_id) REFERENCES price(id)
            )
        ''')
        
        self.conn.commit()

    def create_widgets(self):
        #                   --- Input frame ---
        input_frame = tk.LabelFrame(self.root, text=" Task Input ", padx=10, pady=10)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="n")

        search_frame = tk.LabelFrame(self.root, text=" Search ", padx=10, pady=5)
        search_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
        
        tk.Label(search_frame, text="Search by:").grid(row=0, column=0, padx=5, pady=5)
        
        self.query = ttk.Combobox(search_frame, values=["by id", "by FullName", "by ItemGroup", "by ItemSuplier", "by ItemStatus", "by DateCreated", "by InStock", "All"])
        self.query.set("Select a search query")
        self.query.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(search_frame, text="Search term:").grid(row=0, column=2, padx=5, pady=5)
        
        self.searchQuery = tk.Entry(search_frame, width=20)
        self.searchQuery.grid(row=0, column=3, padx=5, pady=5)
        
        
        #                    --- Labels ---
        tk.Label(input_frame, text="FullName").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tk.Label(input_frame, text="ItemGroup").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        tk.Label(input_frame, text="InStock").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        tk.Label(input_frame, text="ItemSuplier").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        tk.Label(input_frame, text="PVN(0-3)").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        tk.Label(input_frame, text="Price").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        tk.Label(input_frame, text="Barcode (Optional)").grid(row=6, column=0, padx=5, pady=5, sticky="w")

        #                        --- Entries ---
        self.fullName = tk.Entry(input_frame, width=20)
        self.itemGroup = tk.Entry(input_frame, width=20)
        self.inStock = tk.Entry(input_frame, width=20)
        self.itemSuplier = tk.Entry(input_frame, width=20)
        self.pvn = ttk.Combobox(input_frame, values=pvn_values)
        self.pvn.set("Select the PVN")
        self.price = tk.Entry(input_frame, width=20)
        self.barcode = tk.Entry(input_frame, width=20)

        self.fullName.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.itemGroup.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.inStock.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.pvn.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        self.itemSuplier.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.price.grid(row=5, column=1, padx=5, pady=5, sticky="w")
        self.barcode.grid(row=6, column=1, padx=5, pady=5, sticky="w")

         # --- Treeview Frame ---
        tree_frame = tk.LabelFrame(self.root, text=" Task List ", padx=10, pady=10)
        tree_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # --- Treeview ---
        columns = ("id", "FullName", "ItemGroup", "ItemSuplier", "ItemStatus", "DateCreated", "InStock")
        self.tree = ttk.Treeview(tree_frame, columns=columns, selectmode=tk.EXTENDED, show="headings", height=11)
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=130)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind('<ButtonRelease-1>', self.on_item_select)

           # --- Buttons Frame ---
        
        self.tree.bind('<Escape>', self.clear_selection)
        button_frame = tk.Frame(input_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=(10, 0))
        
        submitTask_button = tk.Button(
            button_frame,
            text="Submit",
            command=lambda: self.validate(self.add_task), 
            activebackground="blue",
            activeforeground="white",
            width=10
        )
        updateTask_button = tk.Button(
            button_frame,
            text="Update", 
            command=lambda: self.validate(self.update_task),
            activebackground="blue", 
            activeforeground="white",
            width=10
        )
        completeTask_button = tk.Button(
            button_frame,
            text="Complete task", 
            command=self.mark_complete,
            activebackground="blue", 
            activeforeground="white",
            width=12
        )
        deleteTask_button = tk.Button(
            button_frame,
            text="Delete task", 
            command=self.delete_task,
            activebackground="blue", 
            activeforeground="white",
            width=12
        )
        searchQuery_button = tk.Button(
            search_frame,
            text="Search", 
            command=self.search_for_tasks,
            activebackground="blue", 
            activeforeground="white",
            width=12
        )
        
        submitTask_button.grid(row=0, column=0, padx=3, pady=3)
        updateTask_button.grid(row=0, column=1, padx=3, pady=3)
        completeTask_button.grid(row=1, column=0, padx=3, pady=3)
        deleteTask_button.grid(row=1, column=1, padx=3, pady=3)
        searchQuery_button.grid(row=0, column=4, padx=3, pady=3)

    def setup_enter_navigation(self):
        """Set up Enter key to navigate between fields"""
        self.input_fields = [
            self.fullName,
            self.itemGroup,
            self.inStock,
            self.itemSuplier,
            self.pvn,
            self.price,
            self.barcode
        ]
        
        for i, field in enumerate(self.input_fields):
            if i < len(self.input_fields) - 1:
                next_field = self.input_fields[i + 1]
                field.bind('<Return>', lambda e, nf=next_field: nf.focus())
            else:
                field.bind('<Return>', lambda e: self.validate(self.add_task))

    def clear_selection(self, event=None):
        self.tree.selection_remove(self.tree.selection())
        
        self.fullName.delete(0, tk.END)
        self.itemGroup.delete(0, tk.END)
        self.inStock.delete(0, tk.END)
        self.itemSuplier.delete(0, tk.END)
        self.pvn.set("Select the PVN")
        self.price.delete(0, tk.END)
        self.barcode.delete(0, tk.END)

        if hasattr(self, 'selected_id'):
            del self.selected_id

    def validate(self, action_function):
        title = self.fullName.get().strip()
        description = self.itemGroup.get().strip()
        quantity = self.inStock.get().strip()
        suplier = self.itemSuplier.get().strip()
        price = self.price.get().strip()
        Pvn = self.pvn.get().strip()
    
        try:
            fields = {'FullName': title, 'ItemGroup': description, 'InStock': quantity, 'ItemSuplier': suplier, 'Price': price}
            missing = [name for name, value in fields.items() if not value]
            if missing:
                if len(missing) == 1:
                    messagebox.showwarning("Warning", f"{missing[0]} is required!")
                else:
                    messagebox.showwarning("Warning", "The following fields are required:\n• " + "\n• ".join(missing))
                return

            fields2 = {'Quantity': quantity, 'Price': price}
            notNumerical = [name for name, value in fields2.items() 
                            if not str(value).isdigit()]
            if notNumerical:
                if len(notNumerical) == 1:
                    messagebox.showwarning("Warning", f"{notNumerical[0]} must be numeric!")
                else:
                    messagebox.showwarning("Warning", "The following fields are non-numeric:\n• " + "\n• ".join(notNumerical))
                return

            if Pvn == "Select the PVN" or not Pvn:
                messagebox.showwarning("Warning", "Please select a valid PVN!")
                return
            
            if action_function == self.update_task and not hasattr(self, 'selected_id'):
                messagebox.showwarning("Warning", "Please select a task to update!")
                return
            
            return action_function()
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def add_task(self):
        title = self.fullName.get().strip()
        description = self.itemGroup.get().strip()
        quantity = self.inStock.get().strip()
        suplier = self.itemSuplier.get().strip()
        price = self.price.get().strip()
        Pvn = self.pvn.get().strip()
        barcode = self.barcode.get().strip()

        if not barcode:
            numbers = random.randint(0, 9999999999999)
            num = f"{numbers:013}"
        else:
            num = barcode

        self.cursor.execute("SELECT id FROM tasks ORDER BY id")
        existing_ids = [row[0] for row in self.cursor.fetchall()]
        next_id = 1
        for existing_id in existing_ids:
            if next_id < existing_id:
                break
            next_id = existing_id + 1

        self.cursor.execute("INSERT INTO price (task_id, price) VALUES (?, ?)", (next_id, price))
        price_id = self.cursor.lastrowid
        
        self.cursor.execute("INSERT INTO PVN (price_id, pvn) VALUES (?, ?)", (price_id, Pvn))
        pvn_id = self.cursor.lastrowid

        self.cursor.execute(
            "INSERT INTO tasks (id, FullName, ItemGroup, ItemSuplier, InStock, pvn_id) VALUES (?, ?, ?, ?, ?, ?)",
            (next_id, title, description, suplier, quantity, pvn_id)
        )

        self.cursor.execute(
            "INSERT INTO barcode (task_id, barcode) VALUES (?, ?)",
            (next_id, num)
        )

        self.conn.commit()
            
        self.fullName.delete(0, tk.END)
        self.itemGroup.delete(0, tk.END)
        self.inStock.delete(0, tk.END)
        self.itemSuplier.delete(0, tk.END)
        self.pvn.set("Select the PVN")
        self.price.delete(0, tk.END)
        self.barcode.delete(0, tk.END)
        
        self.load_tasks()
        messagebox.showinfo("Success", "Task added!")

    def load_tasks(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.cursor.execute("SELECT * FROM tasks")
        for row in self.cursor.fetchall():
            self.tree.insert("", tk.END, values=row)
    
    def on_item_select(self, event):
        item_id = self.tree.focus()
        item = self.tree.item(item_id)
        values = item['values']
        if not values:
            return

        task_id = values[0]
        
        self.fullName.delete(0, tk.END)
        self.fullName.insert(0, str(values[1]))
        self.itemGroup.delete(0, tk.END)
        self.itemGroup.insert(0, str(values[2]))
        self.itemSuplier.delete(0, tk.END)
        self.itemSuplier.insert(0, str(values[3]))
        self.inStock.delete(0, tk.END)
        self.inStock.insert(0, str(values[6]))
        
        self.cursor.execute("SELECT id, price FROM price WHERE task_id = ?", (task_id,))
        price_result = self.cursor.fetchone()
        self.price.delete(0, tk.END)
        if price_result:
            self.price.insert(0, str(int(float(price_result[1]))))
        else:
            self.price.insert(0, "")

        if price_result:
            price_id = price_result[0]
            self.cursor.execute("SELECT pvn FROM PVN WHERE price_id = ?", (price_id,))
            pvn_result = self.cursor.fetchone()

        else:
            pvn_result = None
            
        self.pvn.set("")
        if pvn_result:
            pvn_str = str(pvn_result[0]).strip()
            matching_value = None
            for pv in pvn_values:
                if pvn_str in pv or pv.startswith(pvn_str):
                    matching_value = pv
                    break
            if matching_value:
                self.pvn.set(matching_value)
            else:
                self.pvn.set(pvn_str)

        self.cursor.execute("SELECT barcode FROM barcode WHERE task_id = ?", (task_id,))
        barcode_result = self.cursor.fetchone()
        self.barcode.delete(0, tk.END)
        if barcode_result:
            self.barcode.insert(0, str(barcode_result[0]))
        else:
            self.barcode.insert(0, "")

        self.selected_id = task_id

    def update_task(self):
        task_id = self.selected_id
        title = self.fullName.get().strip()
        description = self.itemGroup.get().strip()
        quantity = self.inStock.get().strip()
        suplier = self.itemSuplier.get().strip()
        price = self.price.get().strip()
        pvn = self.pvn.get().strip()
        barcode = self.barcode.get().strip()

        self.cursor.execute(
            "UPDATE tasks SET FullName = ?, ItemGroup = ?, ItemSuplier = ?, InStock = ? WHERE id = ?",
            (title, description, suplier, quantity, task_id)
        )

        self.cursor.execute("UPDATE price SET price = ? WHERE task_id = ?", (price, task_id))

        self.cursor.execute("""
            UPDATE PVN SET pvn = ? 
            WHERE price_id IN (SELECT id FROM price WHERE task_id = ?)
        """, (pvn, task_id))

        if barcode:
            self.cursor.execute("UPDATE barcode SET barcode = ? WHERE task_id = ?", (barcode, task_id))

        self.conn.commit()
        self.load_tasks()
        messagebox.showinfo("Success", "Task updated successfully!")
        del self.selected_id

    def delete_task(self):
        if not hasattr(self, 'selected_id'):
            messagebox.showwarning("Warning", "Please select a task to delete!")
            return
            
        task_id = self.selected_id
        self.cursor.execute("DELETE FROM barcode WHERE task_id = ?", (task_id,))
        self.cursor.execute("DELETE FROM price WHERE task_id = ?", (task_id,))
        self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()
        self.load_tasks()
        messagebox.showinfo("Success", "Task deleted successfully!")
        del self.selected_id

    def mark_complete(self):
        if not hasattr(self, 'selected_id'):
            messagebox.showwarning("Warning", "Please select a task to mark as complete!")
            return
            
        task_id = self.selected_id
        self.cursor.execute("UPDATE tasks SET ItemStatus = ? WHERE id = ?", ("completed", task_id))
        self.conn.commit()
        self.load_tasks()
        messagebox.showinfo("Success", "Task completed successfully!")
        del self.selected_id

    def search_for_tasks(self):
        value = self.searchQuery.get().strip()
        query_type = self.query.get().strip()
        if query_type == "by id":
            sql = "SELECT * FROM tasks WHERE id = ?"
            value = (value,)
        elif query_type == "by FullName":
            sql = "SELECT * FROM tasks WHERE FullName LIKE ?"
            value = ('%' + value + '%',)
        elif query_type == "by ItemGroup":
            sql = "SELECT * FROM tasks WHERE ItemGroup LIKE ?"
            value = ('%' + value + '%',)
        elif query_type == "by ItemSuplier":
            sql = "SELECT * FROM tasks WHERE ItemSuplier LIKE ?"
            value = ('%' + value + '%',)
        elif query_type == "by ItemStatus":
            sql = "SELECT * FROM tasks WHERE ItemStatus = ?"
            value = (value,)
        elif query_type == "by DateCreated":
            sql = "SELECT * FROM tasks WHERE DateCreated = ?"
            value = (value,)
        elif query_type == "by InStock":
            sql = "SELECT * FROM tasks WHERE InStock LIKE ?"
            value = ('%' + value + '%',)
        elif query_type == "All":
            sql = "SELECT * FROM tasks"
            value = ()
        else:
            return

        self.cursor.execute(sql, value)
        rows = self.cursor.fetchall()
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in rows:
            self.tree.insert("", tk.END, values=row)
        
if __name__ == "__main__":
    root = tk.Tk()
    app = TaskApp(root)
    root.mainloop()