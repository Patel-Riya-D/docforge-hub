import streamlit as st
import requests

API_BASE_URL = "http://127.0.0.1:8000"

st.title("Admin - Pending Approvals")

response = requests.get(f"{API_BASE_URL}/approval/pending")
approvals = response.json()

for item in approvals:
    with st.expander(item["document_filename"]):
        st.write("Department:", item["department"])
        st.write("Requested at:", item["requested_at"])

        if st.button(f"Approve {item['request_id']}"):
            requests.post(
                f"{API_BASE_URL}/approval/approve/{item['request_id']}"
            )
            st.success("Approved")
            st.rerun()
