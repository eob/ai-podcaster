import json
from typing import List, Union, Any
from pydantic import BaseModel, Field
from steamship import Block, Steamship, Task
from repl import ToolREPL
from steamship.agents.schema import AgentContext, Tool
from steamship.agents.utils import get_llm, with_llm
from steamship.agents.llms import OpenAI
from steamship.agents.tools.text_generation import JsonObjectGeneratorTool
from steamship.utils.kv_store import KeyValueStore

from tools.tool_cache import ToolCache


class PodcastPremiseTool(JsonObjectGeneratorTool):
    cache: ToolCache = Field(None, exclude=True)

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True
        """Permit the ToolCache object."""

    class Output(BaseModel):
        podcast_name: str = Field()
        podcast_description: str = Field()

    name: str = "PodcastPremiseTool"
    human_description: str = "Generates a premise for a podcast."
    agent_description: str = (
        "Used to generate a premise for a new podcast. ",
        "Use this tool if a user asks for an idea for a new podcast. ",
        "Input: The desire for a new podcast. "
        "Output: The name and description of a podcast the user could create."
    )

    plural_object_description: str = "podcasts"
    object_keys: List[str] = ["podcast_name", "podcast_description"]
    example_rows: List[List[str]] = [
        ["Animal Planet", "The world is an amazing place. We'll tell you its stories every day."],
        ["Banking News", "All the updates you need to track the banking world."],
        ["Hollywood Gab", "The latest stories from inside Hollywood."],
        ["The MIT Tech Review", "The latest in science and technology, explained."],
        ["Politico", "Hear the opinions and analysis that shapes capitol hill."],
        ["Car Talk", "Call-in show with automotive mysteries, fix-it help, and laughter."],
    ]

    def parse_final_output(self, block: Block) -> Output:
        """Parses the final output"""
        return PodcastPremiseTool.Output.parse_obj(json.loads(block.text))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cache = ToolCache(self.name)

    def run(self, tool_input: List[Block], context: AgentContext) -> Union[List[Block], Task[Any]]:
        """Run the tool, caching output."""
        output = []

        for block in tool_input:
            cached_output = self.cache.get(block, context)
            if cached_output:
                output.append(cached_output)
            else:
                output_blocks = super().run([block], context)
                if len(output_blocks):
                    output_block = output_blocks[0]
                    self.cache.set(block, output_block, context)
                    output.append(output_block)

        return output

if __name__ == "__main__":
    """Note that the temporary workspace will mean that a DIFFERENT cache is used each time!
    
    To see the cache in action, provide a second (or third) input that is identical to the tool within the REPL.
    """
    with Steamship.temporary_workspace() as client:
        ToolREPL(PodcastPremiseTool()).run_with_client(
            client=client, context=with_llm(llm=OpenAI(client=client))
        )
