import requests
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_weather_for_slug(slug, retries=2, delay=1):
    """
    Mengambil data cuaca untuk satu pelabuhan berdasarkan slug-nya menggunakan REST API.
    Termasuk mekanisme coba lagi (retry) untuk mengatasi error sementara.
    """
    api_url = f"https://maritim.bmkg.go.id/api/pelabuhan?slug={slug}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(retries + 1):
        try:
            response = requests.get(api_url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            harbor_name = data.get('pelabuhan', slug.replace('-', ' ').title())
            return harbor_name, data.get('prakiraan', [])
        except (requests.exceptions.RequestException, json.JSONDecodeError):
            if attempt < retries:
                time.sleep(delay)  # Menunggu sebelum mencoba lagi
                continue
            else:
                # Gagal setelah semua percobaan
                return None, None

def generate_slug_from_name(name):
    """
    Membuat slug yang valid dari nama pelabuhan.
    Contoh: "Pelabuhan Pomalaa/Dawi-dawi" -> "pelabuhan-pomalaa-dawi-dawi"
    """
    if not isinstance(name, str):
        return ""
    # Konversi ke huruf kecil
    slug = name.lower()
    # Ganti karakter non-alfanumerik dengan tanda hubung
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    # Hapus tanda hubung di awal atau akhir
    slug = slug.strip('-')
    return slug

def parse_bmkg_payload(payload):
    """
    Mem-parsing struktur data JSON yang kompleks dari BMKG untuk mengekstrak slug pelabuhan.
    """
    all_slugs = set()
    try:
        # Data utama adalah sebuah list (payload) yang berfungsi sebagai lookup table.
        # Referensi ke daftar provinsi ada di indeks ke-4 dari payload.
        province_references = payload[4]

        for province_ref in province_references:
            # Dapatkan objek provinsi dari payload menggunakan referensinya
            province_obj = payload[province_ref]
            
            # Dapatkan referensi ke daftar pelabuhan untuk provinsi ini
            ports_references = payload[province_obj['ports']]
            
            for port_ref in ports_references:
                # Dapatkan objek pelabuhan
                port_obj = payload[port_ref]
                
                # Dapatkan nama pelabuhan
                port_name = payload[port_obj['name']]
                
                # Buat slug dari nama pelabuhan
                slug = generate_slug_from_name(port_name)
                if slug:
                    all_slugs.add(slug)
                    
    except (IndexError, KeyError, TypeError) as e:
        print(f"Error saat mem-parsing payload: {e}. Struktur data mungkin telah berubah.")
        return []
        
    return list(all_slugs)

def get_all_harbor_weather():
    """
    Fungsi utama untuk mengambil data cuaca dari semua pelabuhan yang tersedia.
    """
    payload_url = "https://maritim.bmkg.go.id/cuaca/pelabuhan/_payload.json?a72905da-75ea-4547-8cfd-60d9c71cc7f6"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    all_weather_data = {}
    
    try:
        print("Mengambil daftar pelabuhan dari API _payload.json...")
        response = requests.get(payload_url, headers=headers)
        response.raise_for_status()
        payload_data = response.json()
        
        # Mem-parsing payload untuk mendapatkan semua slug
        slugs = parse_bmkg_payload(payload_data)
        
        if not slugs:
            print("Tidak dapat mengekstrak slug pelabuhan dari payload.")
            return None
        
        print(f"Berhasil menemukan {len(slugs)} pelabuhan dari API.")

    except requests.exceptions.RequestException as e:
        print(f"Error saat mengakses _payload.json: {e}")
        return None
    except json.JSONDecodeError:
        print("Gagal mem-parsing JSON dari _payload.json.")
        return None

    # Menggunakan ThreadPoolExecutor untuk membuat permintaan API secara paralel
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_slug = {executor.submit(fetch_weather_for_slug, slug): slug for slug in slugs}
        
        print(f"Memulai pengambilan data cuaca untuk {len(slugs)} pelabuhan...")
        
        for i, future in enumerate(as_completed(future_to_slug)):
            slug = future_to_slug[future]
            try:
                harbor_name, weather_data = future.result()
                if harbor_name and weather_data:
                    all_weather_data[harbor_name] = weather_data
                    print(f"({i+1}/{len(slugs)}) Berhasil mengambil data untuk: {harbor_name}")
                else:
                    print(f"({i+1}/{len(slugs)}) Gagal atau tidak ada data untuk slug: {slug}")
            except Exception as exc:
                print(f"Slug {slug} menghasilkan error: {exc}")

    return all_weather_data

# --- Contoh Penggunaan ---
if __name__ == "__main__":
    print("Memulai proses pengambilan data cuaca maritim BMKG...")
    all_data = get_all_harbor_weather()
    
    if all_data:
        print("\n--- Proses Selesai ---")
        print(f"Total {len(all_data)} data pelabuhan berhasil diambil.")
        
        # Menyimpan hasil ke file JSON
        output_filename = "cuaca_semua_pelabuhan.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
            
        print(f"\nData lengkap telah disimpan ke file: {output_filename}")
        
        # Menampilkan contoh data dari satu pelabuhan
        if all_data:
            first_harbor = next(iter(all_data))
            print(f"\nContoh data untuk '{first_harbor}':")
            print(json.dumps(all_data[first_harbor][:2], indent=2, ensure_ascii=False))
