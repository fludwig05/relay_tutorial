# langgraph imports
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

# langchain imports
from langchain.chat_models import init_chat_model
from langchain.tools import ToolRuntime, tool
from langchain.agents import create_agent

# other imports
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Context:
    user_id: str


@tool
def get_current_weather(city: str) -> str:
    """Get the current weather for a given city."""
    output = "The weather in {city} is snowy.".format(city=city)
    return output


@tool
def save_user_information(information_name: str, information_value: str, runtime: ToolRuntime[Context]) -> str:
    """Save persistent information for the current user."""
    if runtime.store is None:
        return "Memory store is unavailable."

    user_id = runtime.context.user_id
    namespace = ("users", user_id, "information")

    runtime.store.put(namespace, information_name, {"value": information_value})
    return f"Saved information: {information_name} = {information_value}"    


@tool
def get_user_information(runtime: ToolRuntime[Context]) -> str:
    """Retrieve all persistent information for the current user."""
    
    if runtime.store is None:
        return "Memory store is unavailable."

    user_id = runtime.context.user_id
    namespace = ("users", user_id, "information")

    memories = runtime.store.search(namespace)

    if not memories:
        return "No information has been saved."

    information = {memory.key: memory.value["value"] for memory in memories}
    return str(information)


def create_user_message(user_input):
    return {"messages": [{"role": "user", "content": user_input}]}


def create_memory_config(user_id, thread_id):
    return {"configurable": {"user_id": user_id, "thread_id": thread_id}}


def get_user_input(current_thread: str):
    try:
        user_input = input(f"[{current_thread}] You: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye.")
        return None
    return user_input


def agent_loop(agent, user_id):

    # provide the user with the instructions
    print("Type 'quit' or 'exit' to stop.\n")

    # create an initial thread
    current_thread = "thread_1"

    # loop until the user quits
    while True:

        # get the user input
        user_input = get_user_input(current_thread)

        # check if the user wants to quit
        if user_input is None or user_input == "/quit":
            break

        if user_input.startswith("/new "):
            current_thread = user_input.split(maxsplit=1)[1]
            print(f"Switched to {current_thread}")
            continue

        elif user_input.startswith("/use "):
            current_thread = user_input.split(maxsplit=1)[1]
            print(f"Switched to {current_thread}")
            continue

        # get the config of the current memory
        memory_config = create_memory_config(user_id, current_thread)

        # create the context
        context = Context(user_id=user_id)

        try:

            # run the agent
            response = agent.invoke(create_user_message(user_input), config=memory_config, context=context)
        
            final_message = response["messages"][-1]
            print(f"Assistant: {final_message.content}\n")

        except Exception as exc:
            print(f"Error while running the agent: {exc}\n")


def main(user_id):

    # set the environment variables
    load_dotenv()

    # define a model
    model = init_chat_model(model="gpt-4.1", model_provider="openai")

    # checkpointer for short term memory
    checkpointer = InMemorySaver()

    # store for long term memory
    store = InMemoryStore()

    # define the system prompt
    system_prompt = "You are a helpful assistant that can save and retrieve information for the current user."

    # create an agent
    agent = create_agent(model=model, tools=[get_current_weather, save_user_information, get_user_information], checkpointer=checkpointer, 
                         store=store, context_schema=Context, system_prompt=system_prompt)

    # run the agent loop
    agent_loop(agent, user_id)


if __name__ == '__main__':

    # ids for user
    user_id = "user_1"
    
    # run the main function
    main(user_id)
