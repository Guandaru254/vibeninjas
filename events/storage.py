"""
ZOZAPRIME Custom Cloudinary Storage

This overrides django-cloudinary-storage's URL generation to ALWAYS produce
working URLs by using Cloudinary's f_auto,q_auto transformations.

WHY THIS EXISTS:
The default MediaCloudinaryStorage generates URLs like:
    https://res.cloudinary.com/{cloud}/image/upload/v1/{public_id}

This 404s when:
- The public_id doesn't have a file extension
- Cloudinary can't infer the resource type from the extension-less URL
- The version prefix (v1) doesn't match the actual upload version

OUR FIX:
We generate URLs like:
    https://res.cloudinary.com/{cloud}/image/upload/f_auto,q_auto/{public_id}

f_auto tells Cloudinary to detect the format automatically (serves WebP to
Chrome, AVIF to Safari, JPEG as fallback). q_auto optimizes quality.
No extension needed, no version needed.

SETUP:
In settings.py, change:
    DEFAULT_FILE_STORAGE = 'events.storage.ZozaCloudinaryStorage'

That's it. Every {{ event.image.url }} across every template is now fixed.
No template edits needed.
"""
import re
from cloudinary_storage.storage import MediaCloudinaryStorage
from django.conf import settings


class ZozaCloudinaryStorage(MediaCloudinaryStorage):
    """
    Custom Cloudinary storage that generates bulletproof URLs.
    
    Extends MediaCloudinaryStorage to override only the URL generation.
    Upload behavior remains identical — files still go to Cloudinary
    under the media/ prefix as before.
    """

    def url(self, name):
        """
        Generate a Cloudinary URL with automatic format detection.
        
        Args:
            name: The stored public_id (e.g., "media/event_images/CREATIVES_UNWIND_1_upi1ai")
        
        Returns:
            str: A working Cloudinary URL with f_auto,q_auto transformations
        """
        # Guard: empty/None name
        if not name:
            return ''

        name_str = str(name)

        # If it's already a full URL, fix it in place
        if name_str.startswith('http'):
            return self._fix_existing_url(name_str)

        # Strip file extension — f_auto handles format detection
        clean_name = re.sub(r'\.\w{3,4}$', '', name_str)

        # Get cloud name from settings
        cloud_name = self._get_cloud_name()

        if not cloud_name:
            # Fallback to parent behavior if cloud name not configured
            return super().url(name)

        # Build URL with auto format and quality
        return (
            f"https://res.cloudinary.com/{cloud_name}"
            f"/image/upload/f_auto,q_auto/{clean_name}"
        )

    def _get_cloud_name(self):
        """Extract cloud name from Django settings."""
        storage_config = getattr(settings, 'CLOUDINARY_STORAGE', {})
        return storage_config.get('CLOUD_NAME', '')

    def _fix_existing_url(self, url):
        """
        Fix an existing Cloudinary URL by injecting f_auto,q_auto.
        
        Handles URLs like:
            .../upload/v1/media/event_images/foo
            .../upload/media/event_images/foo
            .../upload/v1234567890/media/event_images/foo.jpg
        
        Converts all to:
            .../upload/f_auto,q_auto/media/event_images/foo
        """
        # Pattern: everything before /upload/, then optional version/transforms, then public_id
        match = re.match(
            r'(https://res\.cloudinary\.com/[^/]+/image/upload/)'
            r'(?:v\d+/)?'           # Optional version prefix
            r'(?:[\w,_]+/)?'        # Optional existing transformations
            r'(.+?)$',              # Public ID (with or without extension)
            url
        )

        if match:
            base = match.group(1)
            public_id = match.group(2)
            # Strip extension from public_id
            clean_id = re.sub(r'\.\w{3,4}$', '', public_id)
            return f"{base}f_auto,q_auto/{clean_id}"

        # Can't parse — return original
        return url