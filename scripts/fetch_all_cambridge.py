#!/usr/bin/env python3
"""
Official Cambridge IELTS Listening Audio Cloud Ingestion Pipeline
Downloads, verifies, concatenates, and structures official listening tests 
for Cambridge Books 10 through 18.
"""

import os
import sys
import shutil
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
TEMP_DIR = os.path.join(BASE_DIR, "temp_downloads")

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_part_url_candidates(book: int, test: int, part: int):
    """
    Generate candidate URLs for a given book, test, and part.
    Different Cambridge editions use slightly different path conventions on ieltstrainingonline.
    """
    candidates = []
    
    # Cambridge 17 & 18 use 2023/06/cam18-test1-part1.mp3
    if book in (17, 18):
        candidates.append(f"https://ieltstrainingonline.com/wp-content/uploads/2023/06/cam{book}-test{test}-part{part}.mp3")
        candidates.append(f"https://ieltstrainingonline.com/wp-content/uploads/2023/06/Cam{book}-Test{test}-Part{part}.mp3")
        candidates.append(f"https://ieltstrainingonline.com/wp-content/uploads/2023/06/cam{book}-test{test}-section{part}.mp3")
    
    # Cambridge 10-16 use 2021/07/Cam16-Test1-Section1.mp3 or 2021/07/cam16-test1-part1.mp3
    candidates.append(f"https://ieltstrainingonline.com/wp-content/uploads/2021/07/Cam{book}-Test{test}-Section{part}.mp3")
    candidates.append(f"https://ieltstrainingonline.com/wp-content/uploads/2021/07/cam{book}-test{test}-section{part}.mp3")
    candidates.append(f"https://ieltstrainingonline.com/wp-content/uploads/2021/07/Cam{book}-Test{test}-Part{part}.mp3")
    candidates.append(f"https://ieltstrainingonline.com/wp-content/uploads/2021/07/cam{book}-test{test}-part{part}.mp3")
    
    # Backup 2022/2020 variations
    candidates.append(f"https://ieltstrainingonline.com/wp-content/uploads/2020/07/Cam{book}-Test{test}-Section{part}.mp3")
    candidates.append(f"https://ieltstrainingonline.com/wp-content/uploads/2020/07/cam{book}-test{test}-section{part}.mp3")
    
    return candidates

def download_part(book: int, test: int, part: int):
    target_path = os.path.join(TEMP_DIR, f"c{book}_t{test}_p{part}.mp3")
    if os.path.exists(target_path) and os.path.getsize(target_path) > 100000:
        return target_path
    
    candidates = get_part_url_candidates(book, test, part)
    for url in candidates:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=25) as response:
                if response.status == 200:
                    data = response.read()
                    if len(data) > 100000:  # Valid audio payload
                        with open(target_path, "wb") as f:
                            f.write(data)
                        print(f"  ✓ Downloaded Part {part} from {url} ({len(data)} bytes)")
                        return target_path
        except Exception:
            continue
    
    print(f"  ✗ Failed to find audio for Book {book} Test {test} Part {part}")
    return None

def process_test(book: int, test: int):
    out_acad_name = f"c{book}_test{test}_listening.mp3"
    out_acad_alias = f"c{book}-acad-t{test}_listening.mp3"
    out_gen_name = f"c{book}_gen_test{test}_listening.mp3"
    out_gen_alias = f"c{book}-gen-t{test}_listening.mp3"
    
    final_path = os.path.join(AUDIO_DIR, out_acad_name)
    
    # If already built and valid (> 10MB), keep it
    if os.path.exists(final_path) and os.path.getsize(final_path) > 10000000:
        print(f"[*] Cambridge {book} Test {test} already exists ({os.path.getsize(final_path)} bytes).")
        return True

    print(f"\nProcessing Cambridge {book} Test {test}...")
    parts = []
    for part in range(1, 5):
        p_file = download_part(book, test, part)
        if p_file:
            parts.append(p_file)
        else:
            print(f"Skipping Test {test} due to missing part {part}.")
            return False

    if len(parts) == 4:
        print(f"  -> Concatenating 4 parts for Cambridge {book} Test {test}...")
        with open(final_path, "wb") as outfile:
            for p in parts:
                with open(p, "rb") as infile:
                    outfile.write(infile.read())
        
        # Create standard aliases
        shutil.copy2(final_path, os.path.join(AUDIO_DIR, out_acad_alias))
        
        # If book has General Training tests (14-18), create dedicated General copies
        if book >= 14 and test in (1, 2):
            shutil.copy2(final_path, os.path.join(AUDIO_DIR, out_gen_name))
            shutil.copy2(final_path, os.path.join(AUDIO_DIR, out_gen_alias))
            print(f"  -> Created dedicated General Training listening track: {out_gen_name}")
            
        print(f"  ✓ Success! Generated {out_acad_name} ({os.path.getsize(final_path)} bytes)")
        return True
    return False

def main():
    print("=== Starting Official Cambridge IELTS Listening Ingestion (Books 10 - 18) ===")
    success_count = 0
    total_tests = 0
    
    # Books 18 down to 10
    for book in range(18, 9, -1):
        for test in range(1, 5):
            total_tests += 1
            if process_test(book, test):
                success_count += 1
                
    print(f"\n=== Ingestion Completed: {success_count}/{total_tests} Tests Processed Successfully ===")
    # Clean temporary parts
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

if __name__ == "__main__":
    main()
