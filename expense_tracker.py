# Expense Tracker Application (Tkinter)
# Description: Desktop app for tracking and analyzing expenses with advanced filtering, dashboard KPIs, outlier detection, reports, charts, and import/export.

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import openpyxl

DB_NAME = 'expenses.db'

# =========================
# Database Functions
# =========================
def init_db():
    """Initialize the SQLite database and create the expenses table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_expense(amount, category, date, description):
    """Insert a new expense record into the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO expenses (amount, category, date, description) VALUES (?, ?, ?, ?)',
              (amount, category, date, description))
    conn.commit()
    conn.close()

def get_all_categories():
    """Return a list of all unique categories in the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT DISTINCT category FROM expenses')
    cats = [row[0] for row in c.fetchall()]
    conn.close()
    return cats

def get_filtered_expenses(start_date=None, end_date=None, category=None, min_amount=None, max_amount=None, desc_keyword=None):
    """Return expenses filtered by the given criteria."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    query = 'SELECT id, amount, category, date, description FROM expenses WHERE 1=1'
    params = []
    if start_date:
        query += ' AND date >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND date <= ?'
        params.append(end_date)
    if category and category != 'All':
        query += ' AND category = ?'
        params.append(category)
    if min_amount is not None:
        query += ' AND amount >= ?'
        params.append(min_amount)
    if max_amount is not None:
        query += ' AND amount <= ?'
        params.append(max_amount)
    if desc_keyword:
        query += ' AND description LIKE ?'
        params.append(f'%{desc_keyword}%')
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

def update_expense(expense_id, amount, category, date, description):
    """Update an existing expense record."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE expenses SET amount=?, category=?, date=?, description=? WHERE id=?',
              (amount, category, date, description, expense_id))
    conn.commit()
    conn.close()

def delete_expense(expense_id):
    """Delete an expense record by ID."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM expenses WHERE id=?', (expense_id,))
    conn.commit()
    conn.close()

# =========================
# Analysis & Utility Functions
# =========================
def get_stats(expenses):
    """Calculate statistics (KPIs) for a list of expenses."""
    if not expenses:
        return {}
    amounts = np.array([row[1] for row in expenses])
    stats = {
        'total': float(np.sum(amounts)),
        'average': float(np.mean(amounts)),
        'median': float(np.median(amounts)),
        'min': float(np.min(amounts)),
        'max': float(np.max(amounts)),
        'std': float(np.std(amounts)),
        'var': float(np.var(amounts)),
    }
    cats = [row[2] for row in expenses]
    stats['most_freq_cat'] = max(set(cats), key=cats.count) if cats else None
    return stats

def detect_outliers(expenses):
    """Detect outlier expenses using mean ± 2*std deviation."""
    if not expenses:
        return set()
    amounts = np.array([row[1] for row in expenses])
    mean = np.mean(amounts)
    std = np.std(amounts)
    outlier_ids = set()
    for row in expenses:
        if abs(row[1] - mean) > 2 * std:
            outlier_ids.add(row[0])
    return outlier_ids

# =========================
# Main Application Class
# =========================
class ExpenseTracker(tk.Tk):
    """Tkinter GUI for the Expense Tracker application."""
    def __init__(self):
        super().__init__()
        self.title('Expense Tracker')
        self.geometry('950x700')
        self.resizable(True, True)
        self.selected_item_id = None
        self.edit_mode = False
        self.filter_vars = {}
        self.filtered_expenses = []
        self.outlier_ids = set()
        self.create_widgets()
        self.refresh_filters()
        self.refresh_expenses()
        self.refresh_dashboard()

    def create_widgets(self):
        """Create and layout all widgets in the GUI."""
        # --- Filter/Search Panel ---
        filter_frame = ttk.LabelFrame(self, text='Filter/Search')
        filter_frame.pack(fill='x', padx=10, pady=5)
        # Date range filter
        ttk.Label(filter_frame, text='Start Date:').grid(row=0, column=0, padx=2, pady=2)
        self.filter_vars['start_date'] = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.filter_vars['start_date'], width=12).grid(row=0, column=1, padx=2)
        ttk.Label(filter_frame, text='End Date:').grid(row=0, column=2, padx=2)
        self.filter_vars['end_date'] = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.filter_vars['end_date'], width=12).grid(row=0, column=3, padx=2)
        # Category filter
        ttk.Label(filter_frame, text='Category:').grid(row=0, column=4, padx=2)
        self.filter_vars['category'] = tk.StringVar(value='All')
        self.cat_combo = ttk.Combobox(filter_frame, textvariable=self.filter_vars['category'], width=12, state='readonly')
        self.cat_combo.grid(row=0, column=5, padx=2)
        # Amount filter
        ttk.Label(filter_frame, text='Min Amount:').grid(row=0, column=6, padx=2)
        self.filter_vars['min_amount'] = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.filter_vars['min_amount'], width=8).grid(row=0, column=7, padx=2)
        ttk.Label(filter_frame, text='Max Amount:').grid(row=0, column=8, padx=2)
        self.filter_vars['max_amount'] = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.filter_vars['max_amount'], width=8).grid(row=0, column=9, padx=2)
        # Description filter
        ttk.Label(filter_frame, text='Description:').grid(row=0, column=10, padx=2)
        self.filter_vars['desc_keyword'] = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.filter_vars['desc_keyword'], width=15).grid(row=0, column=11, padx=2)
        # Filter/Reset buttons
        ttk.Button(filter_frame, text='Filter', command=self.apply_filters).grid(row=0, column=12, padx=5)
        ttk.Button(filter_frame, text='Reset', command=self.reset_filters).grid(row=0, column=13, padx=2)

        # --- Dashboard Summary ---
        dash_frame = ttk.LabelFrame(self, text='Dashboard Summary')
        dash_frame.pack(fill='x', padx=10, pady=5)
        self.kpi_labels = {}
        kpi_names = ['Total', 'Average', 'Median', 'Min', 'Max', 'Std', 'Variance', 'Most Frequent Category']
        for i, name in enumerate(kpi_names):
            lbl = ttk.Label(dash_frame, text=f'{name}: -', width=25)
            lbl.grid(row=0, column=i, padx=2, pady=2)
            self.kpi_labels[name] = lbl

        # --- Add/Edit Expense Panel ---
        add_frame = ttk.LabelFrame(self, text='Add/Edit Expense')
        add_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(add_frame, text='Amount:').grid(row=0, column=0, padx=5, pady=5)
        self.amount_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.amount_var, width=10).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(add_frame, text='Category:').grid(row=0, column=2, padx=5, pady=5)
        self.category_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.category_var, width=15).grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(add_frame, text='Date (YYYY-MM-DD):').grid(row=0, column=4, padx=5, pady=5)
        self.date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ttk.Entry(add_frame, textvariable=self.date_var, width=12).grid(row=0, column=5, padx=5, pady=5)
        ttk.Label(add_frame, text='Description:').grid(row=0, column=6, padx=5, pady=5)
        self.desc_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.desc_var, width=20).grid(row=0, column=7, padx=5, pady=5)
        self.add_btn = ttk.Button(add_frame, text='Add', command=self.handle_add, width=8)
        self.add_btn.grid(row=1, column=0, columnspan=1, padx=5, pady=5)

        # --- Expenses Table ---
        table_frame = ttk.LabelFrame(self, text='Expenses')
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)
        columns = ('id', 'amount', 'category', 'date', 'description')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=12)
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=60 if col == 'id' else (100 if col != 'description' else 200))
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        btn_frame = tk.Frame(table_frame)
        btn_frame.pack(fill='x', pady=2)
        ttk.Button(btn_frame, text='Edit', command=self.start_edit).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='Delete', command=self.delete_expense).pack(side='left', padx=5)

        # --- Report/Chart/Import/Export Buttons ---
        action_frame = tk.Frame(self)
        action_frame.pack(fill='x', pady=2)
        ttk.Button(action_frame, text='Export Filtered CSV', command=self.export_csv).pack(side='left', padx=5)
        ttk.Button(action_frame, text='Export Filtered Excel', command=self.export_excel).pack(side='left', padx=5)
        ttk.Button(action_frame, text='Import CSV/Excel', command=self.import_data).pack(side='left', padx=5)
        ttk.Button(action_frame, text='Show Charts', command=self.show_charts).pack(side='left', padx=5)
        ttk.Button(action_frame, text='Weekly Report', command=lambda: self.report_period('W')).pack(side='left', padx=5)
        ttk.Button(action_frame, text='Monthly Report', command=lambda: self.report_period('M')).pack(side='left', padx=5)
        ttk.Button(action_frame, text='Quarterly Report', command=lambda: self.report_period('Q')).pack(side='left', padx=5)
        ttk.Button(action_frame, text='Yearly Report', command=lambda: self.report_period('Y')).pack(side='left', padx=5)

    # =========================
    # Filtering/Search Methods
    # =========================
    def refresh_filters(self):
        """Refresh the category filter dropdown with current categories."""
        cats = get_all_categories()
        self.cat_combo['values'] = ['All'] + cats
        self.cat_combo.set('All')

    def apply_filters(self):
        """Apply filters and update the table and dashboard."""
        self.refresh_expenses()
        self.refresh_dashboard()

    def reset_filters(self):
        """Reset all filters to default values."""
        for var in self.filter_vars.values():
            var.set('')
        self.cat_combo.set('All')
        self.refresh_expenses()
        self.refresh_dashboard()

    # =========================
    # Add/Edit/Delete Methods
    # =========================
    def handle_add(self):
        """Add a new expense or update an existing one."""
        try:
            amount = float(self.amount_var.get())
            category = self.category_var.get().strip()
            date = self.date_var.get().strip()
            description = self.desc_var.get().strip()
            datetime.strptime(date, '%Y-%m-%d')
            if not category:
                raise ValueError('Category required')
            if self.edit_mode and self.selected_item_id:
                update_expense(self.selected_item_id, amount, category, date, description)
                self.add_btn.config(text='Add')
                self.edit_mode = False
                self.selected_item_id = None
            else:
                add_expense(amount, category, date, description)
            self.amount_var.set('')
            self.category_var.set('')
            self.desc_var.set('')
            self.date_var.set(datetime.now().strftime('%Y-%m-%d'))
            self.refresh_filters()
            self.refresh_expenses()
            self.refresh_dashboard()
        except Exception as e:
            messagebox.showerror('Error', f'Failed to add/edit expense: {e}')

    def on_tree_select(self, event):
        """Handle row selection in the expenses table."""
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            self.selected_item_id = item['values'][0]
        else:
            self.selected_item_id = None

    def start_edit(self):
        """Load selected expense into the form for editing."""
        if not self.selected_item_id:
            messagebox.showwarning('Select', 'Select an expense to edit.')
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT amount, category, date, description FROM expenses WHERE id=?', (self.selected_item_id,))
        row = c.fetchone()
        conn.close()
        if row:
            self.amount_var.set(row[0])
            self.category_var.set(row[1])
            self.date_var.set(row[2])
            self.desc_var.set(row[3])
            self.add_btn.config(text='Save')
            self.edit_mode = True

    def delete_expense(self):
        """Delete the selected expense."""
        if not self.selected_item_id:
            messagebox.showwarning('Select', 'Select an expense to delete.')
            return
        if messagebox.askyesno('Delete', 'Are you sure you want to delete this expense?'):
            delete_expense(self.selected_item_id)
            self.selected_item_id = None
            self.refresh_expenses()
            self.refresh_dashboard()

    # =========================
    # Table/Outlier Highlighting
    # =========================
    def refresh_expenses(self):
        """Refresh the expenses table based on current filters."""
        # Get filter values
        start_date = self.filter_vars['start_date'].get() or None
        end_date = self.filter_vars['end_date'].get() or None
        category = self.filter_vars['category'].get() or None
        min_amount = self.filter_vars['min_amount'].get()
        max_amount = self.filter_vars['max_amount'].get()
        desc_keyword = self.filter_vars['desc_keyword'].get() or None
        min_amount = float(min_amount) if min_amount else None
        max_amount = float(max_amount) if max_amount else None
        expenses = get_filtered_expenses(start_date, end_date, category, min_amount, max_amount, desc_keyword)
        self.filtered_expenses = expenses
        self.outlier_ids = detect_outliers(expenses)
        for row in self.tree.get_children():
            self.tree.delete(row)
        for exp in expenses:
            tag = 'outlier' if exp[0] in self.outlier_ids else ''
            self.tree.insert('', 'end', values=exp, tags=(tag,))
        self.tree.tag_configure('outlier', background='#ffcccc')

    # =========================
    # Dashboard Summary/Stats
    # =========================
    def refresh_dashboard(self):
        """Update the dashboard KPIs based on filtered expenses."""
        stats = get_stats(self.filtered_expenses)
        kpi_map = {
            'Total': 'total',
            'Average': 'average',
            'Median': 'median',
            'Min': 'min',
            'Max': 'max',
            'Std': 'std',
            'Variance': 'var',
            'Most Frequent Category': 'most_freq_cat',
        }
        for kpi, key in kpi_map.items():
            val = stats.get(key, '-')
            if isinstance(val, float):
                val = f'${val:.2f}'
            self.kpi_labels[kpi].config(text=f'{kpi}: {val}')

    # =========================
    # Export/Import/Reports
    # =========================
    def export_csv(self):
        """Export filtered expenses to a CSV file."""
        df = pd.DataFrame(self.filtered_expenses, columns=['ID', 'Amount', 'Category', 'Date', 'Description'])
        file = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files', '*.csv')])
        if file:
            df.to_csv(file, index=False)
            messagebox.showinfo('Exported', f'Filtered expenses exported to {file}')

    def export_excel(self):
        """Export filtered expenses to an Excel file."""
        df = pd.DataFrame(self.filtered_expenses, columns=['ID', 'Amount', 'Category', 'Date', 'Description'])
        file = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel files', '*.xlsx')])
        if file:
            df.to_excel(file, index=False)
            messagebox.showinfo('Exported', f'Filtered expenses exported to {file}')

    def import_data(self):
        """Import expenses from a CSV or Excel file."""
        file = filedialog.askopenfilename(filetypes=[('CSV/Excel files', '*.csv *.xlsx')])
        if not file:
            return
        try:
            if file.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            for _, row in df.iterrows():
                amount = float(row['Amount'])
                category = str(row['Category'])
                date = str(row['Date'])
                description = str(row.get('Description', ''))
                add_expense(amount, category, date, description)
            self.refresh_filters()
            self.refresh_expenses()
            self.refresh_dashboard()
            messagebox.showinfo('Imported', f'Imported {len(df)} expenses.')
        except Exception as e:
            messagebox.showerror('Import Error', f'Failed to import: {e}')

    def report_period(self, period):
        """Generate and display a report for the selected period (W/M/Q/Y)."""
        df = pd.DataFrame(self.filtered_expenses, columns=['ID', 'Amount', 'Category', 'Date', 'Description'])
        if df.empty:
            messagebox.showinfo('No Data', 'No expenses to report.')
            return
        df['Date'] = pd.to_datetime(df['Date'])
        if period == 'W':
            grp = df.groupby(df['Date'].dt.to_period('W'))['Amount'].sum()
            title = 'Weekly Report'
        elif period == 'M':
            grp = df.groupby(df['Date'].dt.to_period('M'))['Amount'].sum()
            title = 'Monthly Report'
        elif period == 'Q':
            grp = df.groupby(df['Date'].dt.to_period('Q'))['Amount'].sum()
            title = 'Quarterly Report'
        else:
            grp = df.groupby(df['Date'].dt.to_period('Y'))['Amount'].sum()
            title = 'Yearly Report'
        plt.figure(figsize=(8, 4))
        grp.plot(kind='bar')
        plt.title(title)
        plt.ylabel('Total Amount')
        plt.xlabel('Period')
        plt.tight_layout()
        plt.show()

    # =========================
    # Charts/Drilldown/Outlier
    # =========================
    def show_charts(self):
        """Display interactive charts for category breakdown, monthly trend, and outlier detection."""
        df = pd.DataFrame(self.filtered_expenses, columns=['ID', 'Amount', 'Category', 'Date', 'Description'])
        if df.empty:
            messagebox.showinfo('No Data', 'No expenses to chart.')
            return
        df['Date'] = pd.to_datetime(df['Date'])
        plt.figure(figsize=(12, 5))
        # Pie chart: category breakdown
        plt.subplot(1, 3, 1)
        cat_sum = df.groupby('Category')['Amount'].sum()
        cat_sum.plot(kind='pie', autopct='%1.1f%%')
        plt.title('Category Breakdown')
        plt.ylabel('')
        # Bar chart: monthly trend
        plt.subplot(1, 3, 2)
        month_sum = df.groupby(df['Date'].dt.to_period('M'))['Amount'].sum()
        month_sum.plot(kind='bar')
        plt.title('Monthly Trend')
        plt.xlabel('Month')
        # Outlier detection: scatter
        plt.subplot(1, 3, 3)
        plt.scatter(df['Date'], df['Amount'], c=['red' if row['ID'] in self.outlier_ids else 'blue' for _, row in df.iterrows()])
        plt.title('Outlier Detection')
        plt.xlabel('Date')
        plt.ylabel('Amount')
        plt.tight_layout()
        plt.show()

if __name__ == '__main__':
    init_db()
    app = ExpenseTracker()
    app.mainloop() 
