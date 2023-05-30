from typing import List, Union, Any
from steamship import Steamship, Block, Task
from repl import ToolREPL
import json
from pydantic import Field
from steamship.agents.schema import AgentContext, Tool
from steamship.agents.utils import get_llm, with_llm
from steamship.agents.llms import OpenAI
from tools.podcast_premise_tool import PodcastPremiseTool
from steamship.agents.tools.text_generation import JsonObjectGeneratorTool

class PodcastEpisodePremiseTool(JsonObjectGeneratorTool):    
    class Output(PodcastPremiseTool.Output):
        episode_name: str = Field()
        episode_description: str = Field()

    name: str = "PodcastEpisodePremiseTool"
    human_description: str = "Generates a premise for a podcast episode."
    agent_description: str = (
        "Used to generate a premise for a new podcast episode. ",
        "Use this tool if a user asks for an idea for a new podcast episode. ",
        "Input: The desire for a new podcast episode. "
        "Output: The name and description of a podcast episode the user could create."
    )

    plural_object_description: str = "podcast episodes"
    object_keys: List[str] = ["podcast_name", "episode_name", "episode_description"]
    example_rows: List[List[str]] = [
      ["Animal Planet", "Wolverines", "What Wolverines eat in the wild."],
      ["Banking News", "Today's Banking News", "All the updates you need to track the banking world."],
      ["Hollywood Gab", "Guest: Tommy Lee Jones", "What does a retired actor do when he's not in an action movie?"],
      ["The MIT Tech Review", "Sound Lasers", "Soon, we may be directing sound from afar, straight into your head."],
      ["Politico", "What Biden Needs", "Polls got you down? We've got the answer. Everything Biden needs to win the public."],
      ["Car Talk", "A Man. A Sedan. A Mystery.",
      "A caller from Boston has a car that turns off when me makes a left-hand turn."],
    ]

    def run(self, tool_input: List[Block], context: AgentContext) -> Union[List[Block], Task[Any]]:
        # Pull the premise.
        # TODO: This reloads the previously generated one.
        premise_tool = PodcastPremiseTool()
        premise_blocks = premise_tool.run([], context)
        podcast_premise: PodcastPremiseTool.Output = premise_tool.parse_final_output(premise_blocks[0])
                
        # Set the prefix fields
        self.new_row_prefix_fields = [podcast_premise.podcast_name]
        
        # Now run the promopt
        blocks = super().run(tool_input, context)

        # To make things easier we're going to fold in the output from the PodcastPremiseTool into 
        # every output of this as well. This makes sure that this tool output stands on its own; we don't
        # need some downstream tool to combine the output of multiple tools.
        for block in blocks:
            block_dict = json.loads(block.text)
            block_dict.update(podcast_premise.dict())
            block.text = json.dumps(block_dict)
        
        return blocks

    def parse_final_output(self, block: Block) -> Output:
        """Parses the final output"""
        print(block.text)
        return PodcastEpisodePremiseTool.Output.parse_obj(json.loads(block.text))


if __name__ == "__main__":
    with Steamship.temporary_workspace() as client:
        ToolREPL(PodcastEpisodePremiseTool()).run_with_client(
            client=client, context=with_llm(llm=OpenAI(client=client))
        )
