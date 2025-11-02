import streamlit as st
import json
from parser.all_bank_parser import CreditCardParser

st.set_page_config(page_title="Credit Card Statement Parser", page_icon="💳")
st.title("💳 Credit Card Statement Parser")
st.markdown(
    "Select a credit card provider or upload your own PDF statement to extract data."
)

# --- Predefined bank PDFs ---
# --- Predefined bank PDFs ---
bank_samples = {
    "HDFC": "credit_card_pdfs/hdfc.pdf",
    "ICICI": "credit_card_pdfs/icici.pdf",
    "IDFC": "credit_card_pdfs/idfc.pdf",
    "Axis-Normal": "credit_card_pdfs/axis.pdf",
    "Axis-Image": "credit_card_pdfs/axis-image.pdf",
    "YES Bank": "credit_card_pdfs/yes-bank.pdf"
}


# --- Sidebar: Bank selection ---
selected_bank = st.selectbox("Select a credit card provider", list(bank_samples.keys()))

# --- Optionally upload new PDF ---
uploaded_file = st.file_uploader("Or upload your own PDF", type="pdf")

# Determine which PDF to parse
if uploaded_file:
    pdf_path = uploaded_file
    pdf_name = uploaded_file.name
else:
    pdf_path = bank_samples[selected_bank]
    pdf_name = selected_bank + ".pdf"

if st.button("Parse Statement"):
    with st.spinner(f"Parsing {pdf_name}..."):
        parser = CreditCardParser(pdf_path)
        data = parser.extract_data()

    st.success("✅ Parsing Complete!")

    # --- Show summary ---
    st.subheader("Summary")
    for key, value in data.items():
        if key != "Transactions":
            st.write(f"**{key}:** {value}")

    # --- Download JSON ---
    st.download_button(
        label="Download Extracted Data as JSON",
        data=json.dumps(data, indent=4, ensure_ascii=False),
        file_name=f"{pdf_name}_parsed_data.json",
        mime="application/json"
    )
