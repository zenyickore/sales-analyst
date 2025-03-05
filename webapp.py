import streamlit as st
import pandas as pd
import openai
import os
from dotenv import load_dotenv

# Page configuration
st.set_page_config(page_title="C-Kore Sales Data Analyzer", page_icon="💡", layout="wide")

class SalesDataQueryApp:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # OpenAI API setup
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            st.error("Please set your OpenAI API key in .env file")
            st.stop()
        
        # Initialize OpenAI client
        openai.api_key = self.openai_api_key
        
        # Data loading
        self.load_data()

    def load_data(self, file_path="allops.csv"):
        try:
            self.df = pd.read_csv(file_path)
        except Exception as e:
            st.error(f"Could not load data: {e}")
            self.df = None

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

            if not pandas_code or "Error" in pandas_code:
                return "df.head()"
            return pandas_code
        except Exception as e:
            st.error(f"Query Generation Error: {e}")
            return "df.head()"

    def execute_pandas_query(self, generated_code):
        local_vars = {"df": self.df}
        global_vars = {"pd": pd}
        try:
            exec(f"result = {generated_code}", global_vars, local_vars)
            return local_vars["result"]
        except Exception as e:
            return f"Error executing query: {e}"

    def show_quick_insights(self):
        insights = [
            ("Total Sales", "df['Amount'].sum()"),
            ("Average Order Value", "df['Amount'].mean()"),
            ("Number of Transactions", "len(df)"),
            ("Top Product", "df.groupby('Product name')['Amount'].sum().idxmax()"),
            ("Top Customer", "df.groupby('Account (Opportunity) (Opportunity)')['Amount'].sum().idxmax()")
        ]

        insight_results = {}
        for name, query in insights:
            try:
                result = self.execute_pandas_query(query)
                insight_results[name] = result
            except:
                insight_results[name] = "N/A"
        
        return insight_results

def main():
    # App title and description
    st.title("🚀 C-Kore Sales Data Analyzer")
    st.markdown("**EACH QUERY COSTS 0.007 POUNDS**")
    st.markdown("Queries are case-sensitive, for better results try to avoid typos. If you get an error, try to be more specific in your query.")

    # Query hints
    st.sidebar.header("💡 Query Tips")
    st.sidebar.markdown("""
    Try these queries:
    - 'Top 5 salesmen, created by'
    - 'Average order value'
    - 'top Sales by field'
    - 'How many times have we worked with Technip UK Limited?"
    """)

    # Initialize the app
    app = SalesDataQueryApp()

    # Query input
    query = st.text_input("Enter your query:")
    
    # Buttons
    col1, col2 = st.columns(2)
    
    with col1:
        run_query = st.button("Run Query")
    
    with col2:
        show_insights = st.button("Quick Insights")

    # Result container
    result_container = st.container()

    # Query execution
    if run_query and query:
        with st.spinner('Generating query...'):
            generated_code = app.generate_pandas_query(query)
            result = app.execute_pandas_query(generated_code)
        
        result_container.subheader("Query Result")
        result_container.write(result)

    # Quick insights
    if show_insights:
        with st.spinner('Calculating insights...'):
            insights = app.show_quick_insights()
        
        result_container.subheader("Quick Sales Insights")
        for insight, value in insights.items():
            result_container.metric(insight, value)

if __name__ == "__main__":
    main()