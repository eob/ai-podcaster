import hashlib
import json
from typing import List, Union, Any
from pydantic import BaseModel, Field
from steamship import Block, Steamship, Task

from data.podcast_feed import FeedFile, RssFeed
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

        def feed_id(self) -> str:
            """Return a Feed ID based on the name for this podcast."""
            feed_id = hashlib.md5(self.podcast_name.encode()).hexdigest()
            return feed_id

        def get_or_create_feed_file(self, base_url: str, context: AgentContext) -> FeedFile:
            """Gets or creates the persistent Podcast Feed File associated with this premise."""
            feed_id = self.feed_id()
            rss_feed = RssFeed(
                title=self.podcast_name,
                summary=self.podcast_description,
                author="The AI Podcaster: github.com/eob/ai-podcaster"
            )
            feed_file = FeedFile.get_or_create(context.client, base_url, rss_feed)
            return feed_file

        @staticmethod
        def from_block(block: Block) -> "Output":
            podcast_premise = PodcastPremiseTool.Output.parse_obj(json.loads(block.text))
            return podcast_premise
            return podcast_premise

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

    agent_instance_base_url: str
    """The base URL of the agent instance."""

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

        for output_block in output:
            # Test Creating a Feed File
            podcast_premise = PodcastPremiseTool.Output.from_block(output_block)
            feed_file = podcast_premise.get_or_create_feed_file(self.agent_instance_base_url, context=context)
            rss = feed_file.to_rss(self.agent_instance_base_url, [])
            print(rss)

        return output

if __name__ == "__main__":
    """Note that the temporary workspace will mean that a DIFFERENT cache is used each time!
    
    To see the cache in action, provide a second (or third) input that is identical to the tool within the REPL.
    """
    with Steamship.temporary_workspace() as client:
        ToolREPL(PodcastPremiseTool(agent_instance_base_url="https://example.org")).run_with_client(
            client=client, context=with_llm(llm=OpenAI(client=client))
        )
