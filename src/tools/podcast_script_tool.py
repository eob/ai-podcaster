from typing import List
import json
from steamship import Steamship
from steamship.utils.repl import ToolREPL
from steamship.agents.schema import AgentContext, Tool
from steamship.agents.utils import get_llm, with_llm
from steamship.agents.llms import OpenAI
from src.tools.podcast_episode_premise_tool import PodcastEpisodePremiseTool
from tools.json_object_generator_tool import JsonObjectGeneratorTool

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

        llm = get_llm(context)

        blocks = []
        for block in tool_input:
            # If the block is not text, simply pass it through.
            if not block.is_text():
                continue
                
            # I gotta be honest: I'm not really sure how we can reasonably expect an LLM to provide
            # properly formatted input. But I want to structure this AS IF IT WERE because I'm confident
            # we'll figure it out.
            #
            # So! I'm assuming this will have the output.
            input_json = json.loads(block.text)

            podcast_title = input_json.get("Podcast Name", "")
            podcast_description = input_json.get("Podcast Description", "")
            episode_title = input_json.get("Episode Name", "")
            episode_description = input_json.get("Episode Description", "")

            prompt = self.rewrite_prompt.format(
                podcast_title=podcast_title,
                podcast_description=podcast_description,
                episode_title=episode_title,
                episode_description=episode_description,
            )

            res =  llm.complete(prompt, stop="}")
            blocks.extend(res)
        return blocks


if __name__ == "__main__":
    with Steamship.temporary_workspace() as client:
        ToolREPL(PodcastTranscriptGeneratorTool("The Cheese Podcast")).run_with_client(
            client=client, context=with_llm(llm=OpenAI(client=client))
        )
