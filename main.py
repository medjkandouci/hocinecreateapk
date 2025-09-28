import flet as ft
import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect('products.db', check_same_thread=False)
        self.create_table()
    
    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                created_date TEXT NOT NULL
            )
        ''')
        self.conn.commit()
    
    def create_product(self, name, category, price, quantity):
        cursor = self.conn.cursor()
        created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO products (name, category, price, quantity, created_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, category, price, quantity, created_date))
        self.conn.commit()
        return cursor.lastrowid
    
    def read_products(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM products ORDER BY id DESC')
        return cursor.fetchall()
    
    def update_product(self, product_id, name, category, price, quantity):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE products 
            SET name=?, category=?, price=?, quantity=?
            WHERE id=?
        ''', (name, category, price, quantity, product_id))
        self.conn.commit()
        return cursor.rowcount
    
    def delete_product(self, product_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM products WHERE id=?', (product_id,))
        self.conn.commit()
        return cursor.rowcount
    
    def search_products(self, search_term):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM products 
            WHERE name LIKE ? OR category LIKE ?
            ORDER BY id DESC
        ''', (f'%{search_term}%', f'%{search_term}%'))
        return cursor.fetchall()

class ProductManagerApp:
    def __init__(self):
        self.db = DatabaseManager()
        self.current_edit_id = None
        self.page = None
    
    def main(self, page: ft.Page):
        self.page = page  # Store page reference
        page.title = "Product Management System"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 20
        page.scroll = ft.ScrollMode.AUTO
        
        # Form fields
        self.name_field = ft.TextField(
            label="Product Name",
            hint_text="Enter product name",
            width=400
        )
        self.category_field = ft.TextField(
            label="Category",
            hint_text="Enter category",
            width=400
        )
        self.price_field = ft.TextField(
            label="Price",
            hint_text="Enter price",
            width=400,
            input_filter=ft.NumbersOnlyInputFilter()
        )
        self.quantity_field = ft.TextField(
            label="Quantity",
            hint_text="Enter quantity",
            width=400,
            input_filter=ft.NumbersOnlyInputFilter()
        )
        
        # Search field
        self.search_field = ft.TextField(
            label="Search Products",
            hint_text="Search by name or category",
            width=400,
            on_change=self.search_products
        )
        
        # Buttons
        self.submit_button = ft.ElevatedButton(
            "Add Product",
            icon=ft.Icons.ADD,
            on_click=self.add_product
        )
        self.update_button = ft.ElevatedButton(
            "Update Product",
            icon=ft.Icons.EDIT,
            on_click=self.update_product,
            visible=False
        )
        self.cancel_button = ft.ElevatedButton(
            "Cancel",
            icon=ft.Icons.CANCEL,
            on_click=self.cancel_edit,
            visible=False
        )
        
        # Data table
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("Category")),
                ft.DataColumn(ft.Text("Price")),
                ft.DataColumn(ft.Text("Quantity")),
                ft.DataColumn(ft.Text("Created Date")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=[],
        )
        
        # Layout
        form = ft.Column([
            ft.Text("Product Form", size=24, weight=ft.FontWeight.BOLD),
            self.name_field,
            self.category_field,
            self.price_field,
            self.quantity_field,
            ft.Row([self.submit_button, self.update_button, self.cancel_button])
        ])
        
        search_section = ft.Column([
            ft.Text("Search Products", size=20, weight=ft.FontWeight.BOLD),
            self.search_field
        ])
        
        data_section = ft.Column([
            ft.Text("Product List", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=self.data_table,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=10,
                padding=10,
            )
        ])
        
        page.add(
            form,
            ft.Divider(),
            search_section,
            data_section
        )
        
        self.load_products()
    
    def load_products(self, products=None):
        if products is None:
            products = self.db.read_products()
        
        self.data_table.rows.clear()
        
        for product in products:
            row = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(product[0]))),
                    ft.DataCell(ft.Text(product[1])),
                    ft.DataCell(ft.Text(product[2])),
                    ft.DataCell(ft.Text(f"${product[3]:.2f}")),
                    ft.DataCell(ft.Text(str(product[4]))),
                    ft.DataCell(ft.Text(product[5])),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(
                                
                                tooltip="Edit",
                                on_click=lambda e, pid=product[0]: self.edit_product(pid)
                            ),
                            ft.IconButton(
                                
                                tooltip="Delete",
                                on_click=lambda e, pid=product[0]: self.delete_product(pid)
                            ),
                        ], tight=True)
                    ),
                ]
            )
            self.data_table.rows.append(row)
        
        self.data_table.update()
        if self.page:
            self.page.update()
    
    def add_product(self, e):
        if not self.validate_form():
            return
        
        try:
            # Check if all fields have values
            if (self.name_field.value and self.category_field.value and 
                self.price_field.value and self.quantity_field.value):
                
                self.db.create_product(
                    self.name_field.value.strip(),
                    self.category_field.value.strip(),
                    float(self.price_field.value),
                    int(self.quantity_field.value)
                )
                self.clear_form()
                self.load_products()  # Refresh the table
                self.show_snackbar("✅ Product added successfully!", ft.colors.GREEN)
            else:
                self.show_snackbar("⚠️ Please fill all fields!", ft.colors.ORANGE)
                
        except ValueError as ve:
            self.show_snackbar(f"❌ Invalid number format: {str(ve)}", ft.colors.RED)
        except Exception as ex:
            self.show_snackbar(f"❌ Error adding product: {str(ex)}", ft.colors.RED)
    
    def edit_product(self, product_id):
        try:
            products = self.db.read_products()
            product = next((p for p in products if p[0] == product_id), None)
            
            if product:
                self.current_edit_id = product_id
                self.name_field.value = product[1]
                self.category_field.value = product[2]
                self.price_field.value = str(product[3])
                self.quantity_field.value = str(product[4])
                
                self.submit_button.visible = False
                self.update_button.visible = True
                self.cancel_button.visible = True
                
                self.update_ui()
                self.show_snackbar(f"✏️ Editing product: {product[1]}", ft.colors.BLUE)
        except Exception as ex:
            self.show_snackbar(f"❌ Error loading product: {str(ex)}", ft.colors.RED)
    
    def update_product(self, e):
        if not self.validate_form():
            return
        
        try:
            if self.current_edit_id:
                rows_affected = self.db.update_product(
                    self.current_edit_id,
                    self.name_field.value.strip(),
                    self.category_field.value.strip(),
                    float(self.price_field.value),
                    int(self.quantity_field.value)
                )
                
                if rows_affected > 0:
                    self.cancel_edit(e)
                    self.load_products()  # Refresh the table
                    self.show_snackbar("✅ Product updated successfully!", ft.colors.GREEN)
                else:
                    self.show_snackbar("❌ Product not found!", ft.colors.RED)
        except Exception as ex:
            self.show_snackbar(f"❌ Error updating product: {str(ex)}", ft.colors.RED)
    
    def delete_product(self, product_id):
        def confirm_delete(e):
            try:
                rows_affected = self.db.delete_product(product_id)
                if rows_affected > 0:
                    self.load_products()  # Refresh the table
                    self.show_snackbar("✅ Product deleted successfully!", ft.colors.GREEN)
                else:
                    self.show_snackbar("❌ Product not found!", ft.colors.RED)
            except Exception as ex:
                self.show_snackbar(f"❌ Error deleting product: {str(ex)}", ft.colors.RED)
            finally:
                self.page.dialog.open = False
                self.page.update()
        
        def cancel_delete(e):
            self.page.dialog.open = False
            self.page.update()
        
        # Create confirmation dialog
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Delete"),
            content=ft.Text("Are you sure you want to delete this product? This action cannot be undone."),
            actions=[
                ft.TextButton("Yes", on_click=confirm_delete),
                ft.TextButton("No", on_click=cancel_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def cancel_edit(self, e):
        self.clear_form()
        self.current_edit_id = None
        self.submit_button.visible = True
        self.update_button.visible = False
        self.cancel_button.visible = False
        self.update_ui()
    
    def search_products(self, e):
        search_term = self.search_field.value.strip()
        if search_term:
            products = self.db.search_products(search_term)
            self.load_products(products)
            self.show_snackbar(f"🔍 Found {len(products)} products", ft.colors.BLUE)
        else:
            self.load_products()
    
    def clear_form(self):
        self.name_field.value = ""
        self.category_field.value = ""
        self.price_field.value = ""
        self.quantity_field.value = ""
        self.update_ui()
    
    def update_ui(self):
        """Update all UI components"""
        self.name_field.update()
        self.category_field.update()
        self.price_field.update()
        self.quantity_field.update()
        self.submit_button.update()
        self.update_button.update()
        self.cancel_button.update()
        if self.page:
            self.page.update()
    
    def validate_form(self):
        if not self.name_field.value or not self.name_field.value.strip():
            self.show_snackbar("⚠️ Please enter product name", ft.colors.ORANGE)
            self.name_field.focus()
            return False
        if not self.category_field.value or not self.category_field.value.strip():
            self.show_snackbar("⚠️ Please enter category", ft.colors.ORANGE)
            self.category_field.focus()
            return False
        try:
            price = float(self.price_field.value)
            if price <= 0:
                self.show_snackbar("⚠️ Price must be greater than 0", ft.colors.ORANGE)
                self.price_field.focus()
                return False
        except (ValueError, TypeError):
            self.show_snackbar("⚠️ Please enter valid price", ft.colors.ORANGE)
            self.price_field.focus()
            return False
        try:
            quantity = int(self.quantity_field.value)
            if quantity < 0:
                self.show_snackbar("⚠️ Quantity cannot be negative", ft.colors.ORANGE)
                self.quantity_field.focus()
                return False
        except (ValueError, TypeError):
            self.show_snackbar("⚠️ Please enter valid quantity", ft.colors.ORANGE)
            self.quantity_field.focus()
            return False
        return True
    
    def show_snackbar(self, message, color):
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=color,
                duration=3000
            )
            self.page.snack_bar.open = True
            self.page.update()

def main(page: ft.Page):
    app = ProductManagerApp()
    app.main(page)

if __name__ == "__main__":
            port = int(os.getenv("PORT", 8502))
            ft.app(target=main, view=ft.WEB_BROWSER, port=port)
