"""
Dashboard Data Processor

This module processes raw transaction data to generate all the necessary
aggregations, KPIs, and AI-powered insights for the main dashboard.
"""

import pandas as pd
from typing import Dict, Any
import json
from datetime import datetime

from ai.ollama.factory import get_ollama_client

class DashboardProcessor:
    """
    A processor dedicated to preparing data for the dashboard UI.
    """

    def _generate_ai_insights(self, summary: Dict[str, Any], recent_data_slice: pd.DataFrame) -> Dict[str, Any]:
        """
        Uses the Hybrid Prompt Model to generate AI insights.
        """
        try:
            summary_json = json.dumps(summary, indent=2)
            data_csv = recent_data_slice.to_csv(index=False)

            prompt = f"""
            You are a financial analyst AI. Your task is to provide a brief, encouraging overview of the user's spending and identify 1-2 novel, actionable insights based on the provided data.

            Instructions:
            1.  For the overview, use the provided financial summary. Keep it positive and brief.
            2.  For the insights, analyze the raw transaction data to find patterns or anomalies that are not obvious from the summary alone.
            3.  Return a single, valid JSON object with two keys: "overview" (a string) and "insights" (a list of strings).

            Financial Summary:
            ```json
            {summary_json}
            ```

            Raw Transaction Data (last 90 days):
            ---
            {data_csv}
            ---

            Respond with only the JSON object.
            """
            
            ollama_client = get_ollama_client()
            llm_response = ollama_client.generate_completion(prompt)
            
            if llm_response.startswith("```json"):
                llm_response = llm_response[8:].strip()
            if llm_response.endswith("```"):
                llm_response = llm_response[:-3].strip()

            return json.loads(llm_response)

        except Exception as e:
            print(f"Error generating AI insights: {e}")
            return {"overview": "Could not generate AI insights at this time.", "insights": []}

    def process_dashboard_data(self, transactions_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Takes a raw transaction DataFrame and returns a dictionary
        of data structures ready for rendering on the dashboard.
        """
        if transactions_df.empty:
            return {"kpis": {}, "category_chart_data": pd.DataFrame(), "spending_over_time_data": pd.DataFrame(), "ai_insights": {}, "recent_transactions": pd.DataFrame()}

        # Ensure date column is in datetime format
        transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'])
        
        # --- KPIs and Category Chart (Current Month) ---
        current_month = datetime.now().month
        current_year = datetime.now().year
        monthly_df = transactions_df[
            (transactions_df['transaction_date'].dt.month == current_month) & 
            (transactions_df['transaction_date'].dt.year == current_year) & 
            (transactions_df['amount'] < 0) # Only debits
        ].copy()
        
        monthly_df['amount'] = monthly_df['amount'].abs()

        total_spend = monthly_df['amount'].sum()
        top_category_series = monthly_df.groupby('category')['amount'].sum().nlargest(1)
        top_category = top_category_series.index[0] if not top_category_series.empty else "N/A"
        largest_transaction = monthly_df['amount'].max() if not monthly_df.empty else 0

        kpis = {
            "total_spend": total_spend,
            "top_category": top_category,
            "largest_transaction": largest_transaction
        }

        category_chart_data = monthly_df.groupby('category')['amount'].sum().reset_index()

        # --- Spending Over Time (Last 6 Months) ---
        six_months_ago = pd.Timestamp.now() - pd.DateOffset(months=5)
        spending_over_time_df = transactions_df[
            (transactions_df['transaction_date'] >= six_months_ago) & 
            (transactions_df['amount'] < 0)
        ].copy()
        spending_over_time_df['amount'] = spending_over_time_df['amount'].abs()
        
        spending_over_time_data = spending_over_time_df.set_index('transaction_date').resample('M')['amount'].sum().reset_index()
        spending_over_time_data['month'] = spending_over_time_data['transaction_date'].dt.strftime('%b %Y')

        # --- AI Insights ---
        financial_summary = {
            "current_month_spend": total_spend,
            "top_spending_category": top_category,
            "category_totals": category_chart_data.set_index('category')['amount'].to_dict()
        }
        ninety_days_ago = pd.Timestamp.now() - pd.DateOffset(days=90)
        ai_data_slice = transactions_df[transactions_df['transaction_date'] >= ninety_days_ago].head(500)

        ai_insights = self._generate_ai_insights(financial_summary, ai_data_slice)

        # --- Recent Transactions ---
        recent_transactions = transactions_df.sort_values(by='transaction_date', ascending=False).head(10)

        return {
            "kpis": kpis,
            "category_chart_data": category_chart_data,
            "spending_over_time_data": spending_over_time_data,
            "ai_insights": ai_insights,
            "recent_transactions": recent_transactions
        }
