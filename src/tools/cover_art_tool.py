"""Tool for generating images."""
from typing import List, Union, Any

from steamship import Block, Task
from steamship.agents.schema import AgentContext
from steamship.agents.tools.base_tools import ImageGeneratorTool
from steamship.agents.tools.image_generation.stable_diffusion import StableDiffusionTool
from steamship.utils.repl import ToolREPL


class CoverArtTool(ImageGeneratorTool):
    """Tool to generate the Cover Art for the podcast.

    This example illustrates wrapping a tool (StableDiffusionTool) with a fixed prompt template that is combined with user input.
    """

    name: str = "CoverArtTool"
    human_description: str = "Generates a Cover Art for a Podcast."
    agent_description = (
        "Used to generate cover art for a podcast. "
        "Only use if the user has asked directly for cover art and included the podcast title. "
        "Input: title of the podcast. "
        "Output: the cover art image."
    )
    generator_plugin_handle = "stable-diffusion"

    prompt_template = ("music album cover, digital art, background for: {subject}, "
                       "mattepaint, concept art, artstation, photomanipulation, 3d render, movie poster, kinetic art, "
                       "hires, high definition, award winning, no text, art only"
                       )

    def run(self, tool_input: List[Block], context: AgentContext) -> Union[List[Block], Task[Any]]:
        # Modify the tool inputs by interpolating them with stored prompt here
        modified_inputs = [Block(text=self.prompt_template.format(subject=block.text)) for block in tool_input]

        # Create the Stable Diffusion tool we want to wrap
        stable_diffusion_tool = StableDiffusionTool()

        # Now return the results of running Stable Diffusion on those modified prompts.
        return stable_diffusion_tool.run(modified_inputs, context)


if __name__ == "__main__":
    print("Try running with an input like 'The Tech AI Podcast'")
    ToolREPL(CoverArtTool()).run()
