from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHOTOS = (ROOT / "site" / "run-photos.js").read_text()
INDEX = (ROOT / "site" / "index.html").read_text()


def test_photo_ui_uses_bearer_fetch_and_blob_urls():
    assert "/api/run-photos?run_id=" in PHOTOS
    assert "function photoPath(photo)" in PHOTOS
    assert 'searchParams.get("id")' in PHOTOS and 'searchParams.get("run_id")' in PHOTOS
    assert "fetch(path" in PHOTOS
    assert "Authorization=`Bearer ${t}`" in PHOTOS
    assert "URL.createObjectURL(await imageRes.blob())" in PHOTOS
    assert "?access_token=" not in PHOTOS and "&access_token=" not in PHOTOS


def test_photo_ui_crops_and_compresses_before_upload():
    assert "canvas.toBlob" in PHOTOS
    assert "image/jpeg" in PHOTOS
    assert "3*1024*1024" in PHOTOS
    assert "JSON.stringify({run_id:run.id,image_base64:base64})" in PHOTOS
    assert "method:'DELETE'" in PHOTOS
    assert "photos.length<6" in PHOTOS
    assert "Six photos added" in PHOTOS
    assert 'accept="image/jpeg,image/png,image/webp"' in PHOTOS
    assert "Original" in PHOTOS and "Square" in PHOTOS and "Wide" in PHOTOS
    assert "ready:false" in PHOTOS
    assert "data-photo-upload disabled" in PHOTOS
    assert "state.ready=true" in PHOTOS


def test_run_page_mounts_photos_for_reader_and_owner_controls():
    assert '<section id="run-photos"></section>' in INDEX
    assert "StriveRunPhotos.mount({client:sb,run:r,slot:$('run-photos'),owner,status})" in INDEX
    assert "/run-photos.js" in INDEX and "/run-photos.css" in INDEX
    assert 'href="#run-photos">Add photos</a>' in INDEX


def test_feed_cards_load_managed_photo_cover_without_token_query():
    assert "async function mountCovers" in PHOTOS
    assert ".fc[data-run-id]" in PHOTOS
    assert "payload?.photos?.[0]" in PHOTOS
    assert "StriveRunPhotos.mountCovers({client:sb,root:document})" in INDEX
