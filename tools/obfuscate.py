import csv
import sys
import os
import random
import re
from decimal import Decimal

def randomize_value(val_str, min_val=1, max_val=1000, decimals=2):
    """Generates a random decimal maintaining the sign of the original."""
    val_str = val_str.strip()
    if not val_str:
        return None
    
    try:
        # Remove existing commas to parse
        orig_val = float(val_str.replace(',', ''))
    except ValueError:
        return None

    if orig_val == 0:
        return Decimal("0.00")

    # Generate random magnitude
    new_mag = random.uniform(min_val, max_val)
    
    # Preserve sign
    if orig_val < 0:
        new_mag = -new_mag

    # Round
    return Decimal(f"{new_mag:.{decimals}f}")

def obfuscate(input_path):
    filename = os.path.basename(input_path)
    
    # Obfuscate Filename
    if "History_for_Account_" in filename:
        new_account_id = f"TEST{random.randint(1000, 9999)}"
        new_filename = f"History_for_Account_{new_account_id}.csv"
    else:
        new_filename = "obfuscated_" + filename

    output_path = os.path.join(os.path.dirname(input_path), new_filename)

    # Regex patterns
    account_pattern = re.compile(r'\b[A-Z0-9]+-\d+-\d\b')
    dd_pattern = re.compile(r"(DIRECT DEPOSIT ).*")

    # Initialize a random starting balance (e.g., $50,000)
    running_balance = Decimal(random.uniform(10000, 100000)).quantize(Decimal("0.01"))

    with open(input_path, 'r', encoding='utf-8-sig', newline='') as f_in, \
         open(output_path, 'w', encoding='utf-8', newline='') as f_out:
        
        reader = csv.reader(f_in)
        writer = csv.writer(f_out)

        for row in reader:
            # Header
            if not row or row[0] == "Run Date":
                writer.writerow(row)
                continue
            
            # Footer
            if len(row) < 13:
                continue

            # --- TEXT SCRUBBING ---
            if row[1]:
                row[1] = account_pattern.sub("XXX-XXXXXX-X", row[1])
                row[1] = dd_pattern.sub(r"\1OBFUSCATED_SOURCE", row[1])

            row[3] = "OBFUSCATED DESCRIPTION"

            # --- SANE MATH GENERATION ---

            # 1. Quantity (Column 5)
            # Only randomize if it exists (some rows like Interest don't have qty)
            qty = randomize_value(row[5], min_val=1, max_val=100, decimals=3)
            if qty is not None:
                row[5] = str(qty)

            # 2. Price (Column 6)
            price = randomize_value(row[6], min_val=10, max_val=200, decimals=2)
            if price is not None:
                row[6] = str(price)

            # 3. Fees/Commission/Interest (Cols 7, 8, 9) - Randomize independently
            # (Keeping these simple for now)
            for idx in [7, 8, 9]:
                val = randomize_value(row[idx], min_val=0, max_val=5, decimals=2)
                if val is not None:
                    row[idx] = str(val)

            # 4. Amount (Column 10)
            # If we have Qty and Price, calculate Amount = Qty * Price
            # Otherwise, randomize Amount directly (e.g. for simple transfers)
            if qty is not None and price is not None:
                # Math: Amount = Qty * Price
                # Important: In Fidelity, if you BUY, Amount is usually Negative.
                # If Qty is + and Price is +, Amount should be -.
                # We need to respect the sign of the *original* Amount to know if it's Inflow or Outflow.
                
                original_amount_sign = 1.0
                try:
                    if float(row[10].replace(',', '')) < 0:
                        original_amount_sign = -1.0
                except:
                    pass
                
                # Force amount to be magnitude of (Qty * Price) * original_sign
                calc_amount = (abs(qty) * abs(price)) * Decimal(original_amount_sign)
                calc_amount = calc_amount.quantize(Decimal("0.01"))
                row[10] = str(calc_amount)
            else:
                # No Qty/Price? Just randomize the existing amount
                amt = randomize_value(row[10], min_val=10, max_val=1000, decimals=2)
                if amt is not None:
                    row[10] = str(amt)
            
            # 5. Running Cash Balance (Column 11)
            # Update running balance based on the new Amount
            try:
                current_tx_amount = Decimal(row[10])
                running_balance += current_tx_amount
                row[11] = str(running_balance)
            except:
                row[11] = "0.00"

            writer.writerow(row)

    print(f"Done! Created: {new_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 tools/obfuscate.py <path_to_csv>")
        sys.exit(1)
    
    obfuscate(sys.argv[1])
