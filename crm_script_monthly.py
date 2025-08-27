import pandas as pd

def monthly_breakdown(df, df_original):
    # Ensure visit_date is datetime
    df['visit_date'] = pd.to_datetime(df['visit_date'], errors='coerce')
    df_original['visit_date'] = pd.to_datetime(df_original['visit_date'], errors='coerce')

    # Remove timezone info
    df['visit_date'] = df['visit_date'].dt.tz_localize(None)
    df_original['visit_date'] = df_original['visit_date'].dt.tz_localize(None)

    # Convert to month period
    df['month'] = df['visit_date'].dt.to_period('M')
    df_original['month'] = df_original['visit_date'].dt.to_period('M')

    # Compute first visit date per customer
    first_visits = df.groupby('email')['visit_date'].min().reset_index()
    first_visits.columns = ['email', 'first_visit_date']
    first_visits['first_visit_month'] = first_visits['first_visit_date'].dt.to_period('M')

    # Merge first visit info back
    df = df.merge(first_visits, on='email', how='left')

    # Prepare results container
    monthly_results = []

    # Iterate over each month
    for month in sorted(df['month'].unique()):
        month_data = df[df['month'] == month]
        month_data_original = df_original[df_original['month'] == month]

        total_customers = month_data['email'].nunique()

        # New customers: first visit in this month
        new_customers_df = month_data[month_data['first_visit_month'] == month]
        new_customers = new_customers_df['email'].nunique()

        returning_customers = total_customers - new_customers

        new_percentage = round((new_customers / total_customers * 100), 2) if total_customers > 0 else 0
        returning_percentage = round((returning_customers / total_customers * 100), 2) if total_customers > 0 else 0

        # Revenue calculations
        month_revenue = month_data['purchase_value'].sum()
        total_revenue = month_data_original['purchase_value'].sum()

        # Revenue from new vs returning customers
        new_revenue = new_customers_df.groupby('email').first()['purchase_value'].sum()
        returning_revenue = month_revenue - new_revenue

        monthly_results.append({
            'month': month,
            'total_customers': total_customers,
            'new_customers': new_customers,
            'returning_customers': returning_customers,
            'new_percentage': new_percentage,
            'returning_percentage': returning_percentage,
            'total_revenue': total_revenue,
            'new_customer_revenue': new_revenue,
            'returning_customer_revenue': returning_revenue
        })

    monthly_df = pd.DataFrame(monthly_results)

    # LTV calculations
    total_revenue_all = df['purchase_value'].sum()
    unique_customers = df['email'].nunique()

    basic_ltv = total_revenue_all / unique_customers if unique_customers > 0 else 0
    avg_purchase_value = total_revenue_all / len(df) if len(df) > 0 else 0
    avg_purchase_frequency = len(df) / unique_customers if unique_customers > 0 else 0

    # Customer lifespan calculation
    df_sorted = df.sort_values(['email', 'visit_date'])
    df_sorted['next_visit'] = df_sorted.groupby('email')['visit_date'].shift(-1)
    df_sorted['days_between_visits'] = (df_sorted['next_visit'] - df_sorted['visit_date']).dt.days

    avg_days_between_visits = df_sorted['days_between_visits'].dropna().mean() if not df_sorted['days_between_visits'].dropna().empty else 1
    churn_threshold = 180  # days
    avg_customer_lifespan_months = churn_threshold / avg_days_between_visits if avg_days_between_visits > 0 else 1

    advanced_ltv = avg_purchase_value * avg_purchase_frequency * avg_customer_lifespan_months

    return {
        'monthly_breakdown': monthly_df,
        'Basic LTV': basic_ltv,
        'Advanced LTV': advanced_ltv,
        'Average Purchase Value': avg_purchase_value,
        'Average Purchase Frequency': avg_purchase_frequency,
        'Average Customer LifeSpan(Months)': avg_customer_lifespan_months
    }
