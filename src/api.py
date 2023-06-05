import uuid
from typing import List

from steamship import Block
from steamship.agents.schema import AgentContext, Metadata
from steamship.agents.llms import OpenAI
from steamship.agents.react import ReACTAgent

from steamship.agents.tools.image_generation.google_image_search import GoogleImageSearchTool
from steamship.agents.tools.search.search import SearchTool
from steamship.experimental.package_starters.telegram_agent import TelegramAgentService
from steamship.invocable import post
from steamship.utils.repl import AgentREPL

from utils import print_blocks

SYSTEM_PROMPT = """You are Jeff, a podcast producer who helps plan, write, and record podcasts.

Who you are:
- You are a helpful assistant for planning podcasts.
- You enjoy chatting about ideas for new content.

How you behave: 
- NEVER say you're here to assist. Keep conversations casual.
- NEVER ask how you can help or assist. Keep conversations casual.
- You always sounds happy and enthusiastic.
- Help explain the tools you have access to and how to use them.

TOOLS:
------

You have access to the following tools:
{tool_index}

To use a tool, please use the following format:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a final response to say to the Human, or if you do not need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
AI: [your final response here]
```

Make sure to use all observations to come up with your final response.

Begin!

New input: {input}
{scratchpad}"""


class PodcastProducerJeff(TelegramAgentService):
    """Deployable Multimodal Agent that lets you talk to Google Search & Google Images.

    NOTE: To extend and deploy this agent, copy and paste the code into api.py.

    """

    def __init__(self, **kwargs):
        super().__init__(incoming_message_agent=None, **kwargs)
        # The agent's planner is responsible for making decisions about what to do for a given input.
        self.incoming_message_agent = ReACTAgent(
            tools=[
                SearchTool(),
                GoogleImageSearchTool()
            ],
            llm=OpenAI(self.client),
        )
        self.incoming_message_agent.PROMPT = SYSTEM_PROMPT

    @post("prompt")
    def prompt(self, prompt: str) -> str:
        """ This method is only used for handling debugging in the REPL """
        context_id = uuid.uuid4()
        context = AgentContext.get_or_create(self.client, {"id": f"{context_id}"})
        context.chat_history.append_user_message(prompt)

        output = ""
        def sync_emit(blocks: List[Block], meta: Metadata):
            nonlocal output
            block_text = print_blocks(self.client, blocks)
            output += block_text

        context.emit_funcs.append(sync_emit)
        self.run_agent(self.incoming_message_agent, context)
        return output


if __name__ == "__main__":
    AgentREPL(GoogleChatbot,
              method="prompt",
              agent_package_config={'botToken': 'not-a-real-token-for-local-testing'}).run()
