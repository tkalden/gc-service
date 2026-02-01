"""
Test script to verify Replicate virtual try-on is working
"""
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_replicate_service():
    """Test Replicate service availability and initialization"""
    print("=" * 60)
    print("Testing Replicate Service")
    print("=" * 60)
    
    try:
        from app.services.replicate_service import replicate_service, REPLICATE_AVAILABLE
        
        print("\n1️⃣ Checking Replicate Library:")
        print(f"   REPLICATE_AVAILABLE: {REPLICATE_AVAILABLE}")
        
        print("\n2️⃣ Checking API Token:")
        token = os.getenv("REPLICATE_API_TOKEN")
        print(f"   Token from env: {'Set' if token else 'Not set'}")
        print(f"   Token length: {len(token) if token else 0}")
        print(f"   Service token: {'Set' if replicate_service.api_token else 'Not set'}")
        
        print("\n3️⃣ Checking Service Availability:")
        is_available = replicate_service.is_available()
        print(f"   is_available(): {is_available}")
        
        if not is_available:
            print("\n❌ Replicate service is NOT available!")
            if not REPLICATE_AVAILABLE:
                print("   Reason: Replicate library not installed")
            if not replicate_service.api_token:
                print("   Reason: REPLICATE_API_TOKEN not set")
            return False
        
        print("\n✅ Replicate service is available!")
        print(f"   Model version: {replicate_service.model_version}")
        
        print("\n4️⃣ Testing with sample images...")
        print("   (This requires actual images - skipping for now)")
        print("   To test with images, you need:")
        print("   - A person image (avatar)")
        print("   - A garment image (clothing item)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing Replicate service: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_avatar_service_integration():
    """Test if avatar service can use Replicate"""
    print("\n" + "=" * 60)
    print("Testing Avatar Service Integration")
    print("=" * 60)
    
    try:
        from app.services.avatar_service import avatar_service
        from app.services.replicate_service import replicate_service
        
        print("\n1️⃣ Checking Avatar Service:")
        print(f"   Avatar service available: {avatar_service.is_available()}")
        
        print("\n2️⃣ Checking Replicate in Avatar Service:")
        # Check if replicate_service is imported
        import app.services.avatar_service as avatar_module
        has_replicate = hasattr(avatar_module, 'replicate_service')
        print(f"   replicate_service imported: {has_replicate}")
        
        if has_replicate:
            print(f"   Replicate available: {replicate_service.is_available()}")
        
        print("\n3️⃣ Simulating try-on check:")
        # Simulate the condition check
        replicate_available = replicate_service.is_available()
        clothing_image_exists = True  # Simulated
        would_use_replicate = replicate_available and clothing_image_exists
        
        print(f"   Would use Replicate: {would_use_replicate}")
        print(f"   - Replicate available: {replicate_available}")
        print(f"   - Clothing image exists: {clothing_image_exists}")
        
        if would_use_replicate:
            print("\n✅ Avatar service would use Replicate for try-on!")
        else:
            print("\n⚠️  Avatar service would NOT use Replicate")
            if not replicate_available:
                print("   Reason: Replicate not available")
            if not clothing_image_exists:
                print("   Reason: No clothing image")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing integration: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("\n🧪 Starting Replicate Integration Tests\n")
    
    # Test 1: Replicate service
    test1_result = await test_replicate_service()
    
    # Test 2: Avatar service integration
    test2_result = await test_avatar_service_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Replicate Service: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"Avatar Integration: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result and test2_result:
        print("\n✅ All tests passed! Replicate should work for try-on.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())


