import pandas as pd

def monthly_breakdown(df):

    # Ensure date is in datetime format
    df['visit_date'] = pd.to_datetime(df['visit_date'], format='%Y-%m-%d %H:%M:%S%z', errors='coerce')


    # Remove timezone before converting to period
    df['visit_date'] = df['visit_date'].dt.tz_localize(None)

    # Convert to month period
    df['month'] = df['visit_date'].dt.to_period('M')

    # Find first visit date for each customer
    first_visits = df.groupby('email')['visit_date'].min().reset_index()
    first_visits.columns = ['email', 'first_visit_date']

    # Merge first visit date back to main dataframe
    df = pd.merge(df, first_visits, on='email')

    # Create period for first visit month
    df['first_visit_month'] = df['first_visit_date'].dt.to_period('M')

    # Monthly breakdown of new vs returning
    monthly_results = []

    for month in sorted(df['month'].unique()):
        # Filter data for current month
        month_data = df[df['month'] == month]

        # Count unique customers for the month
        total_customers = month_data['email'].nunique()

        # Count new customers (first visit in this month)
        new_customers = month_data[month_data['month'] == month_data['first_visit_month']]['email'].nunique()

        # Count returning customers
        returning_customers = total_customers - new_customers

        # Calculate percentages
        new_percentage = round((new_customers / total_customers * 100), 2) if total_customers > 0 else 0  
        returning_percentage = round((returning_customers / total_customers * 100), 2) if total_customers > 0 else 0  

        # Total revenue for the month
        month_revenue = month_data['purchase_value'].sum()

        # Revenue from new vs returning
        new_revenue = month_data[month_data['month'] == month_data['first_visit_month']]['purchase_value'].sum()
        returning_revenue = month_revenue - new_revenue

        monthly_results.append({
            'month': month,
            'total_customers': total_customers,
            'new_customers': new_customers,
            'returning_customers': returning_customers,
            'new_percentage': new_percentage,
            'returning_percentage': returning_percentage,
            'total_revenue': month_revenue,
            'new_customer_revenue': new_revenue,
            'returning_customer_revenue': returning_revenue
        })

    # Convert results to DataFrame
    monthly_df = pd.DataFrame(monthly_results)
    # Calculate LTV
    # Basic LTV
    total_revenue = df['purchase_value'].sum()
    unique_customers = df['email'].nunique()
    basic_ltv = total_revenue / unique_customers

    # More sophisticated LTV
    avg_purchase_value = total_revenue / len(df)
    avg_purchase_frequency = len(df) / unique_customers

    # Customer lifespan calculation (simplified)
    # Assuming 6 months if no activity for 6 months means churned
    df_sorted = df.sort_values(['email', 'visit_date'])

    # Calculate days between visits for each customer
    df_sorted['next_visit'] = df_sorted.groupby('email')['visit_date'].shift(-1)
    df_sorted['days_between_visits'] = (df_sorted['next_visit'] - df_sorted['visit_date']).dt.days

    # Compute average days between visits
    avg_days_between_visits = df_sorted['days_between_visits'].mean()
    churn_threshold = 180
    avg_customer_lifespan = churn_threshold / avg_days_between_visits
    # Calculate average lifespan (in months)
    # This is a simplification - real calculation would be more complex

    # Calculate LTV
    ltv = avg_purchase_value * avg_purchase_frequency * avg_customer_lifespan

    return {
        'monthly_breakdown': monthly_df,
        'Basic LTV': basic_ltv,
        'Advanced LTV': ltv,
        'Average Purchase Value': avg_purchase_value,
        'Average Purchase Frequency': avg_purchase_frequency,
        'Average Customer LifeSpan(Months)': avg_customer_lifespan
    }






