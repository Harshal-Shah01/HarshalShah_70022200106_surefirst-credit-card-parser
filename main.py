import json
from parser.all_bank_parser import CreditCardParser

if __name__ == "__main__":
    pdf_filename = input("Enter PDF filename (e.g., hdfc.pdf or icici.pdf): ").strip()
    pdf_path = f"credit_card_pdfs/{pdf_filename}"

    parser = CreditCardParser(pdf_path)
    result = parser.extract_data()
    print(json.dumps(result, indent=4, ensure_ascii=False))