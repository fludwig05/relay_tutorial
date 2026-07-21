from pprint import pprint
import nemo_relay
import time


def rewrite_prompt(model_name, request, annotated):

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

            original_content = original_content.replace("Munich", "Berlin")

            new_message["content"] = original_content

        new_messages.append(new_message)

    # Replace the complete normalized message list.
    annotated.messages = new_messages

    return nemo_relay.LLMRequestInterceptOutcome(
        request,
        annotated,
    )


async def timing_and_token_interceptor(model_name, request, next_call):

    # start the timer
    start = time.perf_counter()

    # call the rest of the pipeline
    response = await next_call(request)
    
    # calculate the duration
    duration = (time.perf_counter() - start) * 1000

    # get the usage metadata
    usage = response["__nemo_relay_integrations_langchain_model_response"]["messages"][0]["data"]["usage_metadata"]

    print("=" * 80)
    print(f"Model: {model_name}")
    print(f"Execution time: {duration:.2f} ms")
    print(f"Input Tokens : {usage['input_tokens']}")
    print(f"Output Tokens: {usage['output_tokens']}")
    print(f"Total Tokens : {usage['total_tokens']}")
    print("=" * 80)

    return response


async def adapt_response(model_name, request, next_call):

    # call the rest of the pipeline
    response = await next_call(request)

    messages = response["__nemo_relay_integrations_langchain_model_response"]["messages"]

    for i, message in enumerate(messages):

        if message['data']['type'] == "ai":

            if isinstance(message['data']['content'], str):
                message['data']['content'] = message['data']['content'].replace("Berlin", "Mexico City")
        messages[i] = message
            
    return response
