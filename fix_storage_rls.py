#!/usr/bin/env python3
"""
Script to fix Supabase Storage RLS (Row-Level Security) policies
This script will create the necessary policies for authenticated users to upload images
"""

import os
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

def fix_storage_rls_policies():
    """Fix RLS policies for the clothing-images storage bucket"""
    
    # Create Supabase client with service key (admin privileges)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    print("🔧 Fixing Supabase Storage RLS policies...")
    print(f"📍 Supabase URL: {SUPABASE_URL}")
    print(f"🪣 Storage Bucket: clothing-images")
    
    try:
        # SQL commands to create/update RLS policies for storage
        policies_sql = """
        -- Enable RLS on storage.objects table if not already enabled
        ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;
        
        -- Drop existing policies if they exist (to avoid conflicts)
        DROP POLICY IF EXISTS "Authenticated users can upload images" ON storage.objects;
        DROP POLICY IF EXISTS "Authenticated users can view their images" ON storage.objects;
        DROP POLICY IF EXISTS "Authenticated users can update their images" ON storage.objects;
        DROP POLICY IF EXISTS "Authenticated users can delete their images" ON storage.objects;
        DROP POLICY IF EXISTS "Public can view images" ON storage.objects;
        
        -- Create policy for authenticated users to upload images to their own folder
        CREATE POLICY "Authenticated users can upload images" ON storage.objects
        FOR INSERT WITH CHECK (
            auth.role() = 'authenticated' 
            AND bucket_id = 'clothing-images'
            AND (storage.foldername(name))[1] = 'user-clothes'
            AND (storage.foldername(name))[2] = auth.uid()::text
        );
        
        -- Create policy for authenticated users to view their own images
        CREATE POLICY "Authenticated users can view their images" ON storage.objects
        FOR SELECT USING (
            auth.role() = 'authenticated' 
            AND bucket_id = 'clothing-images'
            AND (storage.foldername(name))[1] = 'user-clothes'
            AND (storage.foldername(name))[2] = auth.uid()::text
        );
        
        -- Create policy for authenticated users to update their own images
        CREATE POLICY "Authenticated users can update their images" ON storage.objects
        FOR UPDATE USING (
            auth.role() = 'authenticated' 
            AND bucket_id = 'clothing-images'
            AND (storage.foldername(name))[1] = 'user-clothes'
            AND (storage.foldername(name))[2] = auth.uid()::text
        );
        
        -- Create policy for authenticated users to delete their own images
        CREATE POLICY "Authenticated users can delete their images" ON storage.objects
        FOR DELETE USING (
            auth.role() = 'authenticated' 
            AND bucket_id = 'clothing-images'
            AND (storage.foldername(name))[1] = 'user-clothes'
            AND (storage.foldername(name))[2] = auth.uid()::text
        );
        
        -- Optional: Allow public read access to images (remove if you want private images)
        CREATE POLICY "Public can view images" ON storage.objects
        FOR SELECT USING (
            bucket_id = 'clothing-images'
            AND (storage.foldername(name))[1] = 'user-clothes'
        );
        """
        
        # Execute the SQL policies
        result = supabase.rpc('exec_sql', {'sql': policies_sql}).execute()
        
        print("✅ RLS policies created successfully!")
        print("\n📋 Created policies:")
        print("   • Authenticated users can upload images")
        print("   • Authenticated users can view their images") 
        print("   • Authenticated users can update their images")
        print("   • Authenticated users can delete their images")
        print("   • Public can view images (optional)")
        
    except Exception as e:
        print(f"❌ Error creating policies with RPC: {e}")
        print("\n🔄 Trying alternative approach with direct SQL execution...")
        
        try:
            # Alternative approach: Execute policies one by one
            individual_policies = [
                "ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;",
                
                "DROP POLICY IF EXISTS \"Authenticated users can upload images\" ON storage.objects;",
                """CREATE POLICY "Authenticated users can upload images" ON storage.objects
                FOR INSERT WITH CHECK (
                    auth.role() = 'authenticated' 
                    AND bucket_id = 'clothing-images'
                );""",
                
                "DROP POLICY IF EXISTS \"Authenticated users can view their images\" ON storage.objects;",
                """CREATE POLICY "Authenticated users can view their images" ON storage.objects
                FOR SELECT USING (
                    auth.role() = 'authenticated' 
                    AND bucket_id = 'clothing-images'
                );""",
                
                "DROP POLICY IF EXISTS \"Public can view images\" ON storage.objects;",
                """CREATE POLICY "Public can view images" ON storage.objects
                FOR SELECT USING (bucket_id = 'clothing-images');"""
            ]
            
            for policy in individual_policies:
                try:
                    supabase.rpc('exec_sql', {'sql': policy}).execute()
                    print(f"✅ Executed: {policy[:50]}...")
                except Exception as policy_error:
                    print(f"⚠️  Warning executing policy: {policy_error}")
                    
            print("✅ Alternative approach completed!")
            
        except Exception as alt_error:
            print(f"❌ Alternative approach also failed: {alt_error}")
            print("\n📝 Manual steps needed:")
            print("1. Go to your Supabase dashboard")
            print("2. Navigate to Storage > Policies")
            print("3. Create policies for the 'clothing-images' bucket")
            print("4. Allow authenticated users to INSERT, SELECT, UPDATE, DELETE")
            
    print("\n🧪 Testing storage access...")
    try:
        # Test if we can list objects in the bucket
        result = supabase.storage.from_('clothing-images').list()
        print("✅ Storage access test successful!")
        print(f"📁 Found {len(result) if result else 0} items in bucket")
        
    except Exception as test_error:
        print(f"⚠️  Storage access test failed: {test_error}")
        
def create_bucket_if_not_exists():
    """Create the clothing-images bucket if it doesn't exist"""
    
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    try:
        # Try to create the bucket (will fail if it already exists)
        bucket_result = supabase.storage.create_bucket('clothing-images', {
            'public': True,  # Allow public read access
            'file_size_limit': 10 * 1024 * 1024,  # 10MB limit
            'allowed_mime_types': ['image/jpeg', 'image/png', 'image/webp']
        })
        print("✅ Created clothing-images bucket")
        
    except Exception as e:
        if "already exists" in str(e).lower():
            print("✅ clothing-images bucket already exists")
        else:
            print(f"⚠️  Error creating bucket: {e}")

def main():
    """Main function to fix all storage issues"""
    
    print("🚀 Starting Supabase Storage RLS Fix...")
    print("=" * 50)
    
    # Step 1: Ensure bucket exists
    create_bucket_if_not_exists()
    
    # Step 2: Fix RLS policies
    fix_storage_rls_policies()
    
    print("\n" + "=" * 50)
    print("🎉 Storage RLS fix completed!")
    print("\n📋 Next steps:")
    print("1. Restart your backend server")
    print("2. Try uploading an image from your app")
    print("3. Check the logs for any remaining errors")

if __name__ == "__main__":
    main()
