import random
from typing import Any, List, Union

from steamship import Block, Steamship, SteamshipError, Task
from steamship.agents.llms import OpenAI
from steamship.agents.schema import AgentContext, Tool
from steamship.agents.utils import get_llm, with_llm
from steamship.utils.repl import ToolREPL

DEFAULT_PROMPT = """INSTRUCTIONS:
Generate a JSON object describing {table_description}. 
Always return a non-empty value for every field in the object.

FIELDS DESIRED:
{fields_desired}

EXAMPLE OBJECTS:
{example_objects}

NEW OBJECT:
{new_object_prefix}
"""

DEFAULT_TABLE_DESCRIPTION = "employees of a company"
DEFAULT_HEADER_FIELDS = ["Name", "Age", "Gender"]
DEFAULT_EXAMPLE_ROWS = [
    ["Bob", 30, "Male"],
    ["Susan", 32, "Female"],
    ["Zhenzhong", 40, "Male"],
    ["Luis", 32, "Male"],
    ["Roberta", 35, "Female"],
    ["Sofia", 30, "Female"],
]
DEFAULT_NEW_ROW_PREFIX_FIELDS = []


class JsonObjectGeneratorTool(Tool):
    """
    Example tool to illustrate generating a new JSON object provided a set of examples.

    Examples might be:

    - A person's imaginary name, gender, and age
    - The title and description of a podcast episode

    The input parameters are framed as a database table.
    """

    rewrite_prompt: str = DEFAULT_PROMPT
    table_description: str = DEFAULT_TABLE_DESCRIPTION
    header_fields: List[str] = DEFAULT_HEADER_FIELDS
    example_rows: List[List[str]] = DEFAULT_EXAMPLE_ROWS
    new_row_prefix_fields: List[str] = DEFAULT_NEW_ROW_PREFIX_FIELDS

    name: str = "TsvRowTool"
    human_description: str = "Generates a new row of a TSV file."
    agent_description: str = "(set at initialization time)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_description = (
            f"Used to generate an instance of the {self.table_description} table. "
            "Input: Anything. "
            f"Output A tab-separated row describing a new instance of the {self.table_description} table."
        )

    def kv_clause(self, key: str, value: str):
        value = str(value).replace("\"", "\\\"")
        clause = f"\"{key}\": \"{value}\""
        return clause


    def object_json(self, schema: List[str], values: List[str]):
        clauses = []
        for field, value in zip(schema, values):
            clauses.append(self.kv_clause(field, value))
        
        return "{" + ", ".join(clauses) + "}"

        

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

        # Compile the prompt based entirely on the tool configuration.
        random.shuffle(self.example_rows)
        example_objects = [self.object_json(self.header_fields, example_row) for example_row in self.example_rows]
        example_objects_str = "\n".join(example_objects)

        new_object_prefix = "{"
        for i in range(len(self.new_row_prefix_fields)):
            clause = self.kv_clause(self.header_fields[i], self.new_row_prefix_fields[i])
            new_object_prefix += f"{clause}, "

        prompt = self.rewrite_prompt.format(
            table_description=self.table_description,
            fields_desired=", ".join(self.header_fields),
            example_objects=example_objects_str,
            new_object_prefix=new_object_prefix
        )

        llm = get_llm(context)
        res =  llm.complete(prompt, stop="}")
        blocks_emitted = len(res)
                             
        if blocks_emitted != 1:
            raise SteamshipError(message=f"{len(blocks_emitted)} blocks emitted; expecting 1.")
        
        full_json = new_object_prefix + res[0].text + "}"
        res[0].text = full_json
        return res

        
if __name__ == "__main__":
    with Steamship.temporary_workspace() as client:
        ToolREPL(JsonObjectGeneratorTool()).run_with_client(
            client=client, context=with_llm(llm=OpenAI(client=client))
        )
