"""
Main user interface for the terminal chatbot (connect to nlip_web if time permits)
- handles conversation, follow-ups, and what-if scenarios
"""

from . import ollama_input, data_conversion, data_generator, analyzer, config, user_input, debug

def conversation():
    print("""
    Hello, I can estimate the queue values if you describe to me what your system is and what components it includes.
    Please include what you know about your system, such as the following information for each component:
        1. Name of components.
        2. Types of components (service, database, connection, etc.).
        3. Operating system of components.
        4. Description of components.
        5. Delay in seconds.
        6. Network speed in mbps.
        7. Message input and output types.
        8. Message size in bytes.
        9. How the components are connected (call, read, write, etc.).
        10. How often the components are used (i.e. probablity of going to each component).
        11. Any other relevant information, such as system version.
    """)

    system_description, system_description_path = ollama_input.ask_sys_desc()

    queue_network = data_conversion.system_to_queue(str(system_description_path))

    print(f"Converted system description {system_description_path} to {queue_network}")

    queue_data_name = data_generator.run(queue_network)

    print(queue_data_name)

    analyzer.run(queue_data_name)