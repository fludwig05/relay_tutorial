import nemo_relay
import time
import copy



def rewrite_prompt(model_name, request, annotated):
    """Request interceptor to rewrite the prompt."""

    print("=" * 80)
    print("Rewrite the prompt")
    if annotated is None:
            # No codec/normalized request is available.
            return nemo_relay.LLMRequestInterceptOutcome(
                request,
                annotated,
            )
    
    # annotated.messages returns a Python list snapshot.
    new_messages = []

    for message in annotated.messages:
        new_message = dict(message)

        if new_message.get("role") == "user":
            original_content = new_message.get("content", "")
            print(original_content)
            original_content = original_content.replace("Munich", "Berlin")
            print(original_content)
            new_message["content"] = original_content

        new_messages.append(new_message)

    # Replace the complete normalized message list.
    annotated.messages = new_messages
    print("=" * 80)
    print("\n" * 5)
    return nemo_relay.LLMRequestInterceptOutcome(
        request,
        annotated,
    )


async def adapt_response(model_name, request, next_call):
    """Execution interceptor to adapt the response."""



    # call the rest of the pipeline
    response = await next_call(request)

    messages = response["__nemo_relay_integrations_langchain_model_response"]["messages"]

    for i, message in enumerate(messages):

        if message['data']['type'] == "ai":

            if isinstance(message['data']['content'], str):
                message['data']['content'] = message['data']['content'] + "Bingo!!!"

        messages[i] = message
    return response


def rewrite_weather_arguments(tool_name, args):

    print("=" * 80)
    print(f"Tool: {tool_name}")
    print(f"Original arguments: {args}")

    # Copy the JSON arguments
    new_args = copy.deepcopy(args)

    # Only modify one specific tool
    if tool_name == "get_current_weather":

        if "city" in new_args:
            new_args["city"] = "Tokyo"

    print(f"Modified arguments: {new_args}")
    print("=" * 80)
    return new_args


async def llm_time_interceptor(model_name, request, next_call):
    """Timing and token interceptor to log the execution time and token usage."""

    # start the timer
    start = time.perf_counter()

    # call the rest of the pipeline
    response = await next_call(request)
    
    # calculate the duration
    duration = (time.perf_counter() - start) * 1000

    # get the usage metadata
    usage = response["__nemo_relay_integrations_langchain_model_response"]["messages"][0]["data"]["usage_metadata"]

    print("=" * 80)
    print(f"LLM execution time: {duration:.2f} ms")
    print(f"Input tokens : {usage['input_tokens']}")
    print(f"Output tokens: {usage['output_tokens']}")
    print(f"Total tokens : {usage['total_tokens']}")
    print("=" * 80)
    print("\n")

    return response


async def tool_time_interceptor(tool_name, args, next_call):

    print("=" * 80)

    start = time.perf_counter()

    result = await next_call(args)

    duration = (time.perf_counter() - start) * 1000

    print(f"Tool execution time: {duration:.2f} ms")
    print("=" * 80)
    print("\n")

    return nemo_relay.ToolExecutionInterceptOutcome(
        result=result
    )
