from typing import Optional, cast
import hashlib
from steamship import Block
from steamship.agents.schema import AgentContext
from steamship.utils.kv_store import KeyValueStore
from steamship.data.tags.tag_constants import TagValueKey

class ToolCache:
    """A simple cache for Tools.

    Usage:

        cache = ToolCache(self.name)
        cache.set(input_block, output_block, agent_context)
        block_or_none = cache.get(input_block, agent_context)

    """
    tool_name: str
    kv_store: Optional[KeyValueStore] = None

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.kv_store = None

    def _get_kv_store(self, context: AgentContext):
        """Return the Key Value store backing this cache, lazily creating it on first use."""
        if self.kv_store is None:
            self.kv_store = KeyValueStore(context.client, store_identifier=f"ToolCache-{self.tool_name}")
        return self.kv_store

    def _key_for_block(self, input_block: Block, context: AgentContext) -> str:
        """Return the hash key for a provided block."""
        string_to_hash = input_block.text or input_block.url or input_block.content_url or ""
        input_hash = hashlib.md5(string_to_hash.encode())
        input_hash_string = input_hash.hexdigest()
        return input_hash_string

    def set(self, input_block: Block, output_value: Block, context: AgentContext):
        """Cache the output for the provided input."""
        kv_store = self._get_kv_store(context)
        input_hash_string = self._key_for_block(input_block, context)

        block_dict = output_value.dict()
        wrapped_dict = {TagValueKey.VALUE: block_dict}

        kv_store.set(input_hash_string, wrapped_dict)

    def get(self, input_block: Block, context: AgentContext) -> Optional[Block]:
        """Cache the output for the provided input."""
        kv_store = self._get_kv_store(context)
        input_hash_string = self._key_for_block(input_block, context)
        val = kv_store.get(input_hash_string)
        if not val:
            return None
        if TagValueKey.VALUE not in val:
            return None

        block_dict = val.get(TagValueKey.VALUE)
        block = cast(Block, Block.parse_obj(block_dict))
        block.client = context.client
        return block


