from transformers import pipeline
from PIL import Image

# 모델을 한 번만 로드
model = pipeline("image-classification", model="falconsai/nsfw_image_detection")

def detect_nsfw_from_image(image_path: str) -> dict:
    image = Image.open(image_path)

    results = model(image)
    best_prediction = max(results, key=lambda x: x["score"])
    confidence_percentage = round(best_prediction["score"] * 100, 1)

    return {
        "is_nsfw": best_prediction["label"] == "nsfw",
        "confidence_percentage": confidence_percentage
    }
