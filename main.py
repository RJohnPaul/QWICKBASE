import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from ttkthemes import ThemedTk
import sqlite3
import random

class Stock:
    def __init__(self, symbol, price):
        self.symbol = symbol
        self.price = price

class Portfolio:
    def __init__(self, balance=10000):
        self.balance = balance
        self.stocks = {}
        self.conn = sqlite3.connect("portfolio.db")
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY,
                symbol TEXT UNIQUE,
                price REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                symbol TEXT,
                quantity INTEGER,
                action TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def buy_stock(self, stock, quantity):
        cost = stock.price * quantity
        if cost > self.balance:
            messagebox.showerror("Error", "Insufficient funds to buy {} shares of {}.".format(quantity, stock.symbol))
        else:
            self.balance -= cost
            if stock.symbol in self.stocks:
                self.stocks[stock.symbol] += quantity
            else:
                self.stocks[stock.symbol] = quantity
            self.record_transaction(stock.symbol, quantity, 'BUY')
            self.update_stock_prices([stock])  # Update stock prices after buying

    def sell_stock(self, stock, quantity):
        if stock.symbol not in self.stocks or self.stocks[stock.symbol] < quantity:
            messagebox.showerror("Error", "Not enough shares of {} to sell.".format(stock.symbol))
        else:
            earnings = stock.price * quantity
            self.balance += earnings
            self.stocks[stock.symbol] -= quantity
            self.record_transaction(stock.symbol, quantity, 'SELL')
            self.update_stock_prices([stock])  # Update stock prices after selling

    def record_transaction(self, symbol, quantity, action):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO transactions (symbol, quantity, action) VALUES (?, ?, ?)",
                       (symbol, quantity, action))
        self.conn.commit()

    def update_stock_prices(self, stocks):
        cursor = self.conn.cursor()
        for stock in stocks:
            price_change = random.uniform(-5, 5)
            stock.price *= (1 + price_change / 100)
            cursor.execute("INSERT OR REPLACE INTO stocks (symbol, price) VALUES (?, ?)",
                           (stock.symbol, stock.price))
        self.conn.commit()

    def get_portfolio_data(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM stocks")
        stocks_data = cursor.fetchall()
        return stocks_data

class StockTradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stock Trading Simulator")
        self.root.geometry("800x600")
        self.style = ttk.Style(self.root)
        self.style.theme_use("equilux")  # Set ttk theme (use 'equilux' for vibrant colors)

        self.stocks = [Stock("AAPL", 150), Stock("GOOGL", 2500), Stock("MSFT", 300)]
        self.portfolio = Portfolio()

        self.create_widgets()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        self.portfolio_frame = ttk.Frame(self.notebook)
        self.buy_sell_frame = ttk.Frame(self.notebook)
        self.history_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.portfolio_frame, text="Portfolio")
        self.notebook.add(self.buy_sell_frame, text="Buy/Sell")
        self.notebook.add(self.history_frame, text="Transaction History")

        self.create_portfolio_widgets()
        self.create_buy_sell_widgets()
        self.create_history_widgets()

    def create_portfolio_widgets(self):
        self.balance_label = ttk.Label(self.portfolio_frame, text="Balance: ${}".format(self.portfolio.balance))
        self.balance_label.pack(pady=10)

        self.portfolio_tree = ttk.Treeview(self.portfolio_frame, columns=('Symbol', 'Price', 'Quantity'))
        self.portfolio_tree.heading('#0', text='Symbol')
        self.portfolio_tree.heading('#1', text='Price')
        self.portfolio_tree.heading('#2', text='Quantity')
        self.portfolio_tree.pack(padx=10, pady=10)

        self.update_portfolio_tree()

    def create_buy_sell_widgets(self):
        ttk.Label(self.buy_sell_frame, text="Stock Symbol:").grid(row=0, column=0, padx=5, pady=5)
        self.symbol_entry = ttk.Entry(self.buy_sell_frame)
        self.symbol_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.buy_sell_frame, text="Quantity:").grid(row=1, column=0, padx=5, pady=5)
        self.quantity_entry = ttk.Entry(self.buy_sell_frame)
        self.quantity_entry.grid(row=1, column=1, padx=5, pady=5)

        self.buy_button = ttk.Button(self.buy_sell_frame, text="Buy", command=self.buy_stock)
        self.buy_button.grid(row=2, column=0, columnspan=2, pady=10)

        self.sell_button = ttk.Button(self.buy_sell_frame, text="Sell", command=self.sell_stock)
        self.sell_button.grid(row=3, column=0, columnspan=2, pady=10)

    def create_history_widgets(self):
        self.history_tree = ttk.Treeview(self.history_frame, columns=('Symbol', 'Quantity', 'Action', 'Timestamp'))
        self.history_tree.heading('#0', text='Symbol')
        self.history_tree.heading('#1', text='Quantity')
        self.history_tree.heading('#2', text='Action')
        self.history_tree.heading('#3', text='Timestamp')
        self.history_tree.pack(padx=10, pady=10)

        self.update_history_tree()

    def update_portfolio_tree(self):
        data = self.portfolio.get_portfolio_data()
        for item in self.portfolio_tree.get_children():
            self.portfolio_tree.delete(item)

        for row in data:
            self.portfolio_tree.insert('', 'end', values=row)

        self.balance_label.config(text="Balance: ${}".format(self.portfolio.balance))

    def update_history_tree(self):
        cursor = self.portfolio.conn.cursor()
        cursor.execute("SELECT * FROM transactions")
        transactions_data = cursor.fetchall()

        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        for row in transactions_data:
            self.history_tree.insert('', 'end', values=row)

    def buy_stock(self):
        symbol = self.symbol_entry.get().upper()
        stock = next((s for s in self.stocks if s.symbol == symbol), None)
        if stock:
            try:
                quantity = int(self.quantity_entry.get())
                self.portfolio.buy_stock(stock, quantity)
                self.update_portfolio_tree()
                self.update_history_tree()
                self.symbol_entry.delete(0, 'end')
                self.quantity_entry.delete(0, 'end')
            except ValueError:
                messagebox.showerror("Error", "Invalid quantity. Please enter a valid integer.")
        else:
            messagebox.showerror("Error", "Invalid stock symbol.")

    def sell_stock(self):
        symbol = self.symbol_entry.get().upper()
        stock = next((s for s in self.stocks if s.symbol == symbol), None)
        if stock:
            try:
                quantity = int(self.quantity_entry.get())
                self.portfolio.sell_stock(stock, quantity)
                self.update_portfolio_tree()
                self.update_history_tree()
                self.symbol_entry.delete(0, 'end')
                self.quantity_entry.delete(0, 'end')
            except ValueError:
                messagebox.showerror("Error", "Invalid quantity. Please enter a valid integer.")
        else:
            messagebox.showerror("Error", "Invalid stock symbol.")

if __name__ == "__main__":
    root = ThemedTk(theme="breeze")  # Set the overall theme for ThemedTk (use 'breeze' for vibrant colors)
    app = StockTradingApp(root)
    root.mainloop()
