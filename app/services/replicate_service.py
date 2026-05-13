"""
Replicate API Service for Virtual Try-On using IDM-VTON
Optimised for speed: 15 inference steps instead of 30 (~2x faster)
"""

import os
import base64
import logging
import requests
import time
from typing import Optional, Dict
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

try:
    import replicate
    REPLICATE_AVAILABLE = True
    logger.info("Replicate library loaded successfully")
except ImportError:
    REPLICATE_AVAILABLE = False
    logger.warning("Replicate library not installed. Install with: pip install replicate")

CATEGORY_MAP = {
    "tops": "upper_body",
    "shirts": "upper_body",
    "sweaters": "upper_body",
    "hoodies": "upper_body",
    "jackets": "upper_body",
    "outerwear": "upper_body",
    "upper_body": "upper_body",
    "bottoms": "lower_body",
    "pants": "lower_body",
    "jeans": "lower_body",
    "shorts": "lower_body",
    "lower_body": "lower_body",
    "dresses": "dresses",
    "one-pieces": "dresses",
}

MODEL = "cuuupid/idm-vton:0513734a452173b8173e907e3a59d19a36266e55b48528559432bd21c7d7e985"
DEFAULT_STEPS = 15
JOB_TIMEOUT = 300  # 5 minutes — cancel and fail if Replicate hangs


class ReplicateService:
    """Virtual try-on via Replicate IDM-VTON (speed-optimised)"""

    def __init__(self):
        self.api_token = os.getenv("REPLICATE_API_TOKEN")
        if not self.api_token:
            logger.warning("REPLICATE_API_TOKEN not set")
        else:
            logger.info(f"✅ REPLICATE_API_TOKEN loaded (length: {len(self.api_token)})")

    def is_available(self) -> bool:
        if not self.api_token:
            self.api_token = os.getenv("REPLICATE_API_TOKEN")
        return REPLICATE_AVAILABLE and self.api_token is not None

    async def create_virtual_tryon(
        self,
        person_image: Image.Image,
        garment_image: Image.Image,
        category: str = "upper_body",
        garment_description: Optional[str] = None,
        num_inference_steps: int = DEFAULT_STEPS,
        guidance_scale: float = 2.0,
    ) -> Optional[Dict]:
        try:
            if not self.is_available():
                logger.error("❌ Replicate not available")
                return None

            os.environ["REPLICATE_API_TOKEN"] = self.api_token

            logger.info(f"🎨 Starting IDM-VTON try-on | category={category} | steps={num_inference_steps}")
            start_time = time.time()

            replicate_category = CATEGORY_MAP.get(category.lower(), "upper_body")

            person_data_url = self._image_to_data_url(person_image)
            garment_data_url = self._image_to_data_url(garment_image)
            if not person_data_url or not garment_data_url:
                logger.error("❌ Failed to encode images")
                return None

            if not garment_description:
                garment_description = f"a {category.replace('_', ' ')}"

            client = replicate.Client(api_token=self.api_token)
            prediction = client.predictions.create(
                version=MODEL.split(":")[1],
                input={
                    "human_img": person_data_url,
                    "garm_img": garment_data_url,
                    "garment_des": garment_description,
                    "category": replicate_category,
                    "steps": num_inference_steps,
                },
            )
            logger.info(f"🔄 Prediction created: {prediction.id}")

            # Poll with timeout instead of blocking replicate.run()
            while prediction.status not in ("succeeded", "failed", "canceled"):
                elapsed = time.time() - start_time
                if elapsed > JOB_TIMEOUT:
                    prediction.cancel()
                    logger.error(f"❌ Replicate job {prediction.id} timed out after {JOB_TIMEOUT}s — cancelled")
                    return None
                time.sleep(2)
                prediction.reload()
                logger.info(f"⏳ Prediction {prediction.id} status: {prediction.status} ({elapsed:.0f}s)")

            if prediction.status != "succeeded":
                logger.error(f"❌ Prediction {prediction.id} {prediction.status}: {prediction.error}")
                return None

            result_image = self._extract_image(prediction.output)
            if not result_image:
                return None

            result_base64 = self._image_to_base64(result_image)
            processing_time = time.time() - start_time
            logger.info(f"✅ Try-on completed in {processing_time:.2f}s")

            return {
                "image_base64": result_base64,
                "confidence": 0.95,
                "method": "replicate_idm_vton",
                "processing_time": processing_time,
                "category": replicate_category,
            }

        except Exception as e:
            import traceback
            logger.error(f"❌ Replicate error: {e}\n{traceback.format_exc()}")
            return None

    def _extract_image(self, output) -> Optional[Image.Image]:
        """Handle all output formats Replicate may return."""
        try:
            if output is None:
                logger.error("❌ Replicate returned None")
                return None

            # Streaming FileOutput — collect chunks
            if hasattr(output, '__iter__') and not isinstance(output, (str, list, dict, bytes)):
                chunks = [c for c in output if isinstance(c, bytes)]
                if chunks:
                    return Image.open(io.BytesIO(b"".join(chunks)))
                logger.error("❌ Stream returned no bytes")
                return None

            if isinstance(output, bytes):
                return Image.open(io.BytesIO(output))

            if isinstance(output, str):
                if output.startswith(("http://", "https://")):
                    return self._download_image(output)
                if output.startswith("data:image"):
                    b64 = output.split(",")[1]
                    return Image.open(io.BytesIO(base64.b64decode(b64)))
                return Image.open(io.BytesIO(base64.b64decode(output)))

            if isinstance(output, list) and output:
                return self._extract_image(output[0])

            logger.error(f"❌ Unexpected output type: {type(output)}")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting image: {e}")
            return None

    def _image_to_data_url(self, image: Image.Image) -> Optional[str]:
        try:
            if image is None:
                return None
            if image.mode != "RGB":
                image = image.convert("RGB")
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            return f"data:image/png;base64,{b64}"
        except Exception as e:
            logger.error(f"❌ Image encode error: {e}")
            return None

    def _image_to_base64(self, image: Image.Image) -> str:
        try:
            if image.mode != "RGB":
                image = image.convert("RGB")
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception as e:
            logger.error(f"Error encoding result: {e}")
            return ""

    def _download_image(self, url: str) -> Optional[Image.Image]:
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                return Image.open(io.BytesIO(resp.content))
            logger.error(f"Download failed: HTTP {resp.status_code}")
            return None
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None

    def get_service_status(self) -> Dict:
        return {
            "available": self.is_available(),
            "api_token_set": self.api_token is not None,
            "model": MODEL,
            "steps": DEFAULT_STEPS,
        }


replicate_service = ReplicateService()
