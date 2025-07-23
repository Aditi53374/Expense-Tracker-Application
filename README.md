# Expense Tracker Application

This project provides two powerful expense tracker applications:
- **Desktop App (Tkinter)**
- **Web Dashboard (Streamlit)**

Both apps use a shared SQLite database (`expenses.db`) and offer advanced analytics, reporting, and visualization features.

---

## Features
- Add, edit, and delete expenses
- Advanced filtering (date range, category, amount, description)
- Dashboard KPIs (total, average, median, min, max, std, variance, most frequent category)
- Outlier/anomaly detection and highlighting
- Custom reports (weekly, monthly, quarterly, yearly)
- Interactive charts (category breakdown, time series, outlier detection)
- Data import/export (CSV/Excel)

---

## Setup

1. **Clone or download this repository.**
2. **Install dependencies:**
   ```bash
   pip install pandas matplotlib openpyxl numpy streamlit
   ```

---

## Usage

### Desktop App (Tkinter)
- Run:
  ```bash
  python Project2/expense_tracker.py
  ```
- Use the GUI to add, filter, analyze, and export expenses.

### Web Dashboard (Streamlit)
- Run:
  ```bash
  streamlit run Project2/expense_tracker_streamlit.py
  ```
- The app will open in your browser. Use the sidebar and dashboard for all features.

---

## Notes
- Both apps use the same `expenses.db` database file, so your data is shared.
- For any issues or feature requests, please contact the author or open an issue. 