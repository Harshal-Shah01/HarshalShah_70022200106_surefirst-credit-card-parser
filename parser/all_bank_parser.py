import pdfplumber
import re
from PIL import Image
import pytesseract

# Set Tesseract executable path 
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class CreditCardParser:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.ocr_fallback = False
        self.text = self._extract_text()
        self.bank = self._detect_bank()

    def _extract_text(self):
        text = ""

        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        if not text.strip():
            self.ocr_fallback = True
            print("No text detected, using OCR fallback...")
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    image = page.to_image(resolution=300).original
                    page_text = pytesseract.image_to_string(image)
                    text += page_text + "\n"
        return text

    def _detect_bank(self):
        text_upper = self.text.upper()
        if "HDFC" in text_upper:
            return "HDFC"
        elif "ICICI" in text_upper:
            return "ICICI"
        elif "AXIS" in text_upper:
            return "AXIS"
        elif "YES BANK" in text_upper:
            return "YES BANK"
        elif "IDFC" in text_upper:
            return "IDFC"
        else:
            return "Unknown"

    def extract_data(self):
        if self.bank == "HDFC":
            result = self._extract_hdfc()
        elif self.bank == "ICICI":
            result = self._extract_icici()
        elif self.bank == "AXIS":
            result = self._extract_axis()
        elif self.bank == "YES BANK":
            result = self._extract_yesbank()
        elif self.bank == "IDFC":
            result = self._extract_idfc()
        else:
            return {"Error": "Unknown bank format"}

        result["OCR_Fallback"] = self.ocr_fallback
        return result

        
    def extract_data_with_ocr_flag(self):
        return self.extract_data(), self.ocr_fallback

    def _extract_hdfc(self):
        text = self.text

        card_last_4 = re.search(
            r'Card\s*No[:\-]?\s*\d{4}\s*\d{2}[Xx*]{2}\s*[Xx*]{4}\s*(\d{4})', 
            text
        )

        payment_due_date = re.search(
            r'Payment\s*Due\s*Date[\s\S]{0,500}?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            text,
            re.IGNORECASE
        )
        if not payment_due_date:
            match = re.search(r'Due\s+Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
            if match:
                payment_due_date = match.group(1)

        total_due = re.search(
            r'Total\s+Dues[\s\S]{0,200}?(?:0[\s\n]*)*([\d]{1,2},\d{3}\.\d{2}|\d{1,3}(?:,\d{3})*(?:\.\d{2}))',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if not total_due:
            total_due = re.search(
                r'Total\s+Amount\s+Due[\s\S]{0,200}?(?:0[\s\n]*)*([\d,]+\.\d{2})',
                text, 
                re.IGNORECASE
        )
            
        statement_date = re.search(
            r'Statement\s+Date\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})', text
        )
        name = re.search(r'Name\s*[:\-]?\s*([A-Z\s]+)', text)
        if not name:
            name = re.search(r'rd\s+([A-Z][A-Z\s]+)\s+Statement', text)

        return {
            "Bank": "HDFC",
            "Name": name.group(1).title().strip() if name else None,
            "Card_Last_4": card_last_4.group(1) if card_last_4 else None,
            "Statement_Date": statement_date.group(1) if statement_date else None,
            "Payment_Due_Date": payment_due_date.group(1) if payment_due_date else None,
            "Total_Due": total_due.group(1).strip() if total_due else None,
            "OCR_Fallback": self.ocr_fallback
        }

    def _extract_icici(self):
        text = self.text

        card_match = re.search(r'(\d{4})X{4,}X{4,}(\d{4})', text)
        card_last_4 = card_match.group(2) if card_match else None

        total_due = None
        header_match = re.search(r'Total\s+Amount\s+due', text, re.IGNORECASE)
        if header_match:
            after_header = text[header_match.end():]
            amount_match = re.search(r'[`₹]?\s*([\d,]+\.\d{2})', after_header)
            if amount_match:
                total_due = '₹' + amount_match.group(1)

        statement_date_match = re.search(
            r'([A-Za-z]+\s+\d{1,2},\s*\d{4})', text
        )
        statement_date = statement_date_match.group(1).strip() if statement_date_match else None


        due_date_match = re.search(
            r'Payment\s*Due\s*(?:Date)?[^\n]*\n?\s*([A-Za-z]+\s+\d{1,2},\s*\d{4})',
            text,
            re.IGNORECASE
        )
        payment_due_date = due_date_match.group(1).strip() if due_date_match else None

        name_match = re.search(r'\b(MR|MRS|MS)\.?\s+([A-Z\s]+)', text)
        if name_match:
            name = f"{name_match.group(1)} {name_match.group(2).strip()}"
        else:
            alt_name = re.search(r'Name\s*[:\-]?\s*([A-Z][A-Z\s]+)', text)
            name = alt_name.group(1).strip() if alt_name else None
        if name:
            name = name.split("\n")[0].strip()

        return {
            "Bank": "ICICI",
            "Name": name,
            "Card_Last_4": card_last_4,
            "Statement_Date": statement_date,
            "Payment_Due_Date": payment_due_date,
            "Total_Due": total_due,
            "OCR_Fallback": self.ocr_fallback
        }

    def _extract_axis(self):
        text = self.text

        card_match = re.search(r'(\d{4})\*{4,}\s*(\d{4})', text)
        card_last_4 = card_match.group(2) if card_match else None

        total_due_match = re.search(r'Total\s+Payment\s+Due[^\d]*([\d,]+\.\d{2})', text, re.IGNORECASE)
        total_due = '₹' + total_due_match.group(1) if total_due_match else None

        name = None
        for line in text.split("\n"):
            if "Card No" in line:
                name_match = re.search(r'Name[:\s]*([A-Z][A-Z\s]+)', line)
                if name_match:
                    name = name_match.group(1).title().strip()
                    break
        if not name:
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            for l in lines:
                words = l.split()
                if len(words) >= 2 and all(w.isupper() or w.isdigit() for w in words):
                    name = l.title().strip()
                    break

        statement_date = None
        payment_due_date = None
        all_dates = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', text)
        if all_dates:
            if len(all_dates) >= 2:
                statement_date = all_dates[1]
            if len(all_dates) >= 3:
                payment_due_date = all_dates[2]

        return {
            "Bank": "AXIS",
            "Name": name,
            "Card_Last_4": card_last_4,
            "Statement_Date": statement_date,
            "Payment_Due_Date": payment_due_date,
            "Total_Due": total_due,
            "OCR_Fallback": self.ocr_fallback
        }


    def _extract_yesbank(self):
        text = self.text

        card_match = re.search(r'\b\d{4}X{6,8}(\d{4})\b', text)
        card_last_4 = card_match.group(1) if card_match else None

        total_due_line = re.search(r'Total\s+Amount\s+Due[:\s]*', text, re.IGNORECASE)
        total_due = None
        if total_due_line:
            remaining_text = text[total_due_line.end():].strip()
            for line in remaining_text.splitlines():
                match = re.search(r'Rs\.?\s*([\d,]+\.\d{2})', line)
                if match:
                    total_due = '₹' + match.group(1)
                    break

        statement_date_match = re.search(r'Statement\s+Date[:\s]*([0-9]{2}/[0-9]{2}/[0-9]{4})', text)
        statement_date = statement_date_match.group(1) if statement_date_match else None

        payment_due_date_match = re.search(r'Payment\s+Due\s+Date[:\s]*([0-9]{2}/[0-9]{2}/[0-9]{4})', text)
        payment_due_date = payment_due_date_match.group(1) if payment_due_date_match else None

        name_match = re.search(r'\n([A-Z][A-Z\s]+)\nNO\s+\d', text)
        name = name_match.group(1).title().strip() if name_match else None

        return {
            "Bank": "YES BANK",
            "Name": name,
            "Card_Last_4": card_last_4,
            "Statement_Date": statement_date,
            "Payment_Due_Date": payment_due_date,
            "Total_Due": total_due,
            "OCR_Fallback": self.ocr_fallback
        }

    def _extract_idfc(self):
        text = self.text

        name = None
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        start_index = 0
        for i, line in enumerate(lines):
            if "Credit Card Statement" in line:
                start_index = i + 1
                break
        for line in lines[start_index:]:
            if re.match(r'^[A-Za-z\s]+$', line):
                name = line.title().strip()
                break

        card_last_4 = None
        card_match = re.search(r'Card\s+Number[:\s]*X{2,}\s*(\d{4})', text, re.IGNORECASE)
        if card_match:
            card_last_4 = card_match.group(1)

        total_due = None
        total_due_match = re.search(
            r'Total\s+Amount\s+Due.*?([rR]?[\d,]+\.\d{2})\s*(CR|DR)?', 
            text, 
            re.IGNORECASE | re.DOTALL
        )
        if total_due_match:
            amount = total_due_match.group(1).replace('r', '').replace('R', '').replace(',', '').strip()
            credit_type = total_due_match.group(2)
            total_due = f'₹{amount}'
            if credit_type:
                total_due += f' {credit_type.upper()}'

        statement_date = None
        statement_date_match = re.search(r'Statement\s+Date[:\s]*([0-9]{2}/[0-9]{2}/[0-9]{4})', text, re.IGNORECASE)
        if statement_date_match:
            statement_date = statement_date_match.group(1)

        payment_due_date = None
        payment_due_date_match = re.search(r'Payment\s+Due\s+Date[:\s]*([0-9]{2}/[0-9]{2}/[0-9]{4})', text, re.IGNORECASE)
        if payment_due_date_match:
            payment_due_date = payment_due_date_match.group(1)

        return {
            "Bank": "IDFC FIRST Bank",
            "Name": name,
            "Card_Last_4": card_last_4,
            "Statement_Date": statement_date,
            "Payment_Due_Date": payment_due_date,
            "Total_Due": total_due,
            "OCR_Fallback": self.ocr_fallback
        }