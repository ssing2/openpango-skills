import logging
import tweepy
import requests
from typing import Dict, Any, Optional

# Basic logging setup
logger = logging.getLogger(__name__)

class SocialConnector:
    """Base class for social media connectors."""
    def post(self, text: str, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement post()")

class TwitterConnector(SocialConnector):
    def __init__(self, bearer_token: str, consumer_key: str, consumer_secret: str, access_token: str, access_token_secret: str):
        self.client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True
        )

    def post(self, text: str, **kwargs) -> Dict[str, Any]:
        try:
            response = self.client.create_tweet(text=text)
            return {"success": True, "platform": "twitter", "data": response.data}
        except Exception as e:
            logger.error(f"Twitter post failed: {e}")
            return {"success": False, "platform": "twitter", "error": str(e)}

class LinkedInConnector(SocialConnector):
    """
    LinkedIn logic: POST to /v2/posts.
    """
    def __init__(self, access_token: str, author_urn: str):
        self.access_token = access_token
        self.author_urn = author_urn
        self.base_url = "https://api.linkedin.com/v2/posts"

    def post(self, text: str, **kwargs) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }
        
        payload = {
            "author": self.author_urn,
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            return {"success": True, "platform": "linkedin", "data": response.json() if response.content else {"status": "success"}}
        except Exception as e:
            logger.error(f"LinkedIn post failed: {e}")
            return {"success": False, "platform": "linkedin", "error": str(e)}

class FarcasterConnector(SocialConnector):
    """
    Farcaster implementation via Neynar API.
    """
    def __init__(self, api_key: str, signer_uuid: str):
        self.api_key = api_key
        self.signer_uuid = signer_uuid
        self.base_url = "https://api.neynar.com/v2/farcaster/cast"

    def post(self, text: str, **kwargs) -> Dict[str, Any]:
        headers = {
            "api_key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "signer_uuid": self.signer_uuid,
            "text": text
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            return {"success": True, "platform": "farcaster", "data": response.json()}
        except Exception as e:
            logger.error(f"Farcaster post failed: {e}")
            return {"success": False, "platform": "farcaster", "error": str(e)}

class SocialManager:
    """
    Manager to orchestrate posts across multiple social platforms.
    """
    def __init__(self, config: Dict[str, Any]):
        self.connectors = {}
        
        if 'twitter' in config:
            self.connectors['twitter'] = TwitterConnector(**config['twitter'])
        
        if 'linkedin' in config:
            self.connectors['linkedin'] = LinkedInConnector(**config['linkedin'])
            
        if 'farcaster' in config:
            self.connectors['farcaster'] = FarcasterConnector(**config['farcaster'])

    def post_to_all(self, text: str) -> Dict[str, Dict[str, Any]]:
        results = {}
        for name, connector in self.connectors.items():
            results[name] = connector.post(text)
        return results

    def post_to_platform(self, platform: str, text: str, **kwargs) -> Dict[str, Any]:
        if platform not in self.connectors:
            return {"success": False, "error": f"Platform {platform} not configured"}
        return self.connectors[platform].post(text, **kwargs)
