# Different chart implementation for different metrics
import streamlit as st
import pandas as pd
import altair as alt

def main():
    st.set_page_config(layout="wide")
    st.title('Gen AI - Trend analyser')

    # Uploader button
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

    if uploaded_file is not None:
        try:
            # Read excel file with openpyxl engine
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            selected_sheet = st.selectbox("Select sheet", sheet_names)

            # Display content of selected sheet
            df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
            # st.dataframe(df)

            # Sidebar
            st.sidebar.subheader("Get trends")
            trend_option = st.sidebar.selectbox("Choose an option", ['All year', '2020' ,'2021', '2022', '2023'])
            
            # Filter dataframe based on trend option
            if trend_option == "All year":
                filtered_df = df.copy()
            elif trend_option in ['2020','2021', '2022', '2023']:
                filtered_df = filter_year_data(df, trend_option)
            else:
                st.warning("Please select a valid option.")
            

            # Tabs
            tabs = ["View data", "Get Trend chart", "ChatBot"]
            selected_tab = st.sidebar.radio("Select tab", tabs)

            if selected_tab == "View data":
                view_data(filtered_df)  
            elif selected_tab == "Get Trend chart":
                get_trend_chart(filtered_df)
            elif selected_tab == "ChatBot":
                chat_bot()

        except Exception as e:
            st.error("An error occurred while reading the Excel file. Please ensure it is a valid Excel file.")
            st.error(f"Error details: {str(e)}")

def filter_year_data(df, selected_year):
    st.subheader(f"Trend for year {selected_year}")
    year_columns = [col for col in df.columns if str(selected_year) in col]
    filtered_df = df[['Particulars'] + year_columns]
    # st.dataframe(filtered_df)
    return filtered_df

def view_data(df):
    st.subheader("Actual datapoints")
    st.dataframe(df)

    if st.button("GET SUMMARY"):
        get_all_list = generate_summary(df)
        print(get_all_list)

def generate_summary(df):
    # List of particular names for summary
    summary_particulars = [
        "Total income", 
        "Total expenses",
        "Total tax expense",
        "Net profit /(loss)for the period",
        "Earnings per share (of ` 10/- each) (not annualised for quarters) - Basic",
        "Paid-up equity share capital (face value of ` 10 each)"
    ]

    # Filter dataframe based on summary particulars
    summary_df = df[df['Particulars'].isin(summary_particulars)]

    # Display summary dataframe
    # st.subheader("Summary")
    # st.dataframe(summary_df)

    # Extract values for each particular and store them in separate lists
    particular_lists = []
    header_list = summary_df.columns.tolist()
    header_list = header_list[1:]
    for particular in summary_particulars:
        particular_values = summary_df.loc[summary_df['Particulars'] == particular].iloc[:, 1:].values.flatten().tolist()
        particular_lists.append(particular_values)

    # Display summary dataframe
    st.subheader("Summary Dataframe")
    st.dataframe(summary_df)

    # Display lists for each particular
    st.subheader("Lists for Each Particular")
    for i, particular in enumerate(summary_particulars):
        st.write(f"{particular}: {particular_lists[i]}")

    # Display header list
    st.subheader("Header List")
    st.write(header_list)

    # Store all lists in a list variable
    all_lists = [summary_particulars, header_list] + particular_lists
    summary_prompt = f'''Act as a financial advisor well equiped in understading a company's financial statement. Your task is to summarize the company's return statement with the details below.
    The period for the financial statement is {header_list}, 
    The Income for the given period is {particular_lists[0]},
    The Expense for the given period is {particular_lists[1]},
    The Total Tax expense for the given period is {particular_lists[2]},
    The net profit or loss for the period is {particular_lists[3]},
    The earnings per share is {particular_lists[4]},
    The paid up share capital is {particular_lists[5]}
    Make sure that the provided data is in Million rupees except the Earnings per share.
    Provide the detailed summary with Introduction - A simple introduction, Heading for each particulars such as 'Income', 'Expense', 'Tax expense' and so on. and explain if the company has shown improvement or deprovement, Overall trend followed by Conclusion.
    '''

    st.write(summary_prompt)
    return all_lists


def get_trend_chart(df):
    st.subheader("Get Trend chart")
    st.write("DISCLAIMER : The below chart depicts the value in terms of million Rs except Earnings per share")
    # Dictionary containing chart type for each particular
    chart_info = {
        "Total income": {"chart_type": "line", "color": "blue"},
        "Total expenses": {"chart_type": "bar", "color": "green"},
        "Total tax expense": {"chart_type": "area", "color": "orange"},
        "Net profit /(loss)for the period": {"chart_type": "line", "color": "red"},
        "Earnings per share (of ` 10/- each) (not annualised for quarters) - Basic": {"chart_type": "line", "color": "purple"},
        "Paid-up equity share capital (face value of ` 10 each)": {"chart_type": "bar", "color": "yellow"}
    }

    # Generate chart for each particular
    charts = []
    for particular, info in chart_info.items():
        particular_df = df[df['Particulars'] == particular]
        if not particular_df.empty:
            # chart = generate_chart(particular_df, chart_type)
            chart = generate_chart(particular_df, info["chart_type"], info["color"])
            charts.append((particular, chart))

    # Render charts in rows of three
    num_charts = len(charts)
    num_rows = (num_charts + 2) // 3
    for i in range(num_rows):
        row_charts = charts[i * 3: (i + 1) * 3]
        col1, col2, col3 = st.columns(3)
        with col1:
            if i * 3 < num_charts:
                particular, chart = row_charts[0]
                st.subheader(particular)
                st.altair_chart(chart, use_container_width=True)
        with col2:
            if i * 3 + 1 < num_charts:
                particular, chart = row_charts[1]
                st.subheader(particular)
                st.altair_chart(chart, use_container_width=True)
        with col3:
            if i * 3 + 2 < num_charts:
                particular, chart = row_charts[2]
                st.subheader(particular)
                st.altair_chart(chart, use_container_width=True)


def generate_chart(df, chart_type, color):
    # Melt DataFrame to have 'Particulars', 'Date', and 'Value' columns
    melted_df = df.melt(id_vars='Particulars', var_name='Date', value_name='Value')

    # Convert 'Date' column to datetime
    melted_df['Date'] = pd.to_datetime(melted_df['Date'], format='%d %B %Y')

    # Generate chart based on chart type
    if chart_type == "line":
        chart = alt.Chart(melted_df).mark_line(color=color).encode(
            x=alt.X('Date:T', title='Date', axis=alt.Axis(format='%b %Y')),
            y='Value:Q'
        ).properties(
            width=800,
            height=400
        )
    elif chart_type == "bar":
        chart = alt.Chart(melted_df).mark_bar(color=color).encode(
            x=alt.X('Date:T', title='Date', axis=alt.Axis(format='%b %Y')),
            y='Value:Q'
        ).properties(
            width=800,
            height=400
        )
    elif chart_type == "area":
        chart = alt.Chart(melted_df).mark_area(color=color).encode(
            x=alt.X('Date:T', title='Date', axis=alt.Axis(format='%b %Y')),
            y='Value:Q'
        ).properties(
            width=800,
            height=400
        )
    return chart


def chat_bot():
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    # Try
     
    #####
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("What is up?"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # ip_df1 = pd.read_csv(os.path.join(analysis_folder,f'{report_name}_{selected_page}_consolidatedTable.csv'))
        sample_prompt = f'''STRICTLY DO NOT ANSWER TO ANY QUESTION WHICH IS IRRELAVENT TO THE ABOVE INPUT TABLE!!!
        '''
        message_text = [{"role":"system","content":f"{sample_prompt}"}]
        # response = openai.ChatCompletion.create(
        #     engine="gpt-35-turbo",
        #     messages = message_text,
        #     temperature=0.2,
        #     max_tokens=2048,
        #     top_p=0.95,
        #     frequency_penalty=0,
        #     presence_penalty=0,
        #     stop=None
        # )

        # res_output = response['choices'][0]['message']['content']
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown("Place holder")
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": "Place holder"})


if __name__ == "__main__":
    main()
