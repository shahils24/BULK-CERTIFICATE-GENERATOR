from PIL import Image, ImageDraw, ImageFont
import os, pandas as pd, re, zipfile, shutil

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def generate_certificates(csv_path, img_path, font_path, column, x, y, size, hex_color, base_temp):
    data = pd.read_csv(csv_path)
    total = len(data)
    font = ImageFont.truetype(font_path, int(size))
    rgb_color = hex_to_rgb(hex_color)
    
    # Path setup
    output_dir = os.path.join(base_temp, "output")
    
    # Clean and recreate output directory to ensure a fresh batch
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    for index, row in data.iterrows():
        name = str(row[column]).strip()
        with Image.open(img_path).convert("RGB") as cert:
            draw = ImageDraw.Draw(cert)
            
            # Center-point calculation
            bbox = draw.textbbox((0, 0), name, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            
            rx = (cert.width * float(x)) - (w / 2)
            ry = (cert.height * float(y)) - (h / 2)
            
            draw.text((rx, ry), name, fill=rgb_color, font=font)
            
            # Filename safety
            safe_name = re.sub(r'[\\/*?:"<>|]', "", name)
            cert.save(os.path.join(output_dir, f"{index+1}_{safe_name}.png"))
            
            yield {"current": index+1, "total": total, "name": name, "done": False}

    # Save the final ZIP inside the base_temp directory
    zip_path = os.path.join(base_temp, "certificates.zip")
    with zipfile.ZipFile(zip_path, "w") as z:
        for f in os.listdir(output_dir):
            file_path = os.path.join(output_dir, f)
            z.write(file_path, arcname=f)
            
    yield {"current": total, "total": total, "name": "Finished", "done": True}
