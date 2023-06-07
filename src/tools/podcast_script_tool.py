from typing import List, Union, Any
import json
from steamship import Steamship, Block, Task
from pydantic import Field
from steamship.utils.kv_store import KeyValueStore

from repl import ToolREPL
from steamship.agents.schema import AgentContext, Tool
from steamship.agents.utils import get_llm, with_llm
from steamship.agents.llms import OpenAI
from tools.podcast_episode_premise_tool import PodcastEpisodePremiseTool

DEFAULT_PROMPT = """INSTRUCTIONS:
Generate a transcript for a two minute long podcast episode. 
Complete the transcript with the capitalized phrase: THE END.

PODCAST TITLE:
{podcast_title}

PODCAST DESCRIPTION:
{podcast_description}

EPISODE TITLE:
{episode_title}

EPISODE DESCRIPTION:
{episode_description}

EPISODE TRANSCRIPT:"""

class PodcastTranscriptGeneratorTool(Tool):    
    kv_store: KeyValueStore

    class Output(PodcastEpisodePremiseTool.Output):
        script: str = Field(alias="Script")
    
    name: str = "PodcastTranscriptGeneratorTool"
    human_description: str = "Generates a transcript for a podcast episode."
    agent_description: str = (
        "Used to generate a premise for a new podcast episode. ",
        "Use this tool if a user asks for an idea for a new podcast episode. ",
        "Input: The desire for a new podcast episode. "
        "Output: The name and description of a podcast episode the user could create."
    )

    def run(self, tool_input: List[Block], context: AgentContext) -> Union[List[Block], Task[Any]]:
        """Ignore tool input and generate a new single row of a table described by the tool's configuration.

        Inputs
        ------
        input: List[Block]
            A list of blocks that will be ignored.
        memory: AgentContext
            The active AgentContext.

        Output
        ------
        output: List[Blocks]
            A single block containing a new row of the table described by the tool's configuration.
        """

        episode_premise_tool = PodcastEpisodePremiseTool(self.kv_store)
        episode_premise_blocks = episode_premise_tool.run([], context)
        episode_premise: PodcastEpisodePremiseTool.Output = episode_premise_tool.parse_final_output(episode_premise_blocks[0])

        llm = get_llm(context)

        prompt = DEFAULT_PROMPT.format(
            podcast_title=episode_premise.podcast_name,
            podcast_description=episode_premise.podcast_description,
            episode_title=episode_premise.episode_name,
            episode_description=episode_premise.episode_description,
        )

        blocks = llm.complete(prompt, stop="THE END")
        block = blocks[0]

        d = episode_premise.dict()
        d["script"] = block.text
        print(block.text)

        block.text = json.dumps(d)
        return [block]
        
    def __init__(self, kv_store: KeyValueStore):
        self.kv_store = kv_store


if __name__ == "__main__":
    with Steamship.temporary_workspace() as client:
        kv_store = KeyValueStore()
        ToolREPL(PodcastTranscriptGeneratorTool(kv_store)).run_with_client(
            client=client, context=with_llm(llm=OpenAI(client=client))
        )
