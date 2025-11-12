import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import random
import pandas as pd
from typing import Optional, List, Tuple
from contextlib import contextmanager

class Database:
    
    def __init__(self, db_path: str = './Database/tasks.db'):
        self.db_path = db_path
        self._ensure_database_exists()
        
    def _ensure_database_exists(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            self._create_tables(cursor)
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def _create_tables(self, cursor):
        cursor.execute('''
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS barcode (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                barcode TEXT UNIQUE,
                is_primary INTEGER DEFAULT 1,
                FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                price DECIMAL(10, 2),
                currency TEXT DEFAULT 'EUR',
                FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS PVN (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                price_id INTEGER,
                pvn TEXT,
                FOREIGN KEY(price_id) REFERENCES price(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_status ON tasks(ItemStatus)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_barcode ON barcode(barcode)')

class TaskApp:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Test")
        self.root.geometry("1920x700")
        self.root.resizable(True, True)
        
        # Initialize database
        self.db = Database()
        
        # Load PVN values
        self.pvn_values = self._load_pvn_values()
        
        # Track selected task and mode
        self.selected_id: Optional[int] = None
        self.edit_mode: bool = False
        
        # Create GUI
        self.create_widgets()
        self.setup_keyboard_bindings()
        self.load_tasks()
        
    def _load_pvn_values(self) -> List[str]:
        """Load PVN values from CSV file."""
        try:
            df = pd.read_csv("./CSV/PVN.csv", header=None)
            return df.iloc[:, 0].dropna().astype(str).str.strip().tolist()
        except FileNotFoundError:
            messagebox.showwarning("Warning", "PVN.csv not found. Using default values.")
            return ["0%", "5%", "12%", "21%"]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load PVN values: {e}")
            return ["0%", "5%", "12%", "21%"]

    def create_widgets(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        self._create_input_frame()
        self._create_search_frame()
        self._create_tree_frame()

    def _create_input_frame(self):
        input_frame = tk.LabelFrame(self.root, text=" Task Input ", padx=10, pady=10)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="n")

        mode_frame = tk.Frame(input_frame, relief=tk.RIDGE, borderwidth=2)
        mode_frame.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="ew")
        
        self.mode_label = tk.Label(mode_frame, text="ADD MODE", pady=5)
        self.mode_label.pack(fill=tk.BOTH, expand=True)
        
        self.mode_button = tk.Button(mode_frame, text="Switch to Edit Mode", command=self.toggle_mode, pady=3)
        self.mode_button.pack(fill=tk.BOTH, expand=True, pady=(2, 0))

        # Labels with character counter for FullName
        labels = ["FullName (max 25)", "ItemGroup", "InStock", "ItemSuplier", "PVN", "Price", "Barcode (Optional)"]
        for i, label in enumerate(labels):
            tk.Label(input_frame, text=label).grid(row=i+1, column=0, padx=5, pady=5, sticky="w")

        # Entry fields
        self.fullName = tk.Entry(input_frame, width=25)
        self.fullName.bind('<KeyRelease>', self._check_fullname_length)
        self.itemGroup = tk.Entry(input_frame, width=25)
        self.inStock = tk.Entry(input_frame, width=25)
        self.itemSuplier = tk.Entry(input_frame, width=25)
        self.pvn = ttk.Combobox(input_frame, values=self.pvn_values, width=23)
        self.pvn.set("Select PVN")
        self.price = tk.Entry(input_frame, width=25)
        self.barcode = tk.Entry(input_frame, width=25)

        entries = [self.fullName, self.itemGroup, self.inStock, self.itemSuplier, 
                   self.pvn, self.price, self.barcode]
        for i, entry in enumerate(entries):
            entry.grid(row=i+1, column=1, padx=5, pady=5, sticky="w")

        # Buttons
        button_frame = tk.Frame(input_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=(15, 0))
        
        # Main action button (changes based on mode)
        self.action_button = tk.Button(button_frame, text="Add Task", command=self.handle_action, 
                                       activebackground="blue", activeforeground="white", width=12)
        self.action_button.grid(row=0, column=0, columnspan=2, padx=3, pady=3)
        
        buttons = [
            ("Complete", self.mark_complete, 1, 0, 12),
            ("Delete", self.delete_task, 1, 1, 12),
            ("Clear", self.clear_selection, 2, 0, 12),
            ("Refresh", self.load_tasks, 2, 1, 12),
            ("Export CSV", self.export_to_csv, 3, 0, 25)
        ]
        
        for text, command, row, col, width in buttons:
            btn = tk.Button(button_frame, text=text, command=command,
                           activebackground="blue", activeforeground="white", width=width)
            if width == 25:  # Export button spans both columns
                btn.grid(row=row, column=col, columnspan=2, padx=3, pady=3)
            else:
                btn.grid(row=row, column=col, padx=3, pady=3)
            
        self.update_mode_ui()

    def _create_search_frame(self):
        search_frame = tk.LabelFrame(self.root, text=" Search ", padx=10, pady=5)
        search_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
        
        tk.Label(search_frame, text="Search by:").grid(row=0, column=0, padx=5, pady=5)
        
        self.query = ttk.Combobox(search_frame, values=[
            "by id", "by FullName", "by ItemGroup", "by ItemSuplier", 
            "by ItemStatus", "by DateCreated", "by InStock", "All"
        ], width=15)
        self.query.set("All")
        self.query.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(search_frame, text="Search term:").grid(row=0, column=2, padx=5, pady=5)
        
        self.searchQuery = tk.Entry(search_frame, width=25)
        self.searchQuery.grid(row=0, column=3, padx=5, pady=5)
        self.searchQuery.bind('<Return>', lambda e: self.search_for_tasks())
        
        tk.Button(search_frame, text="Search", command=self.search_for_tasks,
                 activebackground="blue", activeforeground="white", width=12
                 ).grid(row=0, column=4, padx=5, pady=5)

    def _create_tree_frame(self):
        tree_frame = tk.LabelFrame(self.root, text=" Task List ", padx=10, pady=10)
        tree_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Treeview - expanded columns
        columns = ("id", "FullName", "ItemGroup", "ItemSuplier", "ItemStatus", 
                   "DateCreated", "InStock", "Barcode", "Price", "PVN")
        self.tree = ttk.Treeview(tree_frame, columns=columns, selectmode=tk.EXTENDED, 
                                 show="headings", height=15, yscrollcommand=scrollbar.set)
        
        scrollbar.config(command=self.tree.yview)
        
        # Configure columns with appropriate widths
        column_config = {
            "id": (50, "ID"),
            "FullName": (200, "Full Name"),
            "ItemGroup": (130, "Item Group"),
            "ItemSuplier": (130, "Supplier"),
            "ItemStatus": (90, "Status"),
            "DateCreated": (150, "Date Created"),
            "InStock": (80, "In Stock"),
            "Barcode": (140, "Barcode"),
            "Price": (80, "Price"),
            "PVN": (60, "PVN")
        }
        
        for col in columns:
            width, heading = column_config.get(col, (100, col.capitalize()))
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind('<ButtonRelease-1>', self.on_item_select)
        self.tree.bind('<Double-Button-1>', lambda e: self.handle_update())
        
        # Status bar
        self.status_label = tk.Label(tree_frame, text="Ready", anchor="w", relief=tk.SUNKEN)
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))
    
    def _check_fullname_length(self, event=None):
        """Check and enforce 25 character limit for FullName."""
        current = self.fullName.get()
        if len(current) > 25:
            self.fullName.delete(25, tk.END)
            self.update_status("⚠ FullName limited to 25 characters")

    def setup_keyboard_bindings(self):
        self.root.bind('<Escape>', lambda e: self.clear_selection())
        self.root.bind('<Control-s>', lambda e: self.handle_action())
        self.root.bind('<Control-d>', lambda e: self.delete_task())
        self.root.bind('<Delete>', lambda e: self.delete_task())
        self.root.bind('<F5>', lambda e: self.load_tasks())
        self.root.bind('<Control-m>', lambda e: self.toggle_mode())
        
        # Enter key navigation between fields
        fields = [self.fullName, self.itemGroup, self.inStock, self.itemSuplier, 
                  self.pvn, self.price, self.barcode]
        
        for i, field in enumerate(fields[:-1]):
            field.bind('<Return>', lambda e, next_field=fields[i+1]: next_field.focus())
        
        fields[-1].bind('<Return>', lambda e: self.handle_action())

    def clear_selection(self):
        """Clear all selections and input fields."""
        self.tree.selection_remove(self.tree.selection())
        
        for field in [self.fullName, self.itemGroup, self.inStock, self.itemSuplier, 
                      self.price, self.barcode]:
            field.delete(0, tk.END)
        
        self.pvn.set("Select PVN")
        self.selected_id = None

        if self.edit_mode:
            self.edit_mode = False
            self.update_mode_ui()
        
        self.update_status("Selection cleared")

    def toggle_mode(self):
        self.edit_mode = not self.edit_mode
        self.update_mode_ui()
        
        if self.edit_mode and self.selected_id is None:
            self.update_status("Edit mode: Select a task to edit")
        elif not self.edit_mode:
            self.clear_selection()
            self.update_status("Switched to Add mode")
        else:
            self.update_status("Edit mode activated")

    def update_mode_ui(self):
        if self.edit_mode:
            self.mode_label.config(text="EDIT MODE")
            self.mode_button.config(text="Switch to Add Mode")
            self.action_button.config(text="Update Task")
        else:
            self.mode_label.config(text="ADD MODE")
            self.mode_button.config(text="Switch to Edit Mode")
            self.action_button.config(text="Add Task")

    def handle_action(self):
        if self.edit_mode:
            self.handle_update()
        else:
            self.handle_submit()

    def validate_inputs(self, for_update: bool = False) -> bool:
        # Check required fields
        fields = {
            'FullName': self.fullName.get().strip(),
            'ItemGroup': self.itemGroup.get().strip(),
            'InStock': self.inStock.get().strip(),
            'ItemSuplier': self.itemSuplier.get().strip(),
            'Price': self.price.get().strip()
        }
        
        missing = [name for name, value in fields.items() if not value]
        if missing:
            messagebox.showwarning("Validation Error", 
                                  f"Required fields missing:\n• " + "\n• ".join(missing))
            return False
        
        # Check FullName length
        if len(fields['FullName']) > 25:
            messagebox.showwarning("Validation Error", 
                                  "FullName must be 25 characters or less!")
            return False

        # Check numeric fields
        numeric_fields = {'InStock': fields['InStock'], 'Price': fields['Price']}
        invalid = [name for name, value in numeric_fields.items() 
                  if not value.replace('.', '', 1).isdigit()]
        
        if invalid:
            messagebox.showwarning("Validation Error", 
                                  f"Non-numeric values in:\n• " + "\n• ".join(invalid))
            return False

        # Check PVN selection
        if self.pvn.get() in ["Select PVN", ""] or self.pvn.get() not in self.pvn_values:
            messagebox.showwarning("Validation Error", "Please select a valid PVN!")
            return False
        
        # For updates, check if task is selected
        if for_update and self.selected_id is None:
            messagebox.showwarning("Validation Error", "Please select a task to update!")
            return False
        
        return True

    def handle_submit(self):
        if not self.validate_inputs():
            return
        self.add_task()

    def handle_update(self):
        if not self.validate_inputs(for_update=True):
            return
        self.update_task()

    def add_task(self):
        try:
            title = self.fullName.get().strip()
            description = self.itemGroup.get().strip()
            quantity = int(self.inStock.get().strip())
            suplier = self.itemSuplier.get().strip()
            price = float(self.price.get().strip())
            pvn = self.pvn.get().strip()
            barcode = self.barcode.get().strip() or f"{random.randint(0, 9999999999999):013}"

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get next available ID
                cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM tasks")
                next_id = cursor.fetchone()[0]
                
                # Insert price
                cursor.execute("INSERT INTO price (task_id, price) VALUES (?, ?)", 
                              (next_id, price))
                price_id = cursor.lastrowid
                
                # Insert PVN
                cursor.execute("INSERT INTO PVN (price_id, pvn) VALUES (?, ?)", 
                              (price_id, pvn))
                pvn_id = cursor.lastrowid
                
                # Insert task
                cursor.execute(
                    "INSERT INTO tasks (id, FullName, ItemGroup, ItemSuplier, InStock, pvn_id) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (next_id, title, description, suplier, quantity, pvn_id)
                )
                
                # Insert barcode
                cursor.execute("INSERT INTO barcode (task_id, barcode) VALUES (?, ?)",
                              (next_id, barcode))
                
                conn.commit()
            
            self.clear_selection()
            self.load_tasks()
            self.update_status(f"Task '{title}' added successfully")
            messagebox.showinfo("Success", "Task added successfully!")
            
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Barcode already exists: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add task: {e}")

    def load_tasks(self):
        try:
            for row in self.tree.get_children():
                self.tree.delete(row)
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        t.id,
                        t.FullName,
                        t.ItemGroup,
                        t.ItemSuplier,
                        t.ItemStatus,
                        t.DateCreated,
                        t.InStock,
                        COALESCE(b.barcode, ''),
                        COALESCE(p.price, 0),
                        COALESCE(pvn.pvn, '')
                    FROM tasks t
                    LEFT JOIN barcode b ON t.id = b.task_id
                    LEFT JOIN price p ON t.id = p.task_id
                    LEFT JOIN PVN pvn ON t.pvn_id = pvn.id
                    ORDER BY t.id DESC
                """)
                tasks = cursor.fetchall()
                
                for row in tasks:
                    # Color-code completed tasks
                    tag = 'completed' if row[4] == 'completed' else ''
                    self.tree.insert("", tk.END, values=row, tags=(tag,))
                
                self.tree.tag_configure('completed', background='#d4edda')
                
                self.update_status(f"Loaded {len(tasks)} tasks")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tasks: {e}")

    def on_item_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        values = item['values']
        if not values:
            return

        task_id = values[0]
        self.selected_id = task_id
        
        if not self.edit_mode:
            self.edit_mode = True
            self.update_mode_ui()
        
        try:
            self.fullName.delete(0, tk.END)
            self.fullName.insert(0, str(values[1]))
            self.itemGroup.delete(0, tk.END)
            self.itemGroup.insert(0, str(values[2]))
            self.itemSuplier.delete(0, tk.END)
            self.itemSuplier.insert(0, str(values[3]))
            self.inStock.delete(0, tk.END)
            self.inStock.insert(0, str(values[6]))
            self.barcode.delete(0, tk.END)
            self.barcode.insert(0, str(values[7]))
            self.price.delete(0, tk.END)
            self.price.insert(0, str(values[8]))
            self.pvn.set(str(values[9]))
            
            self.update_status(f"Editing task ID: {task_id}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load task details: {e}")

    def update_task(self):
        if self.selected_id is None:
            return
        
        try:
            task_id = self.selected_id
            title = self.fullName.get().strip()
            description = self.itemGroup.get().strip()
            quantity = int(self.inStock.get().strip())
            suplier = self.itemSuplier.get().strip()
            price = float(self.price.get().strip())
            pvn = self.pvn.get().strip()
            barcode = self.barcode.get().strip()

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Update task
                cursor.execute(
                    "UPDATE tasks SET FullName = ?, ItemGroup = ?, ItemSuplier = ?, InStock = ? "
                    "WHERE id = ?",
                    (title, description, suplier, quantity, task_id)
                )
                
                # Update price
                cursor.execute("UPDATE price SET price = ? WHERE task_id = ?", 
                              (price, task_id))
                
                # Update PVN
                cursor.execute("""
                    UPDATE PVN SET pvn = ? 
                    WHERE price_id IN (SELECT id FROM price WHERE task_id = ?)
                """, (pvn, task_id))
                
                # Update barcode if provided
                if barcode:
                    cursor.execute("UPDATE barcode SET barcode = ? WHERE task_id = ?", 
                                  (barcode, task_id))
                
                conn.commit()
            
            self.load_tasks()
            self.update_status(f"Task '{title}' updated successfully")
            messagebox.showinfo("Success", "Task updated successfully!")
            
            # Clear and switch back to add mode after update
            self.clear_selection()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update task: {e}")

    def delete_task(self):
        """Delete selected task from database."""
        if self.selected_id is None:
            messagebox.showwarning("Warning", "Please select a task to delete!")
            return
        
        if not messagebox.askyesno("Confirm Delete", 
                                   "Are you sure you want to delete this task?"):
            return
        
        try:
            task_id = self.selected_id
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get task name for status message
                cursor.execute("SELECT FullName FROM tasks WHERE id = ?", (task_id,))
                task_name = cursor.fetchone()[0]
                
                # Delete task (cascading will handle related records)
                cursor.execute("DELETE FROM barcode WHERE task_id = ?", (task_id,))
                cursor.execute("DELETE FROM price WHERE task_id = ?", (task_id,))
                cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                
                conn.commit()
            
            self.clear_selection()
            self.load_tasks()
            self.update_status(f"Task '{task_name}' deleted")
            messagebox.showinfo("Success", "Task deleted successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete task: {e}")

    def mark_complete(self):
        """Mark selected task as completed."""
        if self.selected_id is None:
            messagebox.showwarning("Warning", "Please select a task to mark as complete!")
            return
        
        try:
            task_id = self.selected_id
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE tasks SET ItemStatus = ? WHERE id = ?", 
                              ("completed", task_id))
                conn.commit()
            
            self.load_tasks()
            self.update_status("Task marked as completed")
            messagebox.showinfo("Success", "Task marked as completed!")
            self.selected_id = None
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to mark task as complete: {e}")

    def search_for_tasks(self):
        """Search for tasks based on selected criteria."""
        query_type = self.query.get().strip()
        search_term = self.searchQuery.get().strip()
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                base_select = """
                    SELECT 
                        t.id,
                        t.FullName,
                        t.ItemGroup,
                        t.ItemSuplier,
                        t.ItemStatus,
                        t.DateCreated,
                        t.InStock,
                        COALESCE(b.barcode, ''),
                        COALESCE(p.price, 0),
                        COALESCE(pvn.pvn, '')
                    FROM tasks t
                    LEFT JOIN barcode b ON t.id = b.task_id
                    LEFT JOIN price p ON t.id = p.task_id
                    LEFT JOIN PVN pvn ON t.pvn_id = pvn.id
                """
                
                query_map = {
                    "by id": (f"{base_select} WHERE t.id = ?", (search_term,)),
                    "by FullName": (f"{base_select} WHERE t.FullName LIKE ?", (f'%{search_term}%',)),
                    "by ItemGroup": (f"{base_select} WHERE t.ItemGroup LIKE ?", (f'%{search_term}%',)),
                    "by ItemSuplier": (f"{base_select} WHERE t.ItemSuplier LIKE ?", (f'%{search_term}%',)),
                    "by ItemStatus": (f"{base_select} WHERE t.ItemStatus = ?", (search_term,)),
                    "by DateCreated": (f"{base_select} WHERE DATE(t.DateCreated) = ?", (search_term,)),
                    "by InStock": (f"{base_select} WHERE t.InStock = ?", (search_term,)),
                    "All": (f"{base_select} ORDER BY t.id DESC", ())
                }
                
                if query_type not in query_map:
                    messagebox.showwarning("Warning", "Please select a valid search query!")
                    return
                
                sql, params = query_map[query_type]
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                # Update treeview
                for row in self.tree.get_children():
                    self.tree.delete(row)
                
                for row in rows:
                    tag = 'completed' if row[4] == 'completed' else ''
                    self.tree.insert("", tk.END, values=row, tags=(tag,))
                
                self.tree.tag_configure('completed', background='#d4edda')
                self.update_status(f"Found {len(rows)} tasks")
                
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {e}")

    def update_status(self, message: str):
        """Update status bar message."""
        self.status_label.config(text=message)
    
    def export_to_csv(self):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT 
                        t.FullName,
                        b.barcode,
                        p.price,
                        pvn.pvn
                    FROM tasks t
                    LEFT JOIN barcode b ON t.id = b.task_id
                    LEFT JOIN price p ON t.id = p.task_id
                    LEFT JOIN PVN pvn ON t.pvn_id = pvn.id
                    ORDER BY t.id DESC
                """)
                
                rows = cursor.fetchall()
                
                if not rows:
                    messagebox.showinfo("Info", "No data to export!")
                    return
                
                # Format prices with exactly 2 decimal places and comma separator
                formatted_rows = []
                for row in rows:
                    fullname, barcode, price, pvn = row
                    # Format price with 2 decimals and comma separator
                    price_formatted = f"{float(price):.2f}".replace('.', ',')
                    # Format PVN consistently
                    pvn_formatted = str(pvn).replace('.', ',')
                    formatted_rows.append([fullname, barcode, price_formatted, pvn_formatted])
                
                df = pd.DataFrame(formatted_rows, columns=['FullName', 'Barcode', 'Price', 'PVN'])
                csv_path = "./CSV/export.csv"
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                
                self.update_status(f"Exported {len(rows)} records to {csv_path}")
                messagebox.showinfo("Success", f"Data exported successfully to:\n{csv_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TaskApp(root)
    root.mainloop()