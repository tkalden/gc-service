"""
Test script for Replicate virtual try-on integration
"""

import os
import sys
import asyncio
from PIL import Image
import io
import base64

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.replicate_service import replicate_service


async def test_replicate_service():
    """Test the Replicate service"""
    
    print("=" * 60)
    print("Testing Replicate Virtual Try-On Service")
    print("=" * 60)
    
    # Check service status
    status = replicate_service.get_service_status()
    print("\n📊 Service Status:")
    print(f"  Available: {status['available']}")
    print(f"  API Token Set: {status['api_token_set']}")
    print(f"  Model Version: {status['model_version']}")
    print(f"  Library Installed: {status['library_installed']}")
    
    if not status['available']:
        print("\n❌ Replicate service is not available!")
        print("\nTo enable Replicate:")
        print("1. Install replicate: pip install replicate")
        print("2. Set REPLICATE_API_TOKEN in your .env file")
        print("3. Get your token from: https://replicate.com/account")
        return
    
    print("\n✅ Replicate service is available!")
    
    # Test with dummy images (you can replace with actual images)
    print("\n🧪 To test with actual images:")
    print("1. Prepare a person image (full body photo)")
    print("2. Prepare a garment image (clothing item)")
    print("3. Update this script with the image paths")
    print("4. Run: python test_replicate.py")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


async def test_with_images(person_image_path: str, garment_image_path: str):
    """
    Test with actual images
    
    Args:
        person_image_path: Path to person image
        garment_image_path: Path to garment image
    """
    
    print("\n🎨 Testing virtual try-on with images...")
    
    # Load images
    person_image = Image.open(person_image_path)
    garment_image = Image.open(garment_image_path)
    
    print(f"  Person image: {person_image.size}")
    print(f"  Garment image: {garment_image.size}")
    
    # Run virtual try-on
    result = await replicate_service.create_virtual_tryon(
        person_image=person_image,
        garment_image=garment_image,
        category="upper_body"
    )
    
    if result:
        print(f"\n✅ Virtual try-on successful!")
        print(f"  Method: {result['method']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Processing time: {result['processing_time']:.2f}s")
        
        # Save result
        result_image_data = base64.b64decode(result['image_base64'])
        result_image = Image.open(io.BytesIO(result_image_data))
        
        output_path = "tryon_result.png"
        result_image.save(output_path)
        print(f"  Result saved to: {output_path}")
    else:
        print("\n❌ Virtual try-on failed!")


if __name__ == "__main__":
    # Run basic test
    asyncio.run(test_replicate_service())
    
    # Uncomment to test with actual images:
    # asyncio.run(test_with_images(
    #     person_image_path="path/to/person.jpg",
    #     garment_image_path="path/to/garment.jpg"
    # ))
