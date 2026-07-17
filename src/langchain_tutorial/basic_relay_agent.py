# nemo-relay imports
from nemo_relay.integrations.langchain import NemoRelayMiddleware, NemoRelayCallbackHandler
from nemo_relay import plugin
import nemo_relay

# langgraph imports
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

# langchain imports
from langchain.tools import ToolRuntime, tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

# other imports
from dataclasses import dataclass
from dotenv import load_dotenv
import asyncio
import time


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

        # send an event that the memory store is unavailable
        nemo_relay.scope.event("memory.unavailable", data={"operation": "write"})
        return "Memory store is unavailable."

    user_id = runtime.context.user_id
    namespace = ("users", user_id, "information")

    runtime.store.put(namespace, information_name, {"value": information_value})

    # send an event that the memory has been updated
    nemo_relay.scope.event("memory.updated", handle=runtime.scope_handle,
                           data={"user_id": user_id, "key": information_name})

    return f"Saved information: {information_name}"   


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

        # create a scope input
        scope_input = {"thread_id": current_thread, "user_id": user_id, "user_input": user_input}

        # push a scope for the agent turn
        scope_handle = nemo_relay.scope.push("agent-turn", nemo_relay.ScopeType.Agent, input=scope_input)

        # initialize the response and error
        response, error = None, None

        try:

                # send an event that the agent input has been received
                nemo_relay.scope.event("agent.input.received", handle=scope_handle)

                # run the agent
                response = agent.invoke(create_user_message(user_input), context=context, 
                                        config={**memory_config, "callbacks": [NemoRelayCallbackHandler()]})
            
                final_message = response["messages"][-1]
                print(f"Assistant: {final_message.content}\n")  

                # send an event that the agent response has been generated
                nemo_relay.scope.event("agent.response.generated", handle=scope_handle)           

        except Exception as exc:

            # send an event that the agent failed
            nemo_relay.scope.event("agent.failed", handle=scope_handle, data={"error": str(exc)})

        finally:

            # initialize the output
            output = {}

            # set the output
            if response is not None:
                output["assistant_response"] = response["messages"][-1].content

            # set the error
            if error is not None:
                output["error"] = error

            # pop the scope and set the output
            nemo_relay.scope.pop(scope_handle, output=output)   


async def main(user_id):

    # set the environment variables
    load_dotenv()

    # configure the plugin
    config = plugin.PluginConfig()

    # initialize the plugin
    report = await plugin.initialize(config)
    print(report)

    # define a model
    model = ChatOpenAI(model="demo", api_key="dummy", base_url="http://localhost:4000/v1")

    # checkpointer for short term memory
    checkpointer = InMemorySaver()

    # store for long term memory
    store = InMemoryStore()

    # define the system prompt
    system_prompt = "You are a helpful assistant that can save and retrieve information for the current user."

    try:

        # create an agent
        agent = create_agent(model=model, tools=[get_current_weather, save_user_information, get_user_information], checkpointer=checkpointer, 
                            store=store, context_schema=Context, system_prompt=system_prompt, middleware=[NemoRelayMiddleware()])

        # run the agent loop
        agent_loop(agent, user_id)
    
    finally:

        plugin.clear()


if __name__ == '__main__':

    # ids for user
    user_id = "user_1"
    
    # run the main function
    asyncio.run(main(user_id))
