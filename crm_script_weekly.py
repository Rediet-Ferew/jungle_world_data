import pandas as pd


DATE_FORMAT = '%Y-%m-%d'
def weekly_breakdown(df, df_original):

    
    df['visit_date'] = pd.to_datetime(df['visit_date'], format=DATE_FORMAT, errors='coerce')
    df_original['visit_date'] = pd.to_datetime(df_original['visit_date'], format=DATE_FORMAT, errors='coerce')


  
    df['visit_date'] = df['visit_date'].dt.tz_localize(None)
    df_original['visit_date'] = df_original['visit_date'].dt.tz_localize(None)


    # Cutoff date
    cutoff = pd.to_datetime('2023-08-28')
    df = df[df['visit_date'] >= cutoff]
    df_original = df_original[df_original['visit_date'] >= cutoff]


    email_min_dates = df.groupby('email')['visit_date'].min().reset_index()
    email_min_dates.rename(columns={'visit_date': 'first_visit_date'}, inplace=True)
    df = pd.merge(df, email_min_dates, on='email', how='left')


    # --- Step 3: Create weekly bins (shared between both dfs) ---
    start_date = df['visit_date'].min()
    end_date = df['visit_date'].max()


    week_starts = pd.date_range(start=start_date, end=end_date, freq='W-MON')
    week_ends = week_starts + pd.Timedelta(days=6)
    week_labels = [f"{s.strftime('%b %d, %Y')} - {e.strftime('%b %d, %Y')}" for s, e in zip(week_starts, week_ends)]


    bins = [start_date - pd.Timedelta(days=1)] + list(week_starts[1:]) + [end_date + pd.Timedelta(days=1)]


    # Apply bins to df (for customers)
    df['week_label'] = pd.cut(df['visit_date'], bins=bins, labels=week_labels, right=False)
    df['first_visit_week'] = pd.cut(df['first_visit_date'], bins=bins, labels=week_labels, right=False)


    # Apply bins to df_original (for revenue)
    df_original['week_label'] = pd.cut(df_original['visit_date'], bins=bins, labels=week_labels, right=False)
   

    # --- Step 4: Weekly analysis ---
    weekly_results = []
    for week in sorted(df['week_label'].dropna().unique(), key=lambda x: week_labels.index(x)):
        week_data = df[df['week_label'] == week]
        week_data_original = df_original[df_original['week_label'] == week]


        # Customers (only with valid emails)
        total_customers = week_data['email'].nunique()


        new_customer_mask = week_data['week_label'].astype(str) == week_data['first_visit_week'].astype(str)
        new_customers = week_data.loc[new_customer_mask, 'email'].nunique()
        returning_customers = total_customers - new_customers


        new_percentage = round((new_customers / total_customers * 100), 2) if total_customers else 0
        returning_percentage = round((returning_customers / total_customers * 100), 2) if total_customers else 0


        # Revenue (from df_original)
        total_revenue = week_data_original['purchase_value'].sum()
        total_revenue_ = week_data['purchase_value'].sum()


        # For new vs returning revenue:
        # safer to filter week_data_original using emails from df (since NaN emails can't be tracked as new/returning)
        new_revenue = week_data.loc[new_customer_mask, 'purchase_value'].sum()
        returning_revenue = total_revenue_ - new_revenue


        weekly_results.append({
            'week': week,
            'total_customers': total_customers,
            'new_customers': new_customers,
            'returning_customers': returning_customers,
            'new_percentage': new_percentage,
            'returning_percentage': returning_percentage,
            'total_revenue': total_revenue,
            'new_customer_revenue': new_revenue,
            'returning_customer_revenue': returning_revenue
        })


    return pd.DataFrame(weekly_results)



