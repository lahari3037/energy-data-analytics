import streamlit as st
import boto3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# set up the page
st.set_page_config (page_title= "Renewable Energy Dashboard", page_icon= "⚡", layout="wide")

@st.cache_resource
def init_dynamodb():
   # connect to aws database
   return boto3.resource('dynamodb', region_name='us-east-1')

def load_data():
   # get data from database
   dynamodb =init_dynamodb()
   table_name ='energy-data-analytics-energy-data'
   table = dynamodb.Table(table_name)
   
   try:
       response = table.scan()
       return pd.DataFrame(response['Items'])
   except Exception as e:
       st.error(f" Error loading data:{str(e)}")
       return pd.DataFrame()

def main():
   st.title("Renewable Energy Analytics Dashboard")
   st.markdown("Real-time monitoring and analysis of energy generation & consumption")
   
   # load data with spinner
   with st.spinner("Loading data..."):
       df = load_data()
   
   if df.empty:
       st.warning("No data available. Make sure the data pipeline is running")
       return
   
   # clean up the data types
   df['energy_generated_kwh'] = pd.to_numeric (df['energy_generated_kwh'], errors= 'coerce'). fillna(0)
   df['energy_consumed_kwh'] = pd.to_numeric(df['energy_consumed_kwh'], errors='coerce').fillna(0)
   df['net_energy_kwh'] =pd.to_numeric(df['net_energy_kwh'], errors= 'coerce').fillna(0)
   df['timestamp'] =pd.to_datetime (df['timestamp'], errors='coerce')
   df['anomaly'] = df['anomaly'].astype(bool)
   
   # remove rows with bad timestamps
   df =df.dropna(subset=['timestamp'])
   
   # sidebar filters
   st.sidebar.header("Filters")
   available_sites = sorted(df['site_id'].unique())
   selected_sites = st.sidebar.multiselect( "Select Sites", options= available_sites, default=available_sites)
   
   # date range filter
   min_date =df['timestamp'].min().date()
   max_date =df['timestamp'].max().date()
   date_range = st.sidebar.date_input("Select Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
   
   # apply filters
   filtered_df = df[df['site_id'].isin(selected_sites)]
   
   if len(date_range) == 2:
       start_date, end_date = date_range
       filtered_df = filtered_df[
           (filtered_df['timestamp'].dt.date >= start_date) &
           (filtered_df['timestamp'].dt.date <= end_date)
       ]
   
   # show key metrics at the top
   col1, col2, col3, col4 =st.columns(4)
   
   with col1:
       total_records =len(filtered_df)
       st.metric("Total Records", f"{total_records:,}")
   
   with col2:
       total_anomalies = filtered_df['anomaly'].sum()
       st.metric("Total Anomalies",f" {total_anomalies:,}" )
   
   with col3 :
       anomaly_rate = (total_anomalies / total_records * 100) if total_records > 0 else 0
       st.metric("Anomaly Rate", f"{anomaly_rate:.1f}%")
   
   with col4:
       avg_net_energy = filtered_df['net_energy_kwh'].mean()
       st.metric("Avg Net Energy", f"{avg_net_energy:.1f} kWh")
   
   st.header("Analytics")
   
   # two column layout for charts
   col1, col2 = st.columns(2)
   
   with col1:
       st.subheader("Energy Generation vs Consumption by Site")
       
       # sum up energy by site
       site_summary = filtered_df.groupby('site_id').agg( {
           'energy_generated_kwh': 'sum',
           'energy_consumed_kwh': 'sum'
       } ).reset_index()
       
       # create bar chart
       fig_bar = go.Figure()
       fig_bar.add_trace(go.Bar(name='Generated', x=site_summary['site_id'],y=site_summary['energy_generated_kwh'], marker_color='lightgreen'))
       fig_bar.add_trace(go.Bar(name='Consumed',x=site_summary['site_id'],  y=site_summary['energy_consumed_kwh'],  marker_color='lightcoral'))
       
       fig_bar.update_layout(barmode='group', title="Total Energy by Site", xaxis_title="Site ID", yaxis_title="Energy (kWh)")
       st.plotly_chart(fig_bar, use_container_width=True)
   
   with col2:
       st.subheader("Anomaly Distribution by Site")
       
       # count anomalies per site
       anomaly_summary = filtered_df.groupby(['site_id','anomaly']).size().reset_index(name='count')
       anomaly_pivot = anomaly_summary.pivot(index='site_id', columns='anomaly', values='count').fillna(0)
       
       if True in anomaly_pivot.columns:
           fig_pie = px.pie (values=anomaly_pivot[True],names=anomaly_pivot.index, title="Anomalies by Site")
           st.plotly_chart (fig_pie, use_container_width=True)
       else:
           st.info("No anomalies found in the selected data range.")
   
   st.subheader("Energy Trends Over Time")
   
   # create time series chart -- group by hour
   time_series = filtered_df.set_index('timestamp'). groupby('site_id').resample('H').agg({
       'energy_generated_kwh': 'mean',
       'energy_consumed_kwh':'mean',
       'net_energy_kwh': 'mean'
   }).reset_index()
   
   fig_time = px.line(time_series, x='timestamp', y='net_energy_kwh', color='site_id', 
                     title='Net Energy Over Time by Site', labels={'net_energy_kwh': 'Net Energy (kWh)', 'timestamp': 'Time'})
   st.plotly_chart(fig_time,use_container_width=True)
   
   # show anomalies if any exist
   if filtered_df['anomaly'].any():
       st.subheader("Anomaly Timeline")
       
       anomalies = filtered_df[filtered_df['anomaly'] == True].copy()
       anomalies = anomalies.sort_values('timestamp', ascending=False)
       
       # fix negative values for chart sizing
       anomalies_fixed = anomalies.copy()
       anomalies_fixed['size_value'] =anomalies_fixed['energy_generated_kwh'].abs()
       anomalies_fixed['size_value'] = anomalies_fixed['size_value'].clip(lower=1)

       fig_anomaly = px.scatter (anomalies_fixed, x='timestamp', y='site_id', 
                       color='net_energy_kwh', size='size_value',
                       title='Anomaly Occurrences', 
                       labels={'timestamp':'Time', 'site_id':'Site ID'})
       
       st.subheader("Recent Anomalies")
       st.dataframe(anomalies[['site_id', 'timestamp', 'energy_generated_kwh', 'energy_consumed_kwh', 'net_energy_kwh']].head(10), use_container_width=True)
   
   # show raw data in expandable section
   with st.expander("Raw Data"):
       st.dataframe(filtered_df,use_container_width=True)
       
       # download button for csv
       csv = filtered_df.to_csv(index=False)
       st.download_button(label="Download CSV", data=csv, 
                         file_name=f" energy_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",  mime="text/csv")

if __name__ == "__main__":
   main()