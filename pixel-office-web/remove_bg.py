import sys
from PIL import Image

def remove_white_bg(input_path, output_path):
    try:
        img = Image.open(input_path).convert("RGBA")
        datas = img.getdata()
        
        newData = []
        for item in datas:
            # White or near-white background removal
            if item[0] > 230 and item[1] > 230 and item[2] > 230:
                newData.append((255, 255, 255, 0))
            else:
                newData.append(item)
                
        img.putdata(newData)
        img.save(output_path, "PNG")
        print(f"Saved: {output_path}")
    except Exception as e:
        print(f"Error processing {input_path}: {e}")

if __name__ == "__main__":
    remove_white_bg(sys.argv[1], sys.argv[2])
