# Copyright 2026 Firefly Software Solutions Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Memory subsystem: conversation history, working memory, and storage backends."""

from fireflyframework_genai.memory.conversation import ConversationMemory
from fireflyframework_genai.memory.manager import MemoryManager
from fireflyframework_genai.memory.store import FileStore, InMemoryStore, MemoryStore
from fireflyframework_genai.memory.summarization import create_llm_summarizer
from fireflyframework_genai.memory.types import ConversationTurn, MemoryEntry, MemoryScope
from fireflyframework_genai.memory.working import WorkingMemory

__all__ = [
    "ConversationMemory",
    "ConversationTurn",
    "FileStore",
    "InMemoryStore",
    "MemoryEntry",
    "MemoryManager",
    "MemoryScope",
    "MemoryStore",
    "WorkingMemory",
    "create_llm_summarizer",
]
