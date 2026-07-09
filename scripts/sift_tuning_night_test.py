import json
import time
from pathlib import Path
import cv2
import numpy as np
from amazon_search.imagecache import local_path

def get_inliers(img1_path, img2_path):
    try:
        img1 = cv2.imread(img1_path)
        img2 = cv2.imread(img2_path)
        if img1 is None or img2 is None: return 0
        
        # Ridimensiona se troppo grandi (come fa app.py)
        h, w = img1.shape[:2]
        if w > 800 or h > 800:
            scale = 800 / max(w, h)
            img1 = cv2.resize(img1, (int(w*scale), int(h*scale)))
        h, w = img2.shape[:2]
        if w > 800 or h > 800:
            scale = 800 / max(w, h)
            img2 = cv2.resize(img2, (int(w*scale), int(h*scale)))

        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        sift = cv2.SIFT_create(400)
        k1, d1 = sift.detectAndCompute(gray1, None)
        k2, d2 = sift.detectAndCompute(gray2, None)
        
        if d1 is None or d2 is None or len(k1) < 4:
            return 0
            
        pairs = cv2.BFMatcher(cv2.NORM_L2).knnMatch(d1, d2, k=2)
        good = []
        for match_group in pairs:
            if len(match_group) == 2:
                m, n = match_group
                if m.distance < 0.7 * n.distance:
                    good.append(m)
        
        if len(good) < 5:
            return len(good)
            
        src_pts = np.float32([k1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([k2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        
        if mask is not None:
            return int(np.sum(mask))
        return 0
    except Exception as e:
        return 0

def main():
    print("Avvio TEST INTENSIVO NOTTURNO: Tuning Image Detector (SIFT)")
    
    downloads = Path(rstr(Path.home() / "Downloads"))
    test_images = [
        downloads / "immagine con coso O.jpg",
        downloads / "immagine con coso X.jpg",
        downloads / "immaagine con coso X (1).webp",
        downloads / "immaagine con coso Y.webp",
        downloads / "immaagine con coso Z.webp",
        Path(rstr(Path.home() / ".claude", "jobs", "91d6642c", "tmp", "cosoO_amazon.jpg"))
    ]
    test_images = [p for p in test_images if p.exists()]
    print(f"Trovate {len(test_images)} immagini test ('coso').")
    # Carica il dataset Amazon
    offline_file = Path.home() / ".amazon_search_offline.json"
    all_asins = set()
    if offline_file.exists():
        try:
            data = json.loads(offline_file.read_text('utf-8'))
            for p in data.get('products', []):
                if p.get('asin'):
                    all_asins.add(p['asin'])
        except Exception: pass
            
    asins = list(all_asins)
    print(f"Trovati {len(asins)} prodotti Amazon unici nel dataset.")
    
    log_file = Path("sift_tuning_matrix.csv")
    with log_file.open("w", encoding="utf-8") as out:
        out.write("TEST_IMAGE,AMAZON_ASIN,THRESHOLD_5,THRESHOLD_10,THRESHOLD_15,THRESHOLD_20,THRESHOLD_25,THRESHOLD_30\n")
        
    print("Inizio iterazione su tutte le combinazioni (andrà avanti a lungo)...")
    total = len(test_images) * len(asins)
    count = 0
    
    for test_img in test_images:
        print(f"\n=> Analisi immagine test: {test_img.name}")
        for a in asins:
            amz_img = local_path(a)
            if not amz_img or not Path(amz_img).exists(): continue
            
            count += 1
            if count % 50 == 0:
                print(f"Progresso: {count}/{total} combinazioni testate...")
                
            inliers = get_inliers(str(test_img), str(amz_img))
            if inliers >= 5:
                with log_file.open("a", encoding="utf-8") as out:
                    t5 = "PASS" if inliers >= 5 else "FAIL"
                    t10 = "PASS" if inliers >= 10 else "FAIL"
                    t15 = "PASS" if inliers >= 15 else "FAIL"
                    t20 = "PASS" if inliers >= 20 else "FAIL"
                    t25 = "PASS" if inliers >= 25 else "FAIL"
                    t30 = "PASS" if inliers >= 30 else "FAIL"
                    out.write(f"{test_img.name},{a},{t5},{t10},{t15},{t20},{t25},{t30} ({inliers} inliers)\n")
                
    print("Test completato. I risultati sono salvati in sift_tuning_matrix.csv")

if __name__ == "__main__":
    main()
