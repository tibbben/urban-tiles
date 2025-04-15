import os
import requests

# --- CONFIGURATION ---
API_KEY = '<API KEY>' 
TILE_TYPE = 'airports'      # Change to 'local', 'score', or 'traffic' if needed
BASE_DIR = 'tiles'
API_BASE_URL = 'https://api.howloud.com/tiles'

# --- MAIN FUNCTION ---
def download_tiles():
    headers = {'x-api-key': API_KEY}

    for z in os.listdir(BASE_DIR):
        z_path = os.path.join(BASE_DIR, z)
        if not os.path.isdir(z_path):
            continue

        for y in os.listdir(z_path):
            y_path = os.path.join(z_path, y)
            if not os.path.isdir(y_path):
                continue

            for x_file in os.listdir(y_path):
                if not x_file.endswith('.png'):
                    continue

                x = x_file[:-4]  # remove '.png'
                tile_url = f"{API_BASE_URL}/{TILE_TYPE}/{z}/{x}/{y}.png"
                tile_path = os.path.join(y_path, x_file)

                print(f"Requesting: {tile_url}")

                try:
                    r = requests.get(tile_url, headers=headers)
                    r.raise_for_status()
                    with open(tile_path, 'wb') as f:
                        f.write(r.content)
                    print(f"Downloaded tile to: {tile_path}")
                except requests.exceptions.RequestException as e:
                    print(f"Failed to download {tile_url}: {e}")

if __name__ == '__main__':
    download_tiles()
