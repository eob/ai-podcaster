from typing import List, Union, Any
from steamship import Steamship, Block, Task
from repl import ToolREPL
import json
from steamship.agents.schema import AgentContext, Tool
from steamship.agents.utils import get_llm, with_llm
from steamship.agents.llms import OpenAI
from tools.podcast_premise_tool import PodcastPremiseTool
from tools.json_object_generator_tool import JsonObjectGeneratorTool

class PodcastEpisodePremiseTool(JsonObjectGeneratorTool):    
    name: str = "PodcastEpisodePremiseTool"
    human_description: str = "Generates a premise for a podcast episode."
    agent_description: str = (
        "Used to generate a premise for a new podcast episode. ",
        "Use this tool if a user asks for an idea for a new podcast episode. ",
        "Input: The desire for a new podcast episode. "
        "Output: The name and description of a podcast episode the user could create."
    )

    table_description: str = "podcast episodes"
    header_fields: List[str] = ["Podcast Name", "Episode Name", "Episode Description"]
    example_rows: List[List[str]] = [
      ["Animal Planet", "Wolverines", "What Wolverines eat in the wild."],
      ["Banking News", "Today's Banking News", "All the updates you need to track the banking world."],
      ["Hollywood Gab", "Guest: Tommy Lee Jones", "What does a retired actor do when he's not in an action movie?"],
      ["The MIT Tech Review", "Sound Lasers", "Soon, we may be directing sound from afar, straight into your head."],
      ["Politico", "What Biden Needs", "Polls got you down? We've got the answer. Everything Biden needs to win the public."],
      ["Car Talk", "A Man. A Sedan. A Mystery.",
      "A caller from Boston has a car that turns off when me makes a left-hand turn."],
    ]

    def __init__(self, podcast_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_row_prefix_fields = [podcast_name]

    def run(self, tool_input: List[Block], context: AgentContext) -> Union[List[Block], Task[Any]]:
        # Pull the premise.
        # TODO: This reloads the previously generated one.
        premise_tool = PodcastPremiseTool()
        premise_blocks = premise_tool.run([], context)
        podcast_premise: PodcastPremiseTool.Output = premise_tool.parse_final_output(premise_blocks[0])
                
        # Set the prefix fields
        self.new_row_prefix_fields = [podcast_premise.podcast_name]
        
        # Now just return the regular output.
        blocks = super().run(tool_input, context)

        for block in blocks:
            block_dict = json.loads(block.text)
            block_dict.update(podcast_premise.dict())
            block.text = json.dumps(block_dict)
        
        return blocks


if __name__ == "__main__":
    with Steamship.temporary_workspace() as client:
        ToolREPL(PodcastEpisodePremiseTool("The Cheese Podcast")).run_with_client(
            client=client, context=with_llm(llm=OpenAI(client=client))
        )
