"""Florence Analyzer - Object detection, captioning, and visual grounding."""

import gc
from typing import ClassVar


class FlorenceAnalyzer:
    """Analyzes shots using Florence-2-base (~800MB-1.2GB VRAM)."""

    KEY_PROPS: ClassVar[dict[str, list[str]]] = {
        "sword": ["sword", "katana", "blade", "weapon"],
        "cloak": ["cloak", "cape", "robe"],
        "scar": ["scar", "mark", "wound"],
        "headband": ["headband", "forehead protector"],
    }

    def __init__(self):
        self.model = None
        self.processor = None
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
            from transformers import AutoModelForCausalLM, AutoProcessor
            self._init_device()
            self.model = AutoModelForCausalLM.from_pretrained(
                "microsoft/Florence-2-base", trust_remote_code=True
            )
            self.processor = AutoProcessor.from_pretrained(
                "microsoft/Florence-2-base", trust_remote_code=True
            )
            self.model.to(self.device)
            self._loaded = True
            print("[Florence] Model loaded successfully")
        except (OSError, RuntimeError) as e:
            print(f"[Florence] Failed to load model: {e}")
            self._loaded = False

    def detect_objects(self, frame_path: str) -> list[dict]:
        if not self._loaded:
            return []
        try:
            import torch
            from PIL import Image
            image = Image.open(frame_path).convert("RGB")
            prompt = "<OD>"
            inputs = self.processor(text=prompt, images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_new_tokens=256)
            result = self.processor.batch_decode(outputs, skip_special_tokens=True)[0]
            objects = []
            for part in result.split("：</OD>")[0].split("；"):
                if "：" in part:
                    label, conf = part.split("：", 1)
                    try:
                        objects.append({"label": label.strip(), "confidence": float(conf)})
                    except ValueError:
                        objects.append({"label": part.strip(), "confidence": 0.5})
            return objects
        except (OSError, RuntimeError, ValueError) as e:
            print(f"[Florence] Object detection error: {e}")
            return []

    def generate_caption(self, frame_path: str) -> str:
        if not self._loaded:
            return ""
        try:
            import torch
            from PIL import Image
            image = Image.open(frame_path).convert("RGB")
            prompt = "<CAPTION>"
            inputs = self.processor(text=prompt, images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_new_tokens=256)
            return self.processor.batch_decode(outputs, skip_special_tokens=True)[0]
        except (OSError, RuntimeError) as e:
            print(f"[Florence] Caption error: {e}")
            return ""

    def visual_grounding(self, frame_path: str, query: str) -> list[dict]:
        if not self._loaded:
            return []
        try:
            import torch
            from PIL import Image
            image = Image.open(frame_path).convert("RGB")
            prompt = f"<REF EXP>{query}</REF EXP><OD>"
            inputs = self.processor(text=prompt, images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_new_tokens=256)
            result = self.processor.batch_decode(outputs, skip_special_tokens=True)[0]
            regions = []
            for part in result.split("：</OD>")[0].split("；"):
                if "：" in part:
                    coords, conf = part.split("：", 1)
                    try:
                        regions.append({"region": coords.strip(), "score": float(conf)})
                    except ValueError:
                        pass
            return regions
        except (OSError, RuntimeError, ValueError) as e:
            print(f"[Florence] Grounding error: {e}")
            return []

    def analyze_shot(self, keyframes: list[str], shot_info: dict) -> dict:
        if not keyframes:
            return {"objects_detected": [], "caption": "", "key_props_present": {}, "visual_details": ""}
        frame = keyframes[0]
        objects = self.detect_objects(frame)
        object_labels = [obj["label"] for obj in objects]
        caption = self.generate_caption(frame)
        props_present = {}
        for prop_name, keywords in self.KEY_PROPS.items():
            props_present[prop_name] = any(
                kw in label.lower() for label in object_labels for kw in keywords
            )
        return {"objects_detected": object_labels, "caption": caption, "key_props_present": props_present, "visual_details": caption}

    def _cleanup_vram(self):
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()