"""Migration script: Upload existing local files to Supabase Storage and update DB references"""
import os
import re
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
BUCKET = "pipeline-assets"
UPLOADS_DIR = "/app/backend/uploads/pipeline"

s = create_client(SUPABASE_URL, SUPABASE_KEY)

# Step 1: Upload all local files to Supabase Storage
uploaded = {}  # old_path -> new_url
for root, dirs, files in os.walk(UPLOADS_DIR):
    for fname in files:
        local_path = os.path.join(root, fname)
        rel = os.path.relpath(local_path, UPLOADS_DIR)
        # Determine storage path
        if "assets" in root:
            storage_path = f"assets/{fname}"
        else:
            storage_path = fname

        old_url = f"/api/uploads/pipeline/{rel}"
        
        with open(local_path, "rb") as f:
            data = f.read()
        
        ext = os.path.splitext(fname)[1].lower()
        ct_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
        ct = ct_map.get(ext, "application/octet-stream")
        
        try:
            s.storage.from_(BUCKET).upload(storage_path, data, file_options={"content-type": ct, "upsert": "true"})
            new_url = s.storage.from_(BUCKET).get_public_url(storage_path)
            uploaded[old_url] = new_url
            print(f"  OK: {old_url} -> {new_url[:60]}...")
        except Exception as e:
            print(f"  FAIL: {old_url} -> {e}")

print(f"\nUploaded {len(uploaded)} files to Supabase Storage")

# Step 2: Update campaigns table - image URLs in metrics.stats.images
campaigns = s.table("campaigns").select("id, metrics").execute().data or []
updated_campaigns = 0
for c in campaigns:
    metrics = c.get("metrics") or {}
    stats = metrics.get("stats") or {}
    images = stats.get("images") or []
    changed = False
    new_images = []
    for img_url in images:
        if img_url in uploaded:
            new_images.append(uploaded[img_url])
            changed = True
        else:
            new_images.append(img_url)
    
    if changed:
        stats["images"] = new_images
        metrics["stats"] = stats
        s.table("campaigns").update({"metrics": metrics}).eq("id", c["id"]).execute()
        updated_campaigns += 1
        print(f"  Campaign {c['id'][:8]}: updated {sum(1 for i in images if i in uploaded)} image URLs")

print(f"\nUpdated {updated_campaigns} campaigns")

# Step 3: Update pipelines table - image URLs in steps.lucas_design.image_urls
pipelines = s.table("pipelines").select("id, steps").execute().data or []
updated_pipelines = 0
for p in pipelines:
    steps = p.get("steps") or {}
    lucas = steps.get("lucas_design") or {}
    urls = lucas.get("image_urls") or []
    changed = False
    new_urls = []
    for u in urls:
        if u in uploaded:
            new_urls.append(uploaded[u])
            changed = True
        else:
            new_urls.append(u)
    
    if changed:
        lucas["image_urls"] = new_urls
        steps["lucas_design"] = lucas
        s.table("pipelines").update({"steps": steps}).eq("id", p["id"]).execute()
        updated_pipelines += 1
        print(f"  Pipeline {p['id'][:8]}: updated {sum(1 for u in urls if u in uploaded)} image URLs")

print(f"\nUpdated {updated_pipelines} pipelines")
print(f"\n=== Migration complete ===")
print(f"Files uploaded: {len(uploaded)}")
print(f"Campaigns updated: {updated_campaigns}")
print(f"Pipelines updated: {updated_pipelines}")
