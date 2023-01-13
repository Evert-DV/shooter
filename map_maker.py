import PIL
from PIL import Image

# Open the image file
im = Image.open("Map imgs/level2.png")

# Convert the image to grayscale
# im = im.convert("L")

with open("maps/Map4.txt", 'w') as f:
    # Iterate over each row of pixels
    for y in range(im.height):
        # Initialize an empty string for the current row
        row_string = ""
        for x in range(im.width):
            # Get the value of the pixel (0 is black, 255 is white)
            pixel = im.getpixel((x, y))
            if pixel == (0, 0, 0):
                row_string += "1"
            elif pixel == (128, 128, 128):
                row_string += "P"
            elif pixel == (255, 0, 0):
                row_string += "M"
            elif pixel == (128, 0, 128):
                row_string += "B"
            else:
                row_string += "."
        # Add the row string to the list
        f.write(f"{row_string}\n")
