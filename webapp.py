import streamlit as st
import pandas as pd
import openai
import os
from dotenv import load_dotenv

# Page configuration
st.set_page_config(page_title="Sales Query Assistant", page_icon="💡", layout="wide")

class SalesQueryApp:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # OpenAI API setup
        self.openai_api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            st.error("Please set your OpenAI API key in secrets or .env file")
            st.stop()
        
        # Initialize OpenAI client
        openai.api_key = self.openai_api_key
        
        # Data loading
        self.load_data()

    def load_data(self):
        try:
            # Use st.cache_data to optimize loading
            @st.cache_data
            def load_csv():
                return pd.read_csv("allops.csv")
            
            self.df = load_csv()
            
            # Try parsing date column
            try:
                self.df['Date'] = pd.to_datetime(self.df['Created On'], dayfirst=True)
            except:
                st.warning("Could not parse date column")
        
        except Exception as e:
            st.error(f"Error loading data: {e}")
            self.df = None

    def generate_pandas_query(self, question):
        # Prepare column information
        column_info = ", ".join(f"{col} ({dtype})" for col, dtype in self.df.dtypes.items())

        prompt = f"""
        You are a data analysis assistant for a sales team. The DataFrame contains these columns and their data types: {column_info}.
        
        Your task: Generate **ONLY** a valid Pandas query to answer this question precisely:

        "{question}"

        **Rules:**
        - Assume 'df' is the DataFrame
        - Output **ONLY** the Pandas command
        - Focus on sales-relevant analyses
        - Be concise and direct
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            pandas_code = response.choices[0].message.content.strip()

            return pandas_code if pandas_code else "df.head()"
        
        except Exception as e:
            st.error(f"Query generation error: {e}")
            return "df.head()"

    def execute_pandas_query(self, generated_code):
        local_vars = {"df": self.df}
        try:
            exec(f"result = {generated_code}", {}, local_vars)
            return local_vars["result"]
        except Exception as e:
            return f"Error executing query: {e}"

    def quick_insights(self):
        insights = [
            ("Total Extended Amount", "df['Extended Amount'].sum()"),
            ("Average Product Quantity", "df['Quantity'].mean()"),
            ("Number of Transactions", "len(df)"),
            ("Top Product by Sales", "df.groupby('Product name')['Extended Amount'].sum().idxmax()"),
            ("Average Order Value", "df['Extended Amount'].mean()"),
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
    st.title("🚀 Sales Data Query Assistant")
    st.markdown("""
    ### Your AI-Powered Sales Analytics Companion
    - Ask natural language questions about your sales data
    - Get instant insights and precise query results
    """)

    # Initialize the app
    app = SalesQueryApp()

    # Sidebar for user interactions
    st.sidebar.header("Data Query Options")
    
    # Query input
    query = st.sidebar.text_input("Enter your sales query:", 
        placeholder="e.g., Total sales for top 3 products")
    
    # Buttons
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        run_query = st.button("Run Query")
    
    with col2:
        show_insights = st.button("Quick Insights")

    # Main content area
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
            insights = app.quick_insights()
        
        result_container.subheader("Quick Sales Insights")
        for insight, value in insights.items():
            result_container.metric(insight, value)

    # Additional context and help
    st.sidebar.markdown("""
    ### 💡 Query Tips
    - Ask about sales, quantities, products
    - Use natural language
    - Examples:
        - "Total sales this month"
        - "Top 5 selling products"
        - "Average order value"
    """)

if __name__ == "__main__":
    main()