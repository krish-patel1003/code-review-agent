import streamlit as st
import requests
import pandas as pd

# API Base URL (adjust if needed)
API_BASE_URL = "http://localhost:8000"

# Initialize session state for tasks
if "tasks" not in st.session_state:
    st.session_state.tasks = []

st.title("Code Review Agent Demo")

# Tab for Analyzing Pull Requests
with st.form("analyze_pr_form"):
    st.subheader("Analyze Pull Request")
    repo_url = st.text_input("Repository URL", help="Provide the GitHub repository URL.")
    pr_number = st.number_input("Pull Request Number", min_value=1, step=1)
    # github_token = st.text_input("GitHub Token (Optional)", type="password")

    submitted = st.form_submit_button("Analyze")
    if submitted:
        # Call the /analyze-pr endpoint
        payload = {"repo_url": repo_url, "pr_number": pr_number}
        try:
            response = requests.post(f"{API_BASE_URL}/analyze-pr", json=payload)
            if response.status_code == 200:
                task_id = response.json().get("task_id")
                st.success(f"Task submitted successfully. Task ID: {task_id}")

                # Add task to the session state
                st.session_state.tasks.append({"Task ID": task_id, "Status": "Pending"})
            else:
                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error: {str(e)}")

# Tab for Checking Task Status
with st.form("check_status_form"):
    st.subheader("Check Task Status")
    status_submitted = st.form_submit_button("Update Task Statuses")
    if status_submitted:
        for task in st.session_state.tasks:
            task_id = task["Task ID"]
            try:
                # Call the /status/{task_id} endpoint
                response = requests.get(f"{API_BASE_URL}/status/{task_id}")
                if response.status_code == 200:
                    task["Status"] = response.json().get("status", "Unknown")
                else:
                    task["Status"] = "Error"
            except requests.exceptions.RequestException:
                task["Status"] = "Error"

# Display the Task Table
st.subheader("Task Table")
if st.session_state.tasks:
    task_df = pd.DataFrame(st.session_state.tasks)
    st.dataframe(task_df, use_container_width=True)
else:
    st.info("No tasks added yet.")

# Tab for Retrieving Task Results
with st.form("get_results_form"):
    st.subheader("Retrieve Task Results")
    task_id = st.text_input("Task ID", help="Provide the task ID to retrieve results.")

    results_submitted = st.form_submit_button("Get Results")
    if results_submitted:
        # Call the /results/{task_id} endpoint
        try:
            response = requests.get(f"{API_BASE_URL}/results/{task_id}")
            if response.status_code == 200:
                results = response.json()
                st.json(results)
            else:
                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error: {str(e)}")
