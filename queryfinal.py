import pandas as pd
import openai
import os
from dotenv import load_dotenv
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, PhotoImage
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns

class SalesDataQueryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("C-Kore Sales Data Analyzer")
        self.root.geometry("1200x600")

        # Load environment variables and data
        load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.load_data()

        # Setup UI
        self.setup_ui()

    def load_data(self, file_path="allops.csv"):
        try:
            self.df = pd.read_csv(file_path)
            self.column_names = list(self.df.columns)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load data: {str(e)}")
            self.df = None

    def setup_ui(self):
        # Main style configuration
        style = ttk.Style(self.root)
        style.theme_use('clam')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        main_frame.pack(fill='both', expand=True)

        # Query section
        query_frame = ttk.LabelFrame(main_frame, text="Data Query", padding="10 10 10 10")
        query_frame.pack(fill='x', pady=(0, 10))

        # Query entry
        ttk.Label(query_frame, text="Enter your query:").pack(anchor='w')
        self.query_entry = ttk.Entry(query_frame, width=100, font=("Helvetica", 12))
        self.query_entry.pack(fill='x', pady=(0, 10))

        # Query buttons
        button_frame = ttk.Frame(query_frame)
        button_frame.pack(fill='x')
        
        ttk.Button(button_frame, text="Run Query", command=self.run_query).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="Quick Insights", command=self.show_quick_insights).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="Visualize Data", command=self.open_visualization_window).pack(side='left')

        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10 10 10 10")
        results_frame.pack(fill='both', expand=True)

        self.result_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, font=("Helvetica", 12), height=15)
        self.result_text.pack(fill='both', expand=True)

        # Hint text
        hint_text = (
            "💡 Query Tips:\n"
            "- 'Top 5 selling products'\n"
            "- 'Average order value'\n"
            "- 'Sales by field'"
        )
        ttk.Label(main_frame, text=hint_text, font=("Helvetica", 10), justify='left').pack(anchor='w', pady=(10, 0))

    def generate_pandas_query(self, question):
        column_info = ", ".join(f"{col} ({dtype})" for col, dtype in self.df.dtypes.items())

        prompt = f"""
        You are a data analysis assistant for a sales team. The DataFrame contains these columns and their data types: {column_info}.
        
        Your task: Generate **ONLY** a valid Pandas query to answer this question:

        "{question}"

        **Rules:**
        - Assume 'df' is the DataFrame.
        - Output **ONLY** the Pandas command (no explanations, no markdown).
        - If the question is ambiguous, return a query that provides meaningful insight.
        - Focus on sales-relevant analyses.
        - Time data is in this format 24/11/2023  13:10:00 and is on the column 'Created On'
        """

        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            pandas_code = response.choices[0].message.content.strip()
            print(pandas_code)

            if not pandas_code or "Error" in pandas_code:
                return "df.head()"
            return pandas_code
        except Exception as e:
            messagebox.showerror("Query Generation Error", str(e))
            return "df.head()"

    def execute_pandas_query(self, generated_code):
        local_vars = {"df": self.df}
        global_vars = {"pd": pd}
        try:
            exec(f"result = {generated_code}", global_vars, local_vars)
            return local_vars["result"]
        except Exception as e:
            return f"Error executing query: {str(e)}"

    def run_query(self):
        question = self.query_entry.get()
        if not question:
            messagebox.showwarning("Warning", "Please enter a query")
            return

        generated_code = self.generate_pandas_query(question)
        result = self.execute_pandas_query(generated_code)

        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, f"Query: {question}\n\nResult:\n{result}")

    def show_quick_insights(self):
        insights = [
            ("Total Sales", "df['Amount'].sum()"),
            ("Average Order Value", "df['Amount'].mean()"),
            ("Number of Transactions", "len(df)"),
            ("Top Product", "df.groupby('Product name')['Amount'].sum().idxmax()"),
            ("Top Customer", "df.groupby('Account (Opportunity) (Opportunity)')['Amount'].sum().idxmax()")
        ]

        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, "Quick Sales Insights:\n\n")

        for name, query in insights:
            try:
                result = self.execute_pandas_query(query)
                self.result_text.insert(tk.END, f"{name}: {result}\n")
            except Exception as e:
                self.result_text.insert(tk.END, f"{name}: Could not calculate\n")

    def open_visualization_window(self):
        viz_window = tk.Toplevel(self.root)
        viz_window.title("Sales Visualizations")
        viz_window.geometry("1000x700")

        # Create matplotlib figure
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle("Sales Data Visualizations", fontsize=16)

        # Plot 1: Sales by Product
        product_sales = self.df.groupby('Product name')['Amount'].sum().sort_values(ascending=False)
        product_sales.plot(kind='bar', ax=axes[0, 0], color='skyblue')
        axes[0, 0].set_title('Total Sales by Product')
        axes[0, 0].set_xlabel('Product')
        axes[0, 0].set_ylabel('Total Sales')
        axes[0, 0].tick_params(axis='x', rotation=45)

        # Plot 2: Sales Distribution
        sns.histplot(self.df['Amount'], kde=True, ax=axes[0, 1])
        axes[0, 1].set_title('Sales Distribution')
        axes[0, 1].set_xlabel('Sale Amount')
        axes[0, 1].set_ylabel('Frequency')

        '''
        # Plot 3: Monthly Sales Trend
        self.df['Date'] = pd.to_datetime(self.df['Created On'])
        monthly_sales = self.df.groupby(pd.Grouper(key='Date', freq='M'))['Amount'].sum()
        monthly_sales.plot(kind='line', ax=axes[1, 0], marker='o')
        axes[1, 0].set_title('Monthly Sales Trend')
        axes[1, 0].set_xlabel('Month')
        axes[1, 0].set_ylabel('Total Sales')
        '''
        

        # Plot 4: Top 5 Customers
        top_customers = self.df.groupby('Account (Opportunity) (Opportunity)')['Amount'].sum().nlargest(5)
        top_customers.plot(kind='pie', ax=axes[1, 1], autopct='%1.1f%%')
        axes[1, 1].set_title('Top 5 Customers by Total Sales')

        plt.tight_layout()

        # Embed matplotlib figure in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=viz_window)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)

def main():
    root = tk.Tk()
    app = SalesDataQueryApp(root)
    photo = PhotoImage(file="logo.png")
    # Set the window icon
    root.iconphoto(False, photo)
    root.mainloop()
    



if __name__ == "__main__":
    main()