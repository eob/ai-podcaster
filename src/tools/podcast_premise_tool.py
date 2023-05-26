from typing import List
from steamship import Steamship
from steamship.utils.repl import ToolREPL
from steamship.agents.schema import AgentContext, Tool
from steamship.agents.utils import get_llm, with_llm
from steamship.agents.llms import OpenAI
from tools.tsv_row_generator_tool import TsvRowGeneratorTool

class PodcastPremiseTool(TsvRowGeneratorTool):    
    name: str = "PodcastPremiseTool"
    human_description: str = "Generates a premise for a podcast."
    agent_description: str = (
        "Used to generate a premise for a new podcast. ",
        "Use this tool if a user asks for an idea for a new podcast. ",
        "Input: The desire for a new podcast. "
        "Output: The name and description of a podcast the user could create."
    )

    table_description: str = "podcasts"
    header_fields: List[str] = ["Podcast Name", "Podcast Description"]
    example_rows: List[List[str]] = [
        ["Animal Planet", "The world is an amazing place. We'll tell you its stories every day."],
        ["Banking News", "All the updates you need to track the banking world."],
        ["Hollywood Gab", "The latest stories from inside Hollywood."],
        ["The MIT Tech Review", "The latest in science and technology, explained."],
        ["Politico", "Hear the opinions and analysis that shapes capitol hill."],
        ["Car Talk", "Call-in show with automotive mysteries, fix-it help, and laughter."],
    ]


if __name__ == "__main__":
    with Steamship.temporary_workspace() as client:
        ToolREPL(PodcastPremiseTool()).run_with_client(
            client=client, context=with_llm(llm=OpenAI(client=client))
        )
