#!/usr/bin/env python3
"""
Test script to verify AI upload functionality and background removal
"""
import base64
import json
import os
import sys
from pathlib import Path

import requests

# Configuration
BACKEND_URL = "http://192.168.1.169:8000"
TEST_IMAGE_PATH = "test_output_auto.png"  # Using an existing test image

def test_background_removal_configuration():
    """Test if rembg is properly configured"""
    print("\n" + "="*60)
    print("TEST 1: Background Removal Configuration")
    print("="*60)
    
    try:
        from app.services.background_removal import background_removal_service
        
        is_configured = background_removal_service.is_configured()
        print(f"✓ Background removal service loaded")
        print(f"  - Configured: {is_configured}")
        
        if not is_configured:
            print("\n❌ ISSUE: Background removal is NOT configured")
            print("   This means rembg is not installed or failed to initialize")
            print("\n   To fix:")
            print("   1. pip install rembg")
            print("   2. Restart the backend")
            return False
        else:
            print("✓ Background removal is properly configured")
            return True
            
    except Exception as e:
        print(f"❌ ERROR loading background removal service: {e}")
        return False


def test_image_to_base64():
    """Test converting image to base64"""
    print("\n" + "="*60)
    print("TEST 2: Image to Base64 Conversion")
    print("="*60)
    
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"❌ Test image not found: {TEST_IMAGE_PATH}")
        return None
        
    try:
        with open(TEST_IMAGE_PATH, 'rb') as f:
            image_data = f.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
        print(f"✓ Image loaded: {TEST_IMAGE_PATH}")
        print(f"  - File size: {len(image_data)} bytes")
        print(f"  - Base64 length: {len(base64_image)} characters")
        print(f"  - Base64 preview: {base64_image[:50]}...")
        
        return base64_image
        
    except Exception as e:
        print(f"❌ ERROR converting image: {e}")
        return None


def test_background_removal_direct(base64_image):
    """Test background removal directly (without API)"""
    print("\n" + "="*60)
    print("TEST 3: Direct Background Removal")
    print("="*60)
    
    try:
        from app.services.background_removal import background_removal_service
        
        print("Processing image with background removal...")
        result = background_removal_service.remove_background_from_base64(base64_image)
        
        if result:
            print(f"✓ Background removal successful")
            print(f"  - Result type: {type(result)}")
            print(f"  - Result length: {len(result)} characters")
            return True
        else:
            print("❌ Background removal returned None")
            return False
            
    except Exception as e:
        print(f"❌ ERROR in background removal: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_classification_direct(base64_image):
    """Test classification directly (without API)"""
    print("\n" + "="*60)
    print("TEST 4: Direct Classification")
    print("="*60)
    
    try:
        from app.services.enhanced_clothing_classifier import \
            enhanced_classifier
        
        print("Processing image with classifier...")
        result = enhanced_classifier.classify_with_season(base64_image)
        
        if result:
            print(f"✓ Classification successful")
            print(f"  - Category: {result.get('category')}")
            print(f"  - Confidence: {result.get('confidence')}")
            print(f"  - ML Label: {result.get('ml_label')}")
            print(f"  - Season: {result.get('season')}")
            return True
        else:
            print("❌ Classification returned None")
            return False
            
    except Exception as e:
        print(f"❌ ERROR in classification: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_smart_upload_api(base64_image, token=None):
    """Test the full smart upload API endpoint"""
    print("\n" + "="*60)
    print("TEST 5: Smart Upload API Endpoint")
    print("="*60)
    
    url = f"{BACKEND_URL}/api/v1/admin/smart-upload-async"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    payload = {
        'image_base64': base64_image
    }
    
    try:
        print(f"Sending request to: {url}")
        print(f"With auth token: {bool(token)}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"\n✓ Response received")
        print(f"  - Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  - Success: {result.get('success')}")
            print(f"  - Category: {result.get('data', {}).get('category')}")
            print(f"  - Background removed: {result.get('data', {}).get('backgroundRemoved')}")
            print(f"  - AI Features: {result.get('data', {}).get('ai_features')}")
            
            if not result.get('data', {}).get('backgroundRemoved'):
                print("\n⚠️  WARNING: Background was NOT removed")
                print("   Check if rembg is properly installed")
                
            return True
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR calling API: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*60)
    print("AI UPLOAD DIAGNOSTIC TEST")
    print("="*60)
    
    results = []
    
    # Test 1: Check if background removal is configured
    results.append(("Background Removal Config", test_background_removal_configuration()))
    
    # Test 2: Convert test image to base64
    base64_image = test_image_to_base64()
    if not base64_image:
        print("\n❌ FAILED: Could not convert test image to base64")
        print("Stopping tests")
        return
    results.append(("Image to Base64", True))
    
    # Test 3: Test background removal directly
    results.append(("Direct Background Removal", test_background_removal_direct(base64_image)))
    
    # Test 4: Test classification directly
    results.append(("Direct Classification", test_classification_direct(base64_image)))
    
    # Test 5: Test full API (without token - should work for testing)
    results.append(("Smart Upload API", test_smart_upload_api(base64_image)))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n✅ ALL TESTS PASSED - AI upload is working correctly!")
    else:
        print("\n⚠️  SOME TESTS FAILED - Check the output above for details")
        
        # Provide specific recommendations
        if not results[0][1]:  # Background removal config failed
            print("\n🔧 RECOMMENDED FIX:")
            print("   cd /Users/tenzinkalden/gc-service")
            print("   pip install rembg")
            print("   ./startbackend.sh")


if __name__ == "__main__":
    main()


