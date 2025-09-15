# Expense Tracker Dashboard (Streamlit)
# Description: Web app for tracking and analyzing expenses with advanced filtering, dashboard KPIs, outlier detection, reports, charts, and import/export.

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
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

def get_all_expenses():
    """Return all expenses as a pandas DataFrame."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query('SELECT * FROM expenses ORDER BY date DESC', conn)
    conn.close()
    return df

def get_all_categories():
    """Return a list of all unique categories in the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT DISTINCT category FROM expenses')
    cats = [row[0] for row in c.fetchall()]
    conn.close()
    return cats

# =========================
# Helper Functions
# =========================
def filter_expenses(df, start_date, end_date, category, min_amount, max_amount, desc_keyword):
    """Filter the DataFrame by the given criteria."""
    if start_date:
        df = df[df['date'] >= start_date]
    if end_date:
        df = df[df['date'] <= end_date]
    if category and category != 'All':
        df = df[df['category'] == category]
    if min_amount is not None:
        df = df[df['amount'] >= min_amount]
    if max_amount is not None:
        df = df[df['amount'] <= max_amount]
    if desc_keyword:
        df = df[df['description'].str.contains(desc_keyword, case=False, na=False)]
    return df

def get_stats(df):
    """Calculate statistics (KPIs) for a DataFrame of expenses."""
    if df.empty:
        return {}
    stats = {
        'total': float(df['amount'].sum()),
        'average': float(df['amount'].mean()),
        'median': float(df['amount'].median()),
        'min': float(df['amount'].min()),
        'max': float(df['amount'].max()),
        'std': float(df['amount'].std()),
        'var': float(df['amount'].var()),
        'most_freq_cat': df['category'].mode()[0] if not df['category'].mode().empty else None
    }
    return stats

def detect_outliers(df):
    """Detect outlier expenses using mean ± 2*std deviation."""
    if df.empty:
        return set()
    mean = df['amount'].mean()
    std = df['amount'].std()
    outliers = df[(df['amount'] > mean + 2*std) | (df['amount'] < mean - 2*std)]
    return set(outliers['id'])

# =========================
# Streamlit App
# =========================
st.set_page_config(page_title='Expense Tracker Dashboard', layout='wide')
init_db()
st.title('Expense Tracker Dashboard')

# --- Sidebar: Add/Edit Expense ---
st.sidebar.header('Add/Edit Expense')
with st.sidebar.form(key='expense_form', clear_on_submit=True):
    edit_id = st.session_state.get('edit_id', None)
    amount = st.number_input('Amount', min_value=0.0, format="%.2f", value=0.0)
    category = st.text_input('Category')
    date = st.date_input('Date', value=datetime.now())
    description = st.text_input('Description')
    submit = st.form_submit_button('Save' if edit_id else 'Add')
    if submit:
        if not category:
            st.warning('Category required!')
        else:
            if edit_id:
                update_expense(edit_id, amount, category, date.strftime('%Y-%m-%d'), description)
                st.session_state['edit_id'] = None
                st.success('Expense updated!')
            else:
                add_expense(amount, category, date.strftime('%Y-%m-%d'), description)
                st.success('Expense added!')

# --- Main Panel: Filters ---
df = get_all_expenses()
df['date'] = pd.to_datetime(df['date'])

with st.expander('Filter/Search', expanded=True):
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        start_date = st.date_input('Start Date', value=None, key='start_date')
    with col2:
        end_date = st.date_input('End Date', value=None, key='end_date')
    with col3:
        cats = ['All'] + get_all_categories()
        category = st.selectbox('Category', cats, key='category_filter')
    with col4:
        min_amount = st.number_input('Min Amount', min_value=0.0, value=0.0, key='min_amount')
    with col5:
        max_amount = st.number_input('Max Amount', min_value=0.0, value=0.0, key='max_amount')
    with col6:
        desc_keyword = st.text_input('Description Keyword', key='desc_keyword')
    # Convert None to string for filtering
    start_date = start_date.strftime('%Y-%m-%d') if start_date else None
    end_date = end_date.strftime('%Y-%m-%d') if end_date else None
    min_amount = min_amount if min_amount > 0 else None
    max_amount = max_amount if max_amount > 0 else None
    filtered_df = filter_expenses(df, start_date, end_date, category, min_amount, max_amount, desc_keyword)

# --- Dashboard KPIs ---
st.subheader('Dashboard Summary')
stats = get_stats(filtered_df)
kpi1, kpi2, kpi3, kpi4, kpi5, kpi6, kpi7, kpi8 = st.columns(8)
kpi1.metric('Total', f"${stats.get('total', 0):.2f}")
kpi2.metric('Average', f"${stats.get('average', 0):.2f}")
kpi3.metric('Median', f"${stats.get('median', 0):.2f}")
kpi4.metric('Min', f"${stats.get('min', 0):.2f}")
kpi5.metric('Max', f"${stats.get('max', 0):.2f}")
kpi6.metric('Std', f"${stats.get('std', 0):.2f}")
kpi7.metric('Variance', f"${stats.get('var', 0):.2f}")
kpi8.metric('Most Freq. Cat', stats.get('most_freq_cat', '-'))

# --- Table with Edit/Delete ---
st.subheader('Expenses Table')
outlier_ids = detect_outliers(filtered_df)
def highlight_outliers(row):
    color = 'background-color: #ffcccc' if row['id'] in outlier_ids else ''
    return [color]*len(row)
st.dataframe(filtered_df.style.apply(highlight_outliers, axis=1), use_container_width=True)

# --- Edit/Delete actions ---
if not filtered_df.empty:
    st.write('Select a row to edit or delete:')
    selected = st.selectbox('Select Expense ID', filtered_df['id'])
    colA, colB = st.columns(2)
    with colA:
        if st.button('Edit Selected'):
            row = filtered_df[filtered_df['id'] == selected].iloc[0]
            st.session_state['edit_id'] = row['id']
            st.sidebar.warning('Edit mode: update and save in sidebar.')
    with colB:
        if st.button('Delete Selected'):
            delete_expense(selected)
            st.success('Expense deleted!')
            st.experimental_rerun()

# --- Import/Export ---
st.subheader('Import/Export')
colE, colF = st.columns(2)
with colE:
    uploaded = st.file_uploader('Import CSV/Excel', type=['csv', 'xlsx'])
    if uploaded is not None:
        try:
            if uploaded.name.endswith('.csv'):
                import_df = pd.read_csv(uploaded)
            else:
                import_df = pd.read_excel(uploaded)
            for _, row in import_df.iterrows():
                add_expense(float(row['Amount']), str(row['Category']), str(row['Date']), str(row.get('Description', '')))
            st.success(f'Imported {len(import_df)} expenses!')
            st.experimental_rerun()
        except Exception as e:
            st.error(f'Import failed: {e}')
with colF:
    export_type = st.selectbox('Export Format', ['CSV', 'Excel'])
    if st.button('Export Filtered'):
        export_df = filtered_df.copy()
        export_df.columns = ['ID', 'Amount', 'Category', 'Date', 'Description']
        if export_type == 'CSV':
            st.download_button('Download CSV', export_df.to_csv(index=False), file_name='expenses.csv', mime='text/csv')
        else:
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                export_df.to_excel(writer, index=False)
            st.download_button('Download Excel', output.getvalue(), file_name='expenses.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# --- Reports ---
st.subheader('Custom Reports & Charts')
report_type = st.selectbox('Report Type', ['None', 'Weekly', 'Monthly', 'Quarterly', 'Yearly'])
if report_type != 'None' and not filtered_df.empty:
    df_rep = filtered_df.copy()
    df_rep['Date'] = pd.to_datetime(df_rep['date'])
    if report_type == 'Weekly':
        grp = df_rep.groupby(df_rep['Date'].dt.to_period('W'))['amount'].sum()
        title = 'Weekly Report'
    elif report_type == 'Monthly':
        grp = df_rep.groupby(df_rep['Date'].dt.to_period('M'))['amount'].sum()
        title = 'Monthly Report'
    elif report_type == 'Quarterly':
        grp = df_rep.groupby(df_rep['Date'].dt.to_period('Q'))['amount'].sum()
        title = 'Quarterly Report'
    else:
        grp = df_rep.groupby(df_rep['Date'].dt.to_period('Y'))['amount'].sum()
        title = 'Yearly Report'
    st.bar_chart(grp)
    st.write(title)

# --- Interactive Charts ---
if st.button('Show Interactive Charts') and not filtered_df.empty:
    dfc = filtered_df.copy()
    dfc['Date'] = pd.to_datetime(dfc['date'])
    fig, axs = plt.subplots(1, 3, figsize=(15, 5))
    # Pie chart: category breakdown
    cat_sum = dfc.groupby('category')['amount'].sum()
    axs[0].pie(cat_sum, labels=cat_sum.index, autopct='%1.1f%%')
    axs[0].set_title('Category Breakdown')
    # Bar chart: monthly trend
    month_sum = dfc.groupby(dfc['Date'].dt.to_period('M'))['amount'].sum()
    axs[1].bar(month_sum.index.astype(str), month_sum.values)
    axs[1].set_title('Monthly Trend')
    axs[1].set_xticklabels(month_sum.index.astype(str), rotation=45)
    # Outlier scatter
    axs[2].scatter(dfc['Date'], dfc['amount'], c=['red' if rid in outlier_ids else 'blue' for rid in dfc['id']])
    axs[2].set_title('Outlier Detection')
    axs[2].set_xlabel('Date')
    axs[2].set_ylabel('Amount')
    plt.tight_layout()
    st.pyplot(fig) 
