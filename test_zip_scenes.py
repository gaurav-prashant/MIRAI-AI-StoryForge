import zipfile
import io
import streamlit as st
from utils.image_generator import generate_scene_image, create_scene_images_zip

def test_zip_creation():
    print("============================================================")
    print("RUNNING SCENE IMAGES ZIP ARCHIVE TESTS")
    print("============================================================")

    # 1. Create mock story history for 5 Turns
    mock_history = []
    for turn_num in range(1, 6):
        img_url = generate_scene_image(f"Scene for turn {turn_num}", "Fantasy", "Oakhaven", turn_num)
        mock_history.append({
            "turn": turn_num,
            "scene": f"This is scene text for turn {turn_num}.",
            "choices": ["Choice A", "Choice B"],
            "action": f"Action for turn {turn_num-1}" if turn_num > 1 else None,
            "image_url": img_url
        })

    # 2. Generate ZIP archive
    zip_bytes = create_scene_images_zip(mock_history)
    assert zip_bytes is not None, "ZIP bytes must not be None"
    print("[PASS] ZIP buffer created successfully.")

    # 3. Verify ZIP contents
    zip_buffer = io.BytesIO(zip_bytes)
    with zipfile.ZipFile(zip_buffer, "r") as zf:
        file_list = zf.namelist()
        print(f"[PASS] ZIP Contains {len(file_list)} files: {file_list}")

        assert len(file_list) == 5, f"Expected 5 files in ZIP, found {len(file_list)}"
        for i in range(1, 6):
            expected_name = f"Turn_{i}.png"
            assert expected_name in file_list, f"Missing {expected_name} in ZIP!"
            img_data = zf.read(expected_name)
            assert len(img_data) > 100, f"{expected_name} should contain valid image bytes!"

    print("\nALL SCENE IMAGES ZIP TESTS PASSED WITH 100% SUCCESS!\n")

if __name__ == "__main__":
    test_zip_creation()
