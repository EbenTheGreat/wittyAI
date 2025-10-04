from langgraph.constants import END
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel
from typing import Annotated, List, Literal
from operator import add
from langgraph.graph import StateGraph
from config.prompt_builder import build_prompt_from_config
from utils import load_config
from llm import get_llm
from paths import PROMPT_CONFIG_FILE_PATH
from langchain_voyageai import VoyageAIEmbeddings
import os
from dotenv import load_dotenv
import json
from persistence import save_jokes_to_pinecone, is_duplicate_joke

load_dotenv()

# Define the state,
def get_embedding():
    embedding_model = VoyageAIEmbeddings(
        voyage_api_key=os.getenv("VOYAGE_API_KEY"),
        model="voyage-3.5",
    )

    return embedding_model


MAX_RETRIES = 5
CATALOG_FILE = "jokes_catalog.json"
class Joke(BaseModel):
    text: str
    category: str


class JokeState(BaseModel):
    jokes: Annotated[List[Joke], add] = []
    jokes_choice: Literal["n", "c", "l", "r", "b", "q"] = "n"
    joke_embeddings: List[List[float]] = []
    category: str = "general"
    language: str = "en"
    latest_jokes: str = ""
    approved_status: bool = False
    retry_count: int = 0
    quit: bool = False


prompt_config = load_config(PROMPT_CONFIG_FILE_PATH)

# Define the nodes
def show_menu(state: JokeState) -> dict:
    user_input = input("[n] Next [c] Category [l] Change language [r] Reset jokes [b] Browse saved jokes [q] Quit\n>").strip().lower()
    return {"jokes_choice": user_input}

def update_category(state: JokeState) -> dict:
    categories = ["dad developer", "chuck norris developer", "general"]
    selection = int(input("Select Category [0=dad developer, 1=chuck norris developer, 2=general]: ").strip())
    return {"category": categories[selection]}

def update_language(state: JokeState) -> dict:
    languages = ["cs", "de", "en", "es", "eu", "fr", "gl", "hu", "it", "lt", "pl", "ru", "sv"]
    selection = int(input("Select Language "
                          "[0=cs, 1=de, 2=en, 3=es, 4=eu, 5=fr, 6=gl, 7=hu, =8it, 9=lt, 10=pl, 11=ru, 12=sv]: \n>")
                    .strip())
    return {"language": languages[selection]}

def reset_jokes(state: JokeState) -> dict:
    print("\n Joke history has been reset\n")
    return {"jokes": []}

def make_writer_node(writer_llm):
    def writer_node(state: JokeState) -> dict:
        config = prompt_config["joke_writer_cfg"]
        prompt = build_prompt_from_config(config, input_data="")

        prompt += f"\\n\\nThe language is: {state.language}"
        prompt += f"\\n\\nThe category is: {state.category}"
        response = writer_llm.invoke(prompt)
        embedding = get_embedding().embed_query(str(response))

        return {"latest_jokes": response.content,
                "joke_embeddings": [embedding]}
    return writer_node


def make_human_critic_node():
    def make_human_critic(state: JokeState) -> dict:
        print("\n--- Human Critic ---")
        print("Here is the latest joke:\n")
        print(state.latest_jokes)

        decision = input("Do you find this joke funny? (yes/no) ").strip().lower()

        # Default assumption: not approved
        approved_status = False

        if decision in ["yes", "y"]:
            # Get embedding for this joke
            embedding = get_embedding().embed_query(state.latest_jokes)

            # Check Pinecone for duplicates
            if is_duplicate_joke(embedding):
                print(" This joke is too similar to an existing one. Skipping save.")
                approved_status = False
            else:
                approved_status = True
                # Store embedding in state so show_final_joke can persist it
                return {
                    "approved_status": approved_status,
                    "retry_count": state.retry_count,
                    "latest_jokes": state.latest_jokes,
                    "joke_embeddings": [embedding]
                }

        elif decision in ["no", "n"]:
            approved_status = False
        else:
            print("Invalid input. Defaulting to 'no'.")
            approved_status = False

        return {
            "approved_status": approved_status,
            "retry_count": state.retry_count + (0 if approved_status else 1),
            "latest_jokes": state.latest_jokes
        }
    return make_human_critic


def show_final_joke(state: JokeState) -> dict:
    joke = Joke(text=state.latest_jokes, category=state.category)
    print(f"\n Approved Joke: {joke.text}\n")

    if state.approved_status:
        if state.joke_embeddings:
            embeddings = state.joke_embeddings[-1]
        else:
            embeddings = [0.0] * 1024
        if not is_duplicate_joke(embeddings):
            save_jokes_to_pinecone(joke.text, state.category, embeddings)

    return {"jokes": [joke], "retry_count": 0, "approved_status": False, "latest_jokes": ""}


def browse_jokes(state: JokeState) -> dict:
    """
    LangGraph node: shows most recent saved jokes from the JSON catalog.
    Returns an empty dict (no state changes).
    """
    if not os.path.exists(CATALOG_FILE):
        print("\n No jokes saved yet.")
        return {}

    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    if not catalog:
        print("\n No jokes saved yet.")
        return {}

    print("\n--- Saved Jokes ---")
    # show most recent `limit` entries (same as before but hardcode 5)
    for entry in catalog[-5:]:
        print(f"- {entry['text']} ({entry['category']}, {entry['timestamp']})")

    # no state changes; return empty dict
    return {}



def exit_bot(state: JokeState) -> dict:
    return {"quit": True}


# define the edges
def writer_critic_loop(state: JokeState) -> dict:
    if state.approved_status:
        return "show_final_joke"
    elif state.retry_count >= MAX_RETRIES:
        print(f"\nNo joke was approved after {MAX_RETRIES} attempts.\n")
        print("Thanks for trying! Maybe come back when you're in a funnier mood \n")
        return "exit_bot"
    else:
        return "show_menu"

def route_choice(state: JokeState) -> str:
    if state.jokes_choice == "n":
        return "writer"
    if state.jokes_choice == "c":
        return "update_category"
    if state.jokes_choice == "l":
        return "update_language"
    if state.jokes_choice == "r":
        return "reset_jokes"
    if state.jokes_choice == "b":
        return "browse_jokes"

    if state.jokes_choice == "q":
        return "exit_bot"

    return "exit_bot"


def build_joke_graph(writer_model: str = "llama-3.1-8b-instant",
                     critic_model: str = "llama-3.1-8b-instant",
                     writer_temp: float = 0.95,
                     critic_temp: float = 0.1,
                     ) -> CompiledStateGraph:

    writer_llm = get_llm(writer_model, writer_temp)
    critic_llm = get_llm(critic_model, critic_temp)

    workflow = StateGraph(JokeState)
    
    workflow.add_node("show_menu", show_menu)
    workflow.add_node("writer", make_writer_node(writer_llm))
    # workflow.add_node("critic", make_critic_node(critic_llm))
    workflow.add_node("critic", make_human_critic_node())
    workflow.add_node("show_final_joke", show_final_joke)
    workflow.add_node("update_category", update_category)
    workflow.add_node("update_language", update_language)
    workflow.add_node("reset_jokes", reset_jokes)
    workflow.add_node("browse_jokes", browse_jokes)
    workflow.add_node("exit_bot", exit_bot)

    workflow.set_entry_point("show_menu")

    workflow.add_conditional_edges(
        "show_menu",
        route_choice,
        {
            "writer": "writer",
            "update_category": "update_category",
            "update_language": "update_language",
            "reset_jokes": "reset_jokes",
            "browse_jokes": "browse_jokes",
            "exit_bot": "exit_bot"
        }
    )

    workflow.add_edge("writer", "critic")

    workflow.add_conditional_edges(
        "critic",
        writer_critic_loop,
        {
            "writer": "writer",
            "show_final_joke": "show_final_joke",
            "show_menu": "show_menu",
            "exit_bot": "exit_bot"
        }
    )

    workflow.add_edge("show_final_joke", "show_menu")
    workflow.add_edge("update_category", "show_menu")
    workflow.add_edge("update_language", "show_menu")
    workflow.add_edge("reset_jokes", "show_menu")
    workflow.add_edge("browse_jokes", "show_menu")

    workflow.add_edge("exit_bot", END)

    return workflow.compile()


def main():
    graph = build_joke_graph()

    # with open("graph.mmd", "w") as f:
    #     f.write(graph.get_graph().draw_mermaid())

    final_state = graph.invoke(JokeState(), config={"recursion_limit": 100})
main()
