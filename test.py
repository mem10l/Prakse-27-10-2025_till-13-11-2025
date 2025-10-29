import random
from barcode import EAN13
from barcode.writer import ImageWriter

# Generate a 13-digit number as a string
number = random.randint(0, 9999999999999)
number_str = f"{number:013}"  # ensures 13 digits with leading zeros

# Create the barcode
my_code = EAN13(number_str, writer=ImageWriter())

# Save the barcode image
my_code.save("basic_barcode")