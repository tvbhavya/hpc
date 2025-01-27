import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO, BytesIO
import time
import mysql.connector
from mysql.connector import Error, MySQLConnection
import hashlib
import toml
import re
from st_aggrid import AgGrid, GridOptionsBuilder
import pandas as pd
from datetime import datetime
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from datetime import date

blue_logo_path = r"C:\Users\bhavya.shah\Desktop\hpc_codes\blue_logo.png"
white_logo_path = r"C:\Users\bhavya.shah\Desktop\hpc_codes\white_logo.png"
blogo = Image.open(blue_logo_path)
wlogo = Image.open(white_logo_path)


st.set_page_config(layout="wide")

domain_to_check = ["slrcp.com","mo.com","inflexion.com","vistria.com","lcatterton.com","solarcapltd.com", "hpc.com"]

# Initialize session state variables
if 'email_id' not in st.session_state:
    st.session_state.email_id = []
# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'sign_in'  # Set default page to sign in

# Database configuration
db_config = {
    "host": st.secrets["database"]["host"],
    "user": st.secrets["database"]["username"],
    "password": st.secrets["database"]["password"],
    "database": st.secrets["database"]["database"],
    "port": st.secrets["database"]["port"]
}

# Sign Up Form
def sign_up_form():
    col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11 = st.columns(11)
    with col1:
        if styled_button("Back", key="back_button"):
            st.session_state.page = "sign_in"  # Navigate to sign-up page
            st.rerun()  # Use rerun to refresh the app

    col1, col2, col3 = st.columns([4, 1, 4])
    with col2:
        st.image(blogo, width=250)

    col1, col2, col3 = st.columns(3)
    with col2:
        st.markdown("<h2 style='text-align: center;'>Sign Up</h2>", unsafe_allow_html=True)

    with st.container():
        email_id = st.text_input("Email", key="signup_email")
        username = st.text_input("Username", key="signup_username")
        if username:
            if not is_valid_username(username):
                st.warning("Invalid username. Only alphanumeric characters and underscores are allowed.")
        password = st.text_input("Create Password", type="password", key="signup_password")
        if password:
            if not is_strong_password(password):
                st.warning("Weak password. Ensure your password is of at least 8 characters, containing at least 1 Capital letter and a special character.")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")

        # Check if all fields are filled
        if st.button("Submit"):
            if not email_id or not username or not password or not confirm_password:
                st.error("All fields are required!")
                time.sleep(10)
                st.rerun()
            elif password != confirm_password:
                st.error("Passwords do not match!")
                time.sleep(10)
                st.rerun()
            elif not is_valid_username(username):
                st.error("Invalid username. Only alphanumeric characters and underscores are allowed.")
            elif not is_strong_password(password):
                st.error("Weak password. Ensure your password is of at least 8 characters, containing at least 1 Capital letter and a special character.")
            else:
                insert_user(email_id, username, password)
    return email_id

def styled_button(label, key=None):
    # Create a unique key if not provided
    if key is None:
        key = f"styled_button_{label}"
    st.markdown(
        f"""
        <style>
        div.stButton > button {{
            width: 100%; /* Full width */
            padding: 10px; /* Increase padding for height */
            font-size: 16px;
            background-color: #001444; /* Button color */
            color: white;
            border: none;
            border-radius: 5px; /* Rounded corners */
            cursor: pointer;
            transition: background-color 0.3s ease; /* Smooth transition */
        }}
        div.stButton > button:hover {{
            background-color: #FFB401; /* Yellow on hover */
            color: white;
            font-weight: bold;
        }}
        </style>
        """, unsafe_allow_html=True
    )
    return st.button(label, key=key)

# MySQL Database Connection
def create_connection():
    try:
        conn = MySQLConnection(**db_config)
        if conn.is_connected():
            return conn
    except Error as e:
        st.error(f"Error connecting to MySQL.")
        time.sleep(10)
        st.rerun()
    return None

# Hashing function for passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def is_valid_email(email):
    # Define the regex pattern for a valid email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_strong_password(password):
    # Check for at least 8 characters, one uppercase letter, and one special character
    if (len(password) >= 8 and re.search(r'[A-Z]', password) and re.search(r'[!@#$%^&*(),.?":{}|<>]', password)):
        return True
    return False

def show_temporary_message(placeholder, message):
    placeholder.warning(message)
    time.sleep(3)  # Display for 3 seconds
    placeholder.empty()

def is_valid_username(username):
    # Define the regex pattern for a valid username
    pattern = r'^[a-zA-Z0-9_]+$'
    return re.match(pattern, username) is not None

def insert_user(email_id, username, password):
    if not is_valid_email(email_id):
        st.warning("Invalid email address. Please enter a valid email.")
        return
    if not is_valid_username(username):
        st.warning("Invalid username. Only alphanumeric characters and underscores are allowed, with no spaces.")
        return
    if not is_strong_password(password):
        st.warning("Password must be at least 8 characters long and contain at least one uppercase letter and one special character.")
        return

    connection = create_connection()
    if connection is None:
        return  # Exit if connection failed

    cursor = connection.cursor()
    password_hash = hash_password(password)

    # Check if the username already exists
    check_query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(check_query, (username,))
    if cursor.fetchone() is not None:
        st.warning("Username already exists. Use another username.")
        cursor.close()
        connection.close()
        return

    insert_query = "INSERT INTO users (email_id, username, password_hash) VALUES (%s, %s, %s)"
    # try:
    cursor.execute(insert_query, (email_id, username, password_hash))
    connection.commit()
    st.success("Sign up successful! Redirecting to sign in...")
    # Set session state to indicate successful sign-up
    st.session_state.redirect_to_sign_in = True
    # Refresh the app to show the new page
    st.rerun()

if 'redirect_to_sign_in' in st.session_state and st.session_state.redirect_to_sign_in:
    # Reset the redirect flag
    st.session_state.redirect_to_sign_in = False
    # Redirect to sign-in page
    st.session_state.page = "sign_in"
    st.rerun()

# # Function to authenticate user
# def authenticate_user(username, password):
#     connection = create_connection()
#     if connection is None:
#         return "error"  # Exit if connection failed

#     cursor = connection.cursor()
#     password_hash = hash_password(password)

#     # Check if the username exists
#     cursor.execute("SELECT * FROM users WHERE email_id = %s", (email_id,))
#     user = cursor.fetchone()
#     if user is None:
#         cursor.close()
#         connection.close()
#         return "email_id_not_found"  # Username does not exist

#     # Username exists, now check password
#     cursor.execute("SELECT * FROM users WHERE email_id = %s AND password_hash = %s", (email_id, password_hash))
#     result = cursor.fetchone()
#     cursor.close()
#     connection.close()
#     if result:
#         return "success"  # User authenticated successfully
#     else:
#         return "wrong_password"  # Password is incorrect

def authenticate_user(email_id):
    connection = create_connection()
    if connection is None:
        return "error"  # Exit if connection failed

    cursor = connection.cursor()

    # Check if the email_id exists
    cursor.execute("SELECT * FROM users WHERE email_id = %s", (email_id,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if user is None:
        return "email_id_not_found"  # Email ID does not exist

    return "success"  # User authenticated successfully


if st.session_state.page == 'sign_in':
    # st.markdown("", unsafe_allow_html=True)

    # Custom CSS for styling the button
    st.markdown("""
        <style>
            .custom-button {
                font-size: 12px;  /* Smaller font size */
                position: absolute;
                top: 10px;
                right: 10px;
            }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11 = st.columns(11)
    with col11:
        if styled_button("Sign Up", key="signup_button"):
            st.session_state.page = "sign_up"  # Navigate to sign-up page
            st.rerun()  # Use rerun to refresh the app

    col1, col2, col3 = st.columns([4,2,4])

    with col2:
        st.image(blogo, width=300)

    # Centered welcome title
    st.markdown("<h1 style='text-align: center;'>LOGIN PAGE</h1>", unsafe_allow_html=True)

    # Use columns to center the grey box and sign-in button
    col1, col2, col3 = st.columns(3)

    # Add the grey box in the center column
    with col2:
        st.markdown("""
            <style>
                .	 > div > input {
                    height: 1500px;  /* Set your desired width here */
                }
            </style>
        """, unsafe_allow_html=True)

        # Sign-in form components
        email_id = st.text_input("Email ID", key="signin_email_id")
        if email_id:
            st.session_state['email_id'] = email_id
        password = st.text_input("Password", type="password", key="signin_password")

        if styled_button("Log In"):
            # Check for empty fields
            # if not email_id or not password:
            if not email_id or password:
                st.error("Please enter all fields!")
                time.sleep(10)
                st.rerun()
            else:
                # auth_result = authenticate_user(email_id, password)
                auth_result = authenticate_user(email_id)

                if auth_result == "success":
                    st.success("Login successful! Redirecting...")
                    if email_id.endswith('@hpc.com'):
                        st.session_state.page = "hpc_page"  # Navigate to HPC page
                    else:
                        st.session_state.page = "upload"
                    st.rerun()  # Use rerun to refresh the app
                elif auth_result == "emailid_not_found":
                    st.error("Email does not exist! Please sign up.")
                    time.sleep(10)
                    st.rerun()
                elif auth_result == "wrong_password":
                    st.warning("Incorrect password! Please try again.")
                else:
                    st.warning("An error occurred during authentication.")


elif st.session_state.page == 'sign_up':
    sign_up_form()

#  Function to check if a string is in the email ID
def check_string_in_email(domain_list):
    if 'email_id' in st.session_state:
        email_id = st.session_state["email_id"]
    for domain in domain_list:
        if domain in email_id:
            return domain
    return None


def fetch_data():
    connection = create_connection()
    if connection.is_connected():
        try:
            # Fetch data from the first table
            query1 = "SELECT * FROM sharepoint_list"
            df = pd.read_sql(query1, connection)
            
            # Fetch data from the second table
            query2 = "SELECT * FROM date_table"
            df_date_table = pd.read_sql(query2, connection)
            
            return df, df_date_table
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return pd.DataFrame(), pd.DataFrame()  # Return empty DataFrames if there's an error
        finally:
            connection.close()
    else:
        st.error("Failed to connect to the database.")
        return pd.DataFrame(), pd.DataFrame()  # Return empty DataFrames if connection fails
    

# List of domains to check
domain_gp_mapping  = {
    'lcatterton.com': 'L Catterton',
    'slrcp.com': 'SLR',
    'mo.com': 'MidOcean',
    'vistria.com': 'The Vistria Group, LP',
    'inflexion.com': 'Inflexion Strategic Partners LP'
}


def create_consolidated_income_statement_tab(gp_name, user_domain):
    df = st.session_state.df
    df_date_table = st.session_state.df_date_table
    selected_year = st.session_state.selected_year
    selected_type = st.session_state.selected_type
    # filter the data on type, gpname and year
    filtered_df = df[df['Type']==selected_type]
    filtered_df = filtered_df[filtered_df['GPName']==gp_name]
    filtered_df = filtered_df[filtered_df['Year']==selected_year]
    # Get the latest PeriodAsOfYearQuarter
    latest_period = filtered_df['PeriodAsOfYearQuarter'].max()
    # Further filter to show only the latest data
    latest_data = filtered_df[filtered_df['PeriodAsOfYearQuarter'] == latest_period]
    categories = latest_data['Category'].unique()
    for category in categories:
        with st.expander(f"Category: {category}"):
            category_data = latest_data[latest_data['Category'] == category][['Category', 'SubCategory', 'KPI', 'Values', 'YearQuarter']]
            pivoted_df = category_data.pivot(index=['Category', 'KPI', 'SubCategory'], columns='YearQuarter', values='Values').reset_index()
            # Store edited DataFrame in session state
            if f"edited_df_{category}" not in st.session_state:
                st.session_state[f"edited_df_{category}"] = pivoted_df
            
            edit_mode = st.checkbox("Edit Mode", key=f"edit_mode_{category}")
            if edit_mode:
                # Use the stored edited DataFrame for editing
                edited_df = st.data_editor(st.session_state[f"edited_df_{category}"])
                # Update session state with the edited DataFrame
                st.session_state[f"edited_df_{category}"] = edited_df
                if st.button("Save Changes", key=f"save_button_{category}"):
                    st.write("Melting the dataframe...")
                    value_vars = edited_df.columns[-4:]  # Assuming last 4 columns are YearQuarter values
                    melted_df = pd.melt(edited_df, id_vars=['Category', 'KPI', 'SubCategory'], value_vars=value_vars,
                                        var_name='YearQuarter', value_name='Values')
                    st.write("Melted dataframe:", melted_df)
            else:
                st.dataframe(pivoted_df)

def create_sidetab_gp(df, df_date_table):
    # Add custom CSS to change the sidebar background color and style the title
    st.markdown(
    """
    <style>
    /* Set the background color of the entire webpage */
    .stApp {
        background-color: white !important;  /* Light green background */
    }

    /* Set the background color for the sidebar */
    [data-testid="stSidebar"] {
        background-color: #001444 !important;  /* Dark blue background for the sidebar */
    }

    /* Set the color for the sidebar title */
    [data-testid="stSidebar"] .css-1d391kg {
        color: white !important;  /* Change sidebar title color to white */
        align-items: center;
        font-size: 18px;
    }

    /* Set the background color for the header */
    header {
        background-color: #001444 !important;  /* Dark blue background for the header */
        color: black;  /* Black text for the header */
    }

    /* Hide the Streamlit menu and footer */
    #MainMenu {
        visibility: hidden;
    }
    footer {
        visibility: hidden;
    }

    /* Set the color for all headers in the sidebar */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] h5 {
        color: white !important;  /* Change all sidebar headers to white */
        font-size: 24px;  /* Set font size for sidebar headers */
        align-items: center;
        font-weight: bold !important;
        text-align: center; /* Center align the sidebar headers */
    }

    /* Center align the selectbox header */
    [data-testid="stSidebar"] .stSelectbox label {
        text-align: center; /* Center align the label */
        width: 100%; /* Make label take full width */
        display: flex; /* Use flexbox for alignment */
        justify-content: center; /* Center align the label */
    }

    /* Change font color of selectbox options in sidebar to yellow, with transparent background */
    [data-testid="stSidebar"] .stSelectbox div {
        color: white !important;  /* Change options text color to white */
        background-color: transparent !important;  /* No background color for options */
        font-size: 17px;  /* Set font size for selectbox options */
        display: flex;  /* Use flexbox for alignment */
        justify-content: center;  /* Center align the options */
        align-items: center;  /* Center align vertically */
    }

    /* Change dropdown arrow color to white */
    [data-testid="stSidebar"] .stSelectbox div > div > svg {
        fill: white !important;  /* Change arrow (dropdown) icon color to white */
    }

    /* Style for headers in the application */
    h1, h2, h3, h4, h5 {
        color: black;  /* Black color for headers */
        font-weight: bold;  /* Make headers bold */
    }

    /* Style for buttons in the sidebar (navigation bar) */
    [data-testid="stSidebar"] .stButton button {
        background-color: transparent;  /* Dark blue button background */
        color: white;  /* White text color */
        border: 2px solid white;  /* White border with a width of 2px */
        cursor: pointer;  /* Pointer cursor on hover */
        transition: background-color 0.3s ease;  /* Smooth transition */
        font-weight: 900;
        width: 100%;
    }

    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #FFB401;  /* Yellow on hover */
        color: white;
        font-weight: 900; 
    }

    [data-testid="stSidebar"] .stButton button:active {
        color: white;  /* Text color remains white */
        background-color: #001444;  /* Keep the background dark blue */
        border: 2px solid white;  /* Set border color to white */
    }

    /* Change font size of the EDA Options title */
    [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
        font-size: 18px !important; /* Change to your desired font size */
        color: white !important; /* Change to your desired font color */
        text-align: center; /* Center align the text */
    }

    [data-testid="stSidebar"] .stButton:focus {
        outline: none; /* Remove the outline */
        box-shadow: none; /* Remove any box shadow */
    }

    </style>
    """,
    unsafe_allow_html=True
    )


    # Add logo at the top of the sidebar with fixed size and center it
    st.sidebar.image(wlogo, width=200)

    # Title for Data Processing Options below the logo
    st.sidebar.title("Filters")

    if 'selected_type' not in st.session_state:
        st.session_state.selected_type = None
    selected_type = st.sidebar.selectbox("Select Type", df['Type'].unique(), key="sidebar_type")
    st.session_state.selected_type = selected_type
    
    # Dropdown filter to select the Year
    if 'selected_year' not in st.session_state:
        st.session_state.selected_year = None
    
    # Fetch today's date
    today = date.today()
    # Fetch the year from today's date
    if 'current_year' not in st.session_state:
        st.session_state.current_year = None
    current_year = today.year
    st.session_state.current_year = current_year

    # Extracting the year and converting it to int, to compare with current_year
    df_date_table['year'] = df_date_table['year_quarter'].apply(lambda x: x.split()[0]).astype(int)
    year_list = df_date_table['year'].unique()
    year_list = [year for year in year_list if year <= current_year]
    selected_year = st.sidebar.selectbox("Select Year", year_list, key="gp_year_sidebar")
    st.session_state.selected_year = selected_year

    
def create_tabs_gp(gp_name, user_domain):
    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab"] {
            background-color: #001444;
            border-radius: 5px;
            padding: 15px 20px; /* Adjust padding for better spacing */
            margin: 5px;
            font-size: 18px; /* Adjust font size */
            font-family: 'Arial', sans-serif; /* Change font family */
            color: white; /* Non-selected tab text color */
            transition: background-color 0.3s ease; /* Smooth transition for hover effect */
        }
        .stTabs [data-baseweb="tab"]:hover {
            background-color: #FFB401;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #D6E5FD;
            color: black; /* Selected tab text color */
            font-weight: bold; /* Make selected tab bold */
            border-bottom: 3px solid #FFB401; /* Add a bottom border to the selected tab */
        }
        </style>
    """, unsafe_allow_html=True)

    # Create tabs to cover the entire page width
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Consolidated Income Statement", "             ", 
        "Consolidated Balance Sheet", "             ", 
        "Individual Fund Level Details", "             ", 
        "Individual Asset Level Details"
    ])
    
    with tab1:
        st.write("Content for Consolidated Income Statement")
        create_consolidated_income_statement_tab(gp_name, user_domain)
    with tab2:
        pass
    with tab3:
        st.write("Content for Consolidated Balance Sheet")
    with tab4:
        pass
    with tab5:
        st.write("Content for Individual Fund Level Details")
    with tab6:
        pass
    with tab7:
        st.write("Content for Individual Asset Level Details")


def handle_slrcp():
    gp_name = domain_gp_mapping['slrcp.com']
    user_domain = 'slrcp.com'
    create_sidetab_gp(df, df_date_table)
    create_tabs_gp(gp_name, user_domain)
    
def handle_mo():
    gp_name = domain_gp_mapping['mo.com']
    user_domain = 'mo.com'
    create_sidetab_gp(df, df_date_table)
    create_tabs_gp(gp_name, user_domain)

def handle_inflexion():
    gp_name = domain_gp_mapping['inflexion.com']
    user_domain = 'inflexion.com'
    create_sidetab_gp(df, df_date_table)
    create_tabs_gp(gp_name, user_domain)

def handle_vistria():
    gp_name = domain_gp_mapping['vistria.com']
    user_domain = 'vistria.com'
    create_sidetab_gp(df, df_date_table)
    create_tabs_gp(gp_name, user_domain)

def handle_lcatterton():
    gp_name = domain_gp_mapping['lcatterton.com']
    user_domain = 'lcatterton.com'
    create_sidetab_gp(df, df_date_table)
    create_tabs_gp(gp_name, user_domain)


if st.session_state.page == "upload":
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'df_date_table' not in st.session_state:
        st.session_state.df_date_table = None
    df, df_date_table = fetch_data()
    st.session_state.df = df
    st.session_state.df_date_table = df_date_table
    if 'max_id' not in st.session_state:
        st.session_state.max_id = None
    max_id = df['id'].max()
    st.session_state.max_id = max_id
    mapping_df = df[['Category', 'SubCategory', 'KPI']]
    # Replace double spaces with single spaces in all columns
    mapping_df = mapping_df.applymap(lambda x: x.replace('  ', ' ') if isinstance(x, str) else x)
    mapping_df = mapping_df.drop_duplicates()

    matched_domain = check_string_in_email(domain_gp_mapping)
    if matched_domain:
        st.write(f"The string '{matched_domain}' is in the email ID.")
        if matched_domain in domain_gp_mapping:
        # Call specific function based on the matched domain
            if matched_domain == "slrcp.com":
                handle_slrcp()
            elif matched_domain == "mo.com":
                handle_mo()
            elif matched_domain == "inflexion.com":
                handle_inflexion()
            elif matched_domain == "vistria.com":
                handle_vistria()
            elif matched_domain == "lcatterton.com":
                handle_lcatterton()
        else:
            st.write("No matching domain found in the email ID.")



