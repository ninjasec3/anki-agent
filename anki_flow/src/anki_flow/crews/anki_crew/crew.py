from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import Any, Dict, List, cast
from anki_flow.crews.tools.custom_tool import ReadMarkdownFolderTool, AnkiConnectAddNotesTool
from crewai_tools import (
    FileReadTool,
    DirectoryReadTool,
    TXTSearchTool,
    PDFSearchTool,
    DOCXSearchTool,
    CSVSearchTool,
    JSONSearchTool,
    XMLSearchTool,
)
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class AnkiCrew():
    """AnkiCrew crew"""

    agents: List[BaseAgent]
    tasks: List[Task]
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def flashcard_generator(self) -> Agent:
        agents_cfg = cast(Dict[str, Any], self.agents_config)
        return Agent(
            config=agents_cfg['flashcard_generator'], # type: ignore[index]
            tools=[
                ReadMarkdownFolderTool(),
                DirectoryReadTool(),
                FileReadTool(),
                TXTSearchTool(),
                PDFSearchTool(),
                DOCXSearchTool(),
                CSVSearchTool(),
                JSONSearchTool(),
                XMLSearchTool(),
            ],
            verbose=True,
        )

    @agent
    def anki_uploader(self) -> Agent:
        agents_cfg = cast(Dict[str, Any], self.agents_config)
        return Agent(
            config=agents_cfg['anki_uploader'], # type: ignore[index]
            tools=[AnkiConnectAddNotesTool()],
            verbose=True,
        )

    @task
    def generate_flashcards(self) -> Task:
        tasks_cfg = cast(Dict[str, Any], self.tasks_config)
        return Task(
            config=tasks_cfg['generate_flashcards'], # type: ignore[index]
        )

    @task
    def upload_to_anki(self) -> Task:
        tasks_cfg = cast(Dict[str, Any], self.tasks_config)
        return Task(
            config=tasks_cfg['upload_to_anki'], # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the AnkiCrew crew"""

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
