import csv
import random

def generate_sample_csv(filename="data/sample_orders.csv", num_rows=200):
    headers = ["order_id", "customer_id", "phone", "price", "email"]
    
    currencies = ["ريال يمني", "YER", "Rial", ""]
    arabic_nums = {'0':'٠', '1':'١', '2':'٢', '3':'٣', '4':'٤', '5':'٥', '6':'٦', '7':'٧', '8':'٨', '9':'٩'}

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for i in range(1, num_rows + 1):
            order_id = f"ORD-{i:04d}" if i % 15 != 0 else "" 
            customer_id = f"CUST-{random.randint(100, 999)}"
            phone = f"077{random.randint(100000, 999999)}"
            email = f"user{i}@@example..com" if i % 3 == 0 else f"user{i}@example.com"
            raw_price = f"{random.randint(1000, 5000)} {random.choice(currencies)}"
            
            if i % 2 == 0:
                raw_price = "".join([arabic_nums.get(ch, ch) for ch in raw_price])
                
            writer.writerow([order_id, customer_id, phone, raw_price, email])

    print(f"تم إنشاء ملف البيانات التجريبي: {filename}")

if __name__ == "__main__":
    generate_sample_csv()