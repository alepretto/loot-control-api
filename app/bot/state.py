"""Holds the running bot Application instance so routers can access it without circular imports."""
from typing import Optional

bot_app: Optional[object] = None
