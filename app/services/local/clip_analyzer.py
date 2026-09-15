"""CLIP Analyzer - Quantitative similarity scoring using CLIP ViT-B/32."""

from __future__ import annotations

from pathlib import Path


class CLIPAnalyzer:
    """Analyzes shot similarity using CLIP ViT-B/32 (~400MB VRAM)."""

    THRESHOLD_DIALOGUE = 0.78
    THRESHOLD_ACTION = 0.70

    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.device = None
        self._loaded = False

    def _init_device(self):
        import torch
        if self.device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def is_available(self) -> bool:
        return self._loaded

    def load_model(self):
        if self._loaded:
            return
        try:
            from transformers import CLIPModel, CLIPProcessor
            self._init_device()
            self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.preprocessor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.model.to(self.device)
            self._loaded = True
            print("[CLIP] Model loaded successfully")
        except (OSError, RuntimeError) as e:
            print(f"[CLIP] Failed to load model: {e}")
            self._loaded = False

    def extract_keyframe(self, video_path: str, fps: float = 1.0) -> list[str]:
        import cv2

        keyframes: list[str] = []
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return keyframes
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(video_fps / fps) if fps > 0 else int(video_fps)
        frame_interval = max(1, frame_interval)
        frame_count = 0
        saved_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % frame_interval == 0:
                output_dir = Path(video_path).parent / "keyframes" / Path(video_path).stem
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"frame_{saved_count:03d}.jpg"
                cv2.imwrite(str(output_path), frame)
                keyframes.append(str(output_path))
                saved_count += 1
            frame_count += 1
        cap.release()
        return keyframes

    def compute_similarity(self, frame_path: str, reference_path: str) -> float:
        if not self._loaded:
            return 0.0
        try:
            import torch
            from PIL import Image

            self._init_device()
            frame = Image.open(frame_path).convert("RGB")
            reference = Image.open(reference_path).convert("RGB")
            inputs = self.preprocessor(images=[frame, reference], return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = self.model.get_image_features(**inputs)
                frame_features = outputs[0]
                ref_features = outputs[1]
                similarity = torch.cosine_similarity(frame_features, ref_features, dim=0)
            return float(similarity.item())
        except (OSError, RuntimeError, ValueError) as e:
            print(f"[CLIP] Similarity error: {e}")
            return 0.0

    def analyze_shot(self, video_path: str, reference_path: str | None) -> dict:
        keyframes = self.extract_keyframe(video_path)
        if not keyframes:
            return {
                "similarity_score": None,
                "keyframes_extracted": 0,
                "passed_threshold": False,
                "threshold_used": 0,
            }
        if reference_path and Path(reference_path).exists():
            scores = [self.compute_similarity(kf, reference_path) for kf in keyframes[:5]]
            avg_score = sum(scores) / len(scores) if scores else 0.0
        else:
            avg_score = None
        return {
            "similarity_score": avg_score,
            "keyframes_extracted": len(keyframes),
            "passed_threshold": avg_score is not None and avg_score >= self.THRESHOLD_DIALOGUE,
            "threshold_used": self.THRESHOLD_DIALOGUE,
        }
