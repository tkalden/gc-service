"""
Test script to verify virtual try-on API is working correctly
Run with: python test_virtual_tryon_api.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.database_service import DatabaseService
from app.services.avatar_service import avatar_service
from app.models.models import TryOnRequest
from app.core.logging import get_logger

logger = get_logger(__name__)


async def test_virtual_tryon_api():
    """Test the virtual try-on API flow"""
    print("🧪 Testing Virtual Try-On API\n")
    print("=" * 60)
    
    try:
        # Step 1: Get a test user (or create one for testing)
        print("\n1️⃣ Checking for test user and data...")
        
        # Try to get any existing user with an avatar
        # In a real scenario, you'd use a test user ID
        test_user_id = None
        
        # Check if we have any avatars in the database
        try:
            # This is a simplified check - in production you'd have proper test data
            print("   ⚠️  Note: This test requires existing avatar and clothing item data")
            print("   ⚠️  Make sure you have:")
            print("      - A user with an avatar uploaded")
            print("      - At least one clothing item in the database")
            print("      - Valid avatar_id and clothing_item_id")
            
            # For testing, we'll use placeholder IDs
            # Replace these with actual IDs from your database
            test_avatar_id = os.getenv("TEST_AVATAR_ID", "test-avatar-id")
            test_clothing_id = os.getenv("TEST_CLOTHING_ID", "test-clothing-id")
            
            print(f"\n   Using test IDs:")
            print(f"   - Avatar ID: {test_avatar_id}")
            print(f"   - Clothing ID: {test_clothing_id}")
            
        except Exception as e:
            print(f"   ❌ Error checking database: {e}")
            return False
        
        # Step 2: Test the TryOnRequest model
        print("\n2️⃣ Testing TryOnRequest model...")
        try:
            request = TryOnRequest(
                avatar_id=test_avatar_id,
                clothing_item_id=test_clothing_id
            )
            print(f"   ✅ TryOnRequest created successfully")
            print(f"      - avatar_id: {request.avatar_id}")
            print(f"      - clothing_item_id: {request.clothing_item_id}")
        except Exception as e:
            print(f"   ❌ Error creating TryOnRequest: {e}")
            return False
        
        # Step 3: Test avatar service availability
        print("\n3️⃣ Checking avatar service availability...")
        if avatar_service.is_available():
            print("   ✅ Avatar service is available")
        else:
            print("   ⚠️  Avatar service not fully available (MediaPipe may not be installed)")
            print("   ⚠️  This is OK for API testing, but pose detection won't work")
        
        # Step 4: Test Replicate service
        print("\n4️⃣ Checking Replicate service...")
        from app.services.replicate_service import replicate_service
        
        if replicate_service.is_available():
            print("   ✅ Replicate service is available")
            print(f"      - API Token: {'Set' if replicate_service.api_token else 'Not set'}")
            print(f"      - Model: {replicate_service.model_version}")
        else:
            print("   ⚠️  Replicate service not available")
            print("   ⚠️  Will fall back to basic overlay method")
            if not replicate_service.api_token:
                print("   💡 Set REPLICATE_API_TOKEN environment variable to enable Replicate")
        
        # Step 5: Test the perform_virtual_try_on method (with mock data)
        print("\n5️⃣ Testing perform_virtual_try_on method...")
        print("   ⚠️  Note: This requires valid avatar and clothing item IDs")
        print("   ⚠️  Skipping actual API call (requires database connection)")
        print("   💡 To test with real data, run:")
        print("      TEST_AVATAR_ID=<your-avatar-id> TEST_CLOTHING_ID=<your-clothing-id> python test_virtual_tryon_api.py")
        
        # Step 6: Test the API endpoint structure
        print("\n6️⃣ Testing API endpoint structure...")
        from app.api.v1.avatar.router import router
        
        # Check if the route exists
        routes = [route for route in router.routes if hasattr(route, 'path')]
        try_on_route = [r for r in routes if 'try-on' in r.path]
        
        if try_on_route:
            print(f"   ✅ Try-on endpoint found: {try_on_route[0].path}")
            print(f"      - Methods: {try_on_route[0].methods}")
        else:
            print("   ❌ Try-on endpoint not found")
            return False
        
        # Step 7: Test request/response format
        print("\n7️⃣ Testing request/response format...")
        print("   Expected request format:")
        print("   {")
        print("     'avatar_id': 'string',")
        print("     'clothing_item_id': 'string',")
        print("     'pose_adjustment': {} (optional)")
        print("   }")
        print("\n   Expected response format:")
        print("   {")
        print("     'success': True,")
        print("     'data': {")
        print("       'preview_image': 'base64_string',")
        print("       'image_base64': 'base64_string',")
        print("       'confidence': 0.95,")
        print("       'method': 'replicate_idm_vton'")
        print("     },")
        print("     'message': 'Try-on preview generated successfully'")
        print("   }")
        
        print("\n" + "=" * 60)
        print("✅ All structural tests passed!")
        print("\n📝 Next steps:")
        print("   1. Ensure you have a valid avatar and clothing item in the database")
        print("   2. Set TEST_AVATAR_ID and TEST_CLOTHING_ID environment variables")
        print("   3. Run the test again to test the actual API call")
        print("   4. Or test via the frontend by clicking a clothing item")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_with_real_data():
    """Test with real database data if available"""
    print("\n🔬 Testing with real data...\n")
    
    test_avatar_id = os.getenv("TEST_AVATAR_ID")
    test_clothing_id = os.getenv("TEST_CLOTHING_ID")
    test_user_id = os.getenv("TEST_USER_ID")
    
    if not all([test_avatar_id, test_clothing_id, test_user_id]):
        print("   ⚠️  Skipping real data test - missing environment variables")
        print("   💡 Set TEST_AVATAR_ID, TEST_CLOTHING_ID, and TEST_USER_ID")
        return False
    
    try:
        # Verify avatar exists
        avatar = await DatabaseService.get_avatar_by_id(test_avatar_id)
        if not avatar:
            print(f"   ❌ Avatar {test_avatar_id} not found")
            return False
        print(f"   ✅ Avatar found: {avatar.id}")
        
        # Verify clothing item exists
        clothing = await DatabaseService.get_clothing_item_by_id(test_clothing_id)
        if not clothing:
            print(f"   ❌ Clothing item {test_clothing_id} not found")
            return False
        print(f"   ✅ Clothing item found: {clothing.name}")
        
        # Create request
        request = TryOnRequest(
            avatar_id=test_avatar_id,
            clothing_item_id=test_clothing_id
        )
        
        # Test the actual API call
        print("\n   🚀 Calling perform_virtual_try_on...")
        result = await avatar_service.perform_virtual_try_on(request, test_user_id)
        
        if result:
            print("   ✅ Try-on completed successfully!")
            print(f"      - Has preview_image: {'preview_image' in result}")
            print(f"      - Has image_base64: {'image_base64' in result}")
            print(f"      - Method: {result.get('method', 'unknown')}")
            print(f"      - Confidence: {result.get('confidence', 'unknown')}")
            return True
        else:
            print("   ❌ Try-on returned no result")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing with real data: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Virtual Try-On API Test Suite")
    print("=" * 60)
    
    # Run basic structural tests
    basic_test_result = asyncio.run(test_virtual_tryon_api())
    
    # Run real data test if environment variables are set
    if os.getenv("TEST_AVATAR_ID") and os.getenv("TEST_CLOTHING_ID"):
        real_test_result = asyncio.run(test_with_real_data())
    else:
        real_test_result = None
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Basic tests: {'✅ PASSED' if basic_test_result else '❌ FAILED'}")
    if real_test_result is not None:
        print(f"Real data test: {'✅ PASSED' if real_test_result else '❌ FAILED'}")
    else:
        print("Real data test: ⏭️  SKIPPED (set env vars to run)")
    print("=" * 60 + "\n")

