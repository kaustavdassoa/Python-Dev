from google.adk.agents import SequentialAgent
from plsql_converter.agents.parser_agent import parser_agent
from plsql_converter.agents.analyzer_agent import analyzer_agent
from plsql_converter.agents.converter_agent import converter_agent
from plsql_converter.agents.validator_agent import validator_agent

root_agent = SequentialAgent(
    name="plsql_to_csharp_orchestrator",
    description=(
        "Orchestrates the conversion of a PL/SQL stored procedure into a compilable C# method body. "
        "Runs four specialist agents in sequence: Parser → Analyzer → Converter → Validator."
    ),
    sub_agents=[
        parser_agent,
        analyzer_agent,
        converter_agent,
        validator_agent,
    ],
)
