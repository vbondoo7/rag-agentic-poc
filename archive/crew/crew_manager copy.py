# UNUSED BACKUP FILE - crew/crew_manager copy.py (moved to archive)
# Original content preserved for review.

# crew/crew_manager.py
import os
from crewai import Agent, Task, Crew
from logs.logger import get_logger
from db.chat_db import save_message
from uuid import uuid4
from typing import List
import google.generativeai as genai

logger = get_logger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.warning("Gemini API key not set! Please export GEMINI_API_KEY or add to secrets.toml.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# ... (rest of file preserved in archive)
