# Different chart implementation for different metrics
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

def main():
    st.set_page_config(layout="wide")
    st.title('Gen AI - Trend analyser')

    tabs = ["Sales analysis", "Market analysis", "Demographics"]
    selected_tab = st.sidebar.radio("Select tab", tabs)

    uploader_file = st.file_uploader("Upload Excel file", type=["xlsx"])
    if uploader_file is not None:
            try:
                if selected_tab == "Sales analysis":
                    xls1 = pd.ExcelFile(uploader_file)
                    sales_df = pd.read_excel(uploader_file, sheet_name="Competitive_analysis")

                    # Melt DataFrame to long format
                    sales_df = sales_df.melt(id_vars=['Period'], var_name='Company', value_name='Sales')

                    # Chart
                    sales_chart = alt.Chart(sales_df).mark_line().encode(
                        x='Period:N',
                        y=alt.Y('Sales:Q', title='Sales'),
                        color='Company:N'
                    ).properties(
                        width=800,
                        height=400
                    )

                    # Render chart
                    st.altair_chart(sales_chart, use_container_width=True)


                elif selected_tab == "Market analysis":
                    st.write("Market analysis")
                    
                elif selected_tab == "Demographics":
                    st.write("Demographics")
                    xls2 = pd.ExcelFile(uploader_file)
                    demographic_df = pd.read_excel(uploader_file, sheet_name="demograph")
                    #xls2 = pd.ExcelFile(demographic_file)
                    #demograph_sheet = xls2.sheet_names[0]  # Assuming data is in the first sheet
                    #demograph_df = pd.read_excel(demographic_file, sheet_name=demograph_sheet)
                    st.write(demographic_df)
                    print(demographic_df)

                    # Create two columns layout
                    col1, col2 = st.columns(2)

                    for company in demographic_df.columns[1:]:
                        if company != 'Age group':  # Exclude 'Age group' column
                            # Create DataFrame for the current company
                            company_df = demographic_df[['Age group', company]].rename(columns={company: 'Percentage'})

                            # Plot pie chart for the current company
                            fig = px.pie(company_df, values='Percentage', names='Age group', title=f'{company} Demographics',
                                        hole=0.3)

                            # Render chart in the columns
                            if demographic_df.columns.get_loc(company) % 2 == 0:
                                col1.plotly_chart(fig, use_container_width=True)
                            else:
                                col2.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"An error occurred: {e}")

        

 
if __name__ == "__main__":
    main()
