import os

# --- CONFIGURATION ---
with open('key.txt', 'r') as key_file:
    API_KEY = key_file.read().strip()

TILE_TYPE = 'airports'      # Change to 'local', 'score', or 'traffic' if needed
BASE_DIR = 'tiles'
API_BASE_URL = 'https://api.howloud.com/tiles'

# --- MAIN FUNCTION ---
def dry_run_tiles():
    print("=== Dry Run: Listing API Requests ===\n")

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
                tile_url = f"{API_BASE_URL}/{TILE_TYPE}/{z}/{y}/{x}.png"
                tile_path = os.path.join(y_path, x_file)

                print(f"URL:  {tile_url}")
                print(f"Save: {tile_path}")
                print("-" * 60)

if __name__ == '__main__':
    dry_run_tiles()
