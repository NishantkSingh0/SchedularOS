"""
Content Generation Connector
Implements image and video generation using OpenAI DALL-E and similar APIs
"""
import os
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import base64


@dataclass
class GeneratedImage:
    """Represents a generated image"""
    id: str
    url: str
    prompt: str
    revised_prompt: str
    model: str


@dataclass
class GeneratedVideo:
    """Represents a generated video"""
    id: str
    url: str
    prompt: str
    status: str
    duration: float


class ContentGenerationConnector:
    """Connector for content generation (images and videos)"""
    
    def __init__(self, api_key: Optional[str] = None, api_endpoint: Optional[str] = None):
        """
        Initialize content generation connector
        
        Args:
            api_key: API key for content generation service
            api_endpoint: API endpoint URL
        """
        self.api_key = api_key or os.getenv('CONTENT_GEN_API_KEY')
        self.api_endpoint = api_endpoint or os.getenv('CONTENT_GEN_API_ENDPOINT', 'https://api.openai.com/v1')
        self.image_model = os.getenv('CONTENT_GEN_IMAGE_MODEL', 'dall-e-3')
        self.video_model = os.getenv('CONTENT_GEN_VIDEO_MODEL', 'runway-gen3')
        
        if not self.api_key:
            raise ValueError("CONTENT_GEN_API_KEY not configured")
    
    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the content generation API"""
        url = f"{self.api_endpoint}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if method == "GET":
            response = requests.get(url, headers=headers, params=data, timeout=60)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=60)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    def generate_image(self, prompt: str, size: str = "1024x1024", quality: str = "standard", n: int = 1) -> List[GeneratedImage]:
        """
        Generate an image using DALL-E
        
        Args:
            prompt: Text description of the image to generate
            size: Image size (256x256, 512x512, 1024x1024, 1792x1024, 1024x1792)
            quality: Image quality (standard, hd)
            n: Number of images to generate
            
        Returns:
            List of GeneratedImage objects
        """
        endpoint = "images/generations"
        
        data = {
            "model": self.image_model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": n
        }
        
        try:
            response_data = self._make_request(endpoint, "POST", data)
            
            images = []
            if "data" in response_data:
                for item in response_data["data"]:
                    images.append(GeneratedImage(
                        id=item.get("id", ""),
                        url=item.get("url", ""),
                        prompt=prompt,
                        revised_prompt=item.get("revised_prompt", ""),
                        model=self.image_model
                    ))
            
            return images
            
        except requests.RequestException as e:
            raise Exception(f"Failed to generate image: {str(e)}")
    
    def edit_image(self, image_url: str, prompt: str, mask_url: Optional[str] = None, size: str = "1024x1024") -> List[GeneratedImage]:
        """
        Edit an existing image using DALL-E
        
        Args:
            image_url: URL of the image to edit
            prompt: Text description of how to edit the image
            mask_url: Optional URL of the mask image
            size: Image size
            
        Returns:
            List of GeneratedImage objects
        """
        endpoint = "images/edits"
        
        # Note: This endpoint requires multipart/form-data, which is more complex
        # For now, we'll use a simpler approach with URL-based editing if available
        data = {
            "image": image_url,
            "prompt": prompt,
            "size": size
        }
        
        if mask_url:
            data["mask"] = mask_url
        
        try:
            response_data = self._make_request(endpoint, "POST", data)
            
            images = []
            if "data" in response_data:
                for item in response_data["data"]:
                    images.append(GeneratedImage(
                        id=item.get("id", ""),
                        url=item.get("url", ""),
                        prompt=prompt,
                        revised_prompt=prompt,
                        model=self.image_model
                    ))
            
            return images
            
        except requests.RequestException as e:
            raise Exception(f"Failed to edit image: {str(e)}")
    
    def generate_video(self, prompt: str, duration: float = 5.0) -> GeneratedVideo:
        """
        Generate a video (placeholder for Runway or similar service)
        
        Args:
            prompt: Text description of the video to generate
            duration: Video duration in seconds
            
        Returns:
            GeneratedVideo object
        """
        # This is a placeholder - actual implementation would depend on the video generation service
        # For Runway, Replicate, or similar services, you would implement the specific API calls
        
        return GeneratedVideo(
            id="mock-video-id",
            url="https://example.com/mock-video-url",
            prompt=prompt,
            status="completed",
            duration=duration
        )
    
    def get_image_variations(self, image_url: str, n: int = 1, size: str = "1024x1024") -> List[GeneratedImage]:
        """
        Generate variations of an existing image
        
        Args:
            image_url: URL of the image to vary
            n: Number of variations to generate
            size: Image size
            
        Returns:
            List of GeneratedImage objects
        """
        endpoint = "images/variations"
        
        data = {
            "image": image_url,
            "n": n,
            "size": size
        }
        
        try:
            response_data = self._make_request(endpoint, "POST", data)
            
            images = []
            if "data" in response_data:
                for item in response_data["data"]:
                    images.append(GeneratedImage(
                        id=item.get("id", ""),
                        url=item.get("url", ""),
                        prompt="variation",
                        revised_prompt="variation",
                        model=self.image_model
                    ))
            
            return images
            
        except requests.RequestException as e:
            raise Exception(f"Failed to generate image variations: {str(e)}")


# Singleton instance
_content_connector: Optional[ContentGenerationConnector] = None


def get_content_generation_connector() -> ContentGenerationConnector:
    """Get or create the content generation connector singleton"""
    global _content_connector
    if _content_connector is None:
        _content_connector = ContentGenerationConnector()
    return _content_connector
