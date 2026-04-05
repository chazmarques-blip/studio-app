"""
Download Proxy Router - Proxies external image downloads with proper headers
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import httpx
from urllib.parse import unquote

router = APIRouter(prefix="/api", tags=["download"])

@router.get("/download-image")
async def download_image_proxy(url: str, filename: str = "avatar.png"):
    """
    Proxy endpoint to download external images with proper Content-Disposition header.
    This bypasses cross-origin download restrictions.
    
    Args:
        url: Full URL of the image to download (must be URL-encoded)
        filename: Desired filename for download (default: avatar.png)
    
    Returns:
        StreamingResponse with image data and download headers
    """
    try:
        # Decode URL
        decoded_url = unquote(url)
        
        # Fetch image from external URL
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(decoded_url)
            response.raise_for_status()
        
        # Determine content type
        content_type = response.headers.get('content-type', 'image/png')
        
        # Return image with download headers
        return StreamingResponse(
            iter([response.content]),
            media_type=content_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': str(len(response.content)),
                'Cache-Control': 'no-cache',
            }
        )
    
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch image: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
