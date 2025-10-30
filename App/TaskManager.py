import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import random

class TaskApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Manager")
        self.root.geometry("1200x380")
        
        # Initialize the database
        self.init_database()
        
        # Create GUI
        self.create_widgets()
        self.load_tasks()

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
                task_id INTEGER,
                barcode TEXT,
                is_primary BOOLEAN NOT NULL CHECK (is_primary IN (0, 1)),
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS price (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                price DECIMAL(10, 2),
                currency CHAR(3) DEFAULT 'EUR',
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
        #                    --- Labels ---
        self.label_title = tk.Label(self.root, text="Title")
        self.label_desc = tk.Label(self.root, text="Description")
        self.label_quantity = tk.Label(self.root, text="Quantity")
        self.label_price = tk.Label(self.root, text="Price")
        self.label_PVN = tk.Label(self.root, text="PVN")
        
        self.label_title.grid(row=0, column=0, padx=5, pady=(5, 0), sticky="w")
        self.label_desc.grid(row=1, column=0, padx=5, pady=(5, 0), sticky="w")
        self.label_quantity.grid(row=2, column=0, padx=5, pady=(5, 0), sticky="w")
        self.label_price.grid(row=3, column=0, padx=5, pady=(5, 0), sticky="w")
        self.label_PVN.grid(row=4, column=0, padx=5, pady=(5, 0), sticky="w")

        #                        --- Entries ---
        self.fullName = tk.Entry(self.root, width=20)
        self.itemGroup = tk.Entry(self.root, width=20)
        self.inStock = tk.Entry(self.root, width=20)
        self.itemSuplier = tk.Entry(self.root, width=20)
        self.pvn = tk.Entry(self.root, width=20)
        self.searchQuery = tk.Entry(self.root, width=20)

        self.fullName.grid(row=0, column=1, padx=(0,5), pady=(5,0), sticky="w")
        self.itemGroup.grid(row=1, column=1, padx=(0,5), pady=(5,0), sticky="w")
        self.inStock.grid(row=2, column=1, padx=(0,5), pady=(5,0), sticky="w")
        self.itemSuplier.grid(row=3, column=1, padx=(0,5), pady=(5,0), sticky="w")
        self.pvn.grid(row=4, column=1, padx=(0,5), pady=(5,0), sticky="w")
        self.searchQuery.grid(row=8, column=1, padx=(0,5), pady=(5,0), sticky="w")

        #                          --- Treeview ---
        columns = ("id", "FullName", "ItemGroup", "ItemSuplier", "ItemStatus", "DateCreated", "InStock")
        self.tree = ttk.Treeview(self.root, columns=columns, selectmode=tk.EXTENDED, show="headings", height=11)
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=130)
        self.tree.grid(row=0, column=2, rowspan=5, padx=10, pady=5, sticky="nsew")
        self.tree.bind('<ButtonRelease-1>', self.on_item_select)

        #                        --- Button frame ---
        submitTask_button = tk.Button(
            self.root,
            text="Submit",
            command=self.add_task, 
            activebackground="blue",
            activeforeground="white",
            width=10
        )
        updateTask_button = tk.Button(
            self.root,
            text="Update", 
            command=self.update_task,
            activebackground="blue", 
            activeforeground="white",
            width=10
        )

        completeTask_button = tk.Button(
            self.root,
            text="Complete task", 
            command=self.mark_complete,
            activebackground="blue", 
            activeforeground="white"
        )
        deleteTask_button = tk.Button(
            self.root,
            text="Delete task", 
            command=self.delete_task,
            activebackground="blue", 
            activeforeground="white",
            width=15
        )
        searchForTask_button = tk.Button(
            self.root,
            text="Search", 
            command=self.search_for_tasks,
            activebackground="blue", 
            activeforeground="white",
            width=15
        )
        
        submitTask_button.grid(row=6, column=0, padx=5, pady=(10, 5), sticky="ew")
        updateTask_button.grid(row=6, column=1, padx=(0, 5), pady=(10, 5), sticky="ew")
        completeTask_button.grid(row=7, column=0, padx=5, pady=5, sticky="ew")
        deleteTask_button.grid(row=7, column=1, padx=5, pady=5, sticky="ew")
        searchForTask_button.grid(row=8, column=0, padx=5, pady=5, sticky="ew")

        #                               --- Combobox ---
        self.query = ttk.Combobox(self.root, values=["by id", "by title", "by status", "by description", "by quantity", "by stock", "All"])
        self.query.set("Select a search query")
        self.query.grid(row=8, column=2, padx=5, pady=5, sticky="w")

    def add_task(self):
        title = self.fullName.get().strip()
        description = self.itemGroup.get().strip()
        quantity = self.inStock.get().strip()
        price = self.itemSuplier.get().strip()
        Pvn = self.pvn.get().strip()

        fields = {'Title': title, 'Description': description, 'Quantity': quantity, 'Price': price, 'PVN': Pvn}
        missing = [name for name, value in fields.items() if not value]
        if missing:
            if len(missing) == 1:
                messagebox.showwarning("Warning", f"{missing[0]} is required!")
            else:
                messagebox.showwarning("Warning", f"The following fields are required:\n• " + "\n• ".join(missing))
            return

        self.cursor.execute("SELECT id FROM tasks ORDER BY id")
        existing_ids = [row[0] for row in self.cursor.fetchall()]
        next_id = 1
        for existing_id in existing_ids:
            if next_id < existing_id:
                break
            next_id = existing_id + 1

        self.cursor.execute(
            "INSERT INTO tasks (id, FullName, ItemGroup, ItemSuplier, InStock) VALUES (?, ?, ?, ?, ?)",
            (next_id, title, description, price, quantity)
        )

        self.cursor.execute("INSERT INTO price (task_id, price) VALUES (?, ?)", (next_id, price))

        barcode = random.randint(0, 9999999999999)
        barcode_str = f"{barcode:013}"
        self.cursor.execute("INSERT INTO barcode (task_id, barcode) VALUES (?, ?)", (next_id, barcode_str))

        self.conn.commit()
            
        self.fullName.delete(0, tk.END)
        self.itemGroup.delete(0, tk.END)
        self.inStock.delete(0, tk.END)
        self.itemSuplier.delete(0, tk.END)
        self.pvn.delete(0, tk.END)
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

        self.fullName.delete(0, tk.END)
        self.fullName.insert(0, values[1])
        self.itemGroup.delete(0, tk.END)
        self.itemGroup.insert(0, values[2])
        self.inStock.delete(0, tk.END)
        self.inStock.insert(0, values[6])
        self.itemSuplier.delete(0, tk.END)
        self.itemSuplier.insert(0, values[3])

        self.selected_id = values[0]

    def update_task(self):
        task_id = self.selected_id
        title = self.fullName.get().strip()
        description = self.itemGroup.get().strip()
        quantity = self.inStock.get().strip()
        price = self.itemSuplier.get().strip()

        fields = {'Title': title, 'Description': description, 'Quantity': quantity}
        missing = [name for name, value in fields.items() if not value]
        if missing:
            message = f"{missing[0]} is required!" if len(missing)==1 else f"The following fields are required:\n• " + "\n• ".join(missing)
            messagebox.showwarning("Warning", message)
            return

        self.cursor.execute(
            "UPDATE tasks SET FullName = ?, ItemGroup = ?, ItemSuplier = ?, InStock = ? WHERE id = ?",
            (title, description, price, quantity, task_id)
        )
        self.conn.commit()
        self.load_tasks()
        messagebox.showinfo("Success", "Task updated successfully!")
        del self.selected_id

    def delete_task(self):
        task_id = self.selected_id
        self.cursor.execute("DELETE FROM barcode WHERE task_id = ?", (task_id,))
        self.cursor.execute("DELETE FROM price WHERE task_id = ?", (task_id,))
        self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()
        self.load_tasks()
        messagebox.showinfo("Success", "Task deleted successfully!")
        del self.selected_id

    def mark_complete(self):
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
        elif query_type == "by title":
            sql = "SELECT * FROM tasks WHERE FullName LIKE ?"
            value = ('%' + value + '%',)
        elif query_type == "by status":
            sql = "SELECT * FROM tasks WHERE ItemStatus LIKE ?"
            value = (value,)
        elif query_type == "by description":
            sql = "SELECT * FROM tasks WHERE ItemGroup LIKE ?"
            value = ('%' + value + '%',)
        elif query_type == "by quantity":
            sql = "SELECT * FROM tasks WHERE ItemSuplier = ?"
            value = (value,)
        elif query_type == "by stock":
            sql = "SELECT * FROM tasks WHERE InStock = ?"
            value = (value,)
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
