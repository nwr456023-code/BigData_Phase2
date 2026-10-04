import re

class QualityRules:
    @staticmethod
    def clean_arabic_numbers(value):
        if not value or not isinstance(value, str):
            return value, None
        arabic_to_latin = {'٠':'0', '١':'1', '٢':'2', '٣':'3', '٤':'4', '٥':'5', '٦':'6', '٧':'7', '٨':'8', '٩':'9'}
        cleaned = "".join([arabic_to_latin.get(ch, ch) for ch in str(value)])
        if cleaned != value:
            return cleaned, {"rule_code": "ARABIC_NUMBERS_CONVERTED", "original": value, "corrected": cleaned}
        return value, None

    @staticmethod
    def clean_currency(value):
        if not value or not isinstance(value, str):
            return value, None
        original = value
        cleaned = re.sub(r'(ريال يمني|لاير|YER|Rial|ريال)', '', value, flags=re.IGNORECASE).strip()
        if cleaned != original:
            return cleaned, {"rule_code": "CURRENCY_NORMALIZED", "original": original, "corrected": cleaned}
        return value, None

    @staticmethod
    def clean_thousands_separator(value):
        if not value or not isinstance(value, str):
            return value, None
        original = value
        cleaned = re.sub(r'[,،]', '', value).strip()
        if cleaned != original:
            return cleaned, {"rule_code": "THOUSANDS_SEPARATOR_REMOVED", "original": original, "corrected": cleaned}
        return value, None

    @staticmethod
    def clean_phone(value):
        if not value or not isinstance(value, str):
            return value, None
        original = value
        cleaned = re.sub(r'[\s\-\+]', '', value)
        if cleaned.startswith('0'):
            cleaned = '967' + cleaned[1:]
        if cleaned != original:
            return cleaned, {"rule_code": "PHONE_NORMALIZED", "original": original, "corrected": cleaned}
        return value, None

    @staticmethod
    def clean_email(value):
        if not value or not isinstance(value, str):
            return value, None
        original = value
        cleaned = re.sub(r'@+', '@', value)
        cleaned = re.sub(r'\.+', '.', cleaned)
        if cleaned != original:
            return cleaned, {"rule_code": "EMAIL_SYMBOLS_REPAIRED", "original": original, "corrected": cleaned}
        return value, None

    @classmethod
    def process_record(cls, row):
        corrections = []
        cleaned_row = row.copy()
        
        for field in ['price', 'total_amount']:
            if field in cleaned_row and cleaned_row[field]:
                v, err = cls.clean_arabic_numbers(cleaned_row[field])
                if err: 
                    err['field'] = field
                    corrections.append(err)
                cleaned_row[field] = v
                
                v, err = cls.clean_currency(cleaned_row[field])
                if err: 
                    err['field'] = field
                    corrections.append(err)
                cleaned_row[field] = v
                
                v, err = cls.clean_thousands_separator(cleaned_row[field])
                if err: 
                    err['field'] = field
                    corrections.append(err)
                cleaned_row[field] = v

        if 'phone' in cleaned_row and cleaned_row['phone']:
            v, err = cls.clean_phone(cleaned_row['phone'])
            if err: 
                err['field'] = 'phone'
                corrections.append(err)
            cleaned_row['phone'] = v

        if 'email' in cleaned_row and cleaned_row['email']:
            v, err = cls.clean_email(cleaned_row['email'])
            if err: 
                err['field'] = 'email'
                corrections.append(err)
            cleaned_row['email'] = v

        quarantine_reasons = []
        if not cleaned_row.get('order_id'):
            quarantine_reasons.append("ID_ORDER_MISSING")
        if not cleaned_row.get('customer_id'):
            quarantine_reasons.append("ID_CUSTOMER_MISSING")

        if quarantine_reasons:
            status = "quarantined"
        elif corrections:
            status = "corrected"
        else:
            status = "valid"

        return cleaned_row, status, corrections, quarantine_reasons