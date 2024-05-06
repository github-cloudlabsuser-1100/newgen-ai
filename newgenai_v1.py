# Different chart implementation for different metrics
import streamlit as st
import pandas as pd
import altair as alt
import os
from openai import AzureOpenAI
import plotly.express as px

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from PIL import Image


def main():
    st.set_page_config(layout="wide")

    newgenai_logo = "NGAI-transformed.png"
    ui_logo = Image.open(newgenai_logo)
    if ui_logo is not None:
        st.image(ui_logo,width=100)

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
            tabs = ["View financial data", "Get Trend chart","Competitive analysis","Demographic analysis","ChatBot"]
            selected_tab = st.sidebar.radio("Select tab", tabs)

            if selected_tab == "View financial data":
                view_data(filtered_df)  
            elif selected_tab == "Get Trend chart":
                get_trend_chart(filtered_df)
            elif selected_tab == "Competitive analysis":
                sales_df = pd.read_excel(uploaded_file, sheet_name="Competitive_analysis")
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
                sales_summary_prompt = f'Prepare a sales summary for Varun beverages with the data given below {sales_df}. Emphasize how Varun Beverage is competing with its peer companies and mention its trend change compared to each quarters and the delta change with its peer'
                if st.button("GENERATE SALES SUMMARY"):
                    generate_sales_summary = call_openai(sales_summary_prompt)
                    st.write(generate_sales_summary)

            elif selected_tab == "Demographic analysis":
                xls2 = pd.ExcelFile(uploaded_file)
                demographic_df = pd.read_excel(uploaded_file, sheet_name="demograph")
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

                demographic_summary_prompt = f'You are provided with the demographic data of Varun Beverages and its peers, the data is given below : {demographic_df}, provide an analysis of how each beverage company is targeting each age group and emphasize on how VB focus on the different demographic group and is grabbing attention of all age group'
                if st.button("GENERATE DEMOGRAPHIC SUMMARY"):
                    generate_demographic_summary = call_openai(demographic_summary_prompt)
                    st.write(generate_demographic_summary)

            elif selected_tab == "ChatBot":
                sales_df = pd.read_excel(uploaded_file, sheet_name="Competitive_analysis")
                demographic_df = pd.read_excel(uploaded_file, sheet_name="demograph")
                chat_bot(filtered_df,sales_df,demographic_df)

        except Exception as e:
            st.error("An error occurred while reading the Excel file. Please ensure it is a valid Excel file.")
            st.error(f"Error details: {str(e)}")

def write_pdf():
    # Read content from text file and split into sections
    with open('openai_response.txt', 'r') as file:
        sections = file.read().split('\n\n')

    # Create a custom style with a border
    border_style = ParagraphStyle(
        name='Border',
        borderPadding=5,
        borderWidth=1,
        borderColor=colors.black,
    )

    # Create a PDF document
    doc = SimpleDocTemplate(f"newgenai_analytics.pdf", pagesize=letter)

    # Define styles
    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    bordered_style = styles.add(border_style)

    # Add content to PDF
    content_elements = [] 
    content_elements.append(Spacer(1, 12))
    
    # Add Title
    title_style = ParagraphStyle(
        name='Title',
        fontSize=18,
        underline=1
    )
    content_elements.append(Paragraph('<b>New Gen AI - Analysis report</b>', title_style))
    content_elements.append(Spacer(1, 12))
    
    # Add Subtitle
    subtitle_style = ParagraphStyle(
        name='Subtitle',
        fontSize=16,
        underline=1
    )
    content_elements.append(Paragraph('<b>Varun Beverages Analysis report</b>', subtitle_style))

    # Add spacer between title and sections
    content_elements.append(Spacer(1, 50))


    # Add sections with bold headings
    for section in sections:
        if section.strip():  # Skip empty sections
            heading, content = section.split(':', 1)
            content_elements.append(Paragraph('<b>{}</b>'.format(heading.strip()), styles["Heading1"]))
            content_elements.append(Paragraph(content.strip(), bordered_style))
            content_elements.append(Spacer(1, 12))

    doc.build(content_elements)

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

def call_openai(prompt):
    client = AzureOpenAI(
    azure_endpoint = "https://testnewgenai.openai.azure.com/", 
    api_key="d74f723f3d244036999db7ebce4b8764",  
    api_version="2024-02-15-preview"
    )

    message_text = [{"role":"system","content":"You are an AI assistant that helps people find information."},
        {"role":"user","content":f"{prompt}"}]

    completion = client.chat.completions.create(
        model="gpt35turbo_newgenai", # model = "deployment_name"
        messages = message_text,
        temperature=0.2,
        max_tokens=2048,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
        )

    get_response = completion.choices[0].message.content
    return get_response

def generate_summary(df):
    client = AzureOpenAI(
    azure_endpoint = "https://testnewgenai.openai.azure.com/", 
    api_key="d74f723f3d244036999db7ebce4b8764",  
    api_version="2024-02-15-preview"
    )

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

    message_text = [{"role":"system","content":"You are an AI assistant that helps people find information."},
        {"role":"user","content":f"{summary_prompt}"}]

    completion = client.chat.completions.create(
        model="gpt35turbo_newgenai", # model = "deployment_name"
        messages = message_text,
        temperature=0.2,
        max_tokens=2048,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
        )

    st.write(summary_prompt)
    with open('openai_response.txt','w') as file:
        file.write(completion.choices[0].message.content)

    st.write(completion.choices[0].message.content)
    write_pdf()
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

def chat_bot(df1,df2,df3):
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
    if prompt := st.chat_input("Ask any question on the financial year, the competitive analysis and demographic information of Varun Beverages?"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # ip_df1 = pd.read_csv(os.path.join(analysis_folder,f'{report_name}_{selected_page}_consolidatedTable.csv'))
        user_prompt = f'''
        Act as a experienced sales analyst in the beverages sales domain.
        You are given with the financial dataframe of Varun Beverages (VB) : {df1} which is the financial statement of Varun Beverages (VB) make sure that the data given in the financial statement is expressed in terms of Million rupees except for the Earning per share, the competitive analysis of VB is : {df2}, this dataframe provides the competitor list of VB and the demographic data is : {df3}, this shows what percentage of people from different categories have preferred which Company drink.
        As a Q&A assistant of Varun beverage, your task is to provide answers for the questions that are relavant to the data that you have as the dataframes.
        The user question is : {prompt}
        Analyze the question first, if the question can be answered by referring to the data table, provide direct answers without any explanations,
        But, if there is any decision making question related to the beverage industry, you should be able to provide proper response.
        For example: If the user question is "Is it a right time for VB to launch their new drink in India in the month of May 2024?", 
        Generally the summer in India will be during the month of March to May followed by monsoon and rainy season from September to January.
        Analyze the overall growth of VB based on its financial statement and provide your response keeping in mind launching a new soft drink is always a good opinion during summer to beat the heat while the soft drink sales will be low during monsoon and rainy season and so you can suggest the user to launch soft drinks in the summer time for better sales and revenue. Also ensure that the company is showing consistent growth in its sales and only then people will buy that company's product, if the growth is not upto the mark, provide the suggestion accordingly by suggesting effective promotion to increase sales of new product.        
        STRICTLY DO NOT ANSWER TO ANY QUESTION WHICH IS IRRELAVENT TO THE SOFT DRINK INDUSTRY!!!
   
        If the user question is irrelavant to the soft drink you have, respond by saying "Sorry, I can't answer to your question as I don't have the corresponding data"
        '''
        
        #st.write(user_prompt)
        bot_output = call_openai(user_prompt)
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(bot_output)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": f"{bot_output}"})


if __name__ == "__main__":
    main()
