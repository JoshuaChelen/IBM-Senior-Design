
from .user_input import UserInput
from . import config, data_conversion, user_input, data_generator, analyzer, ollama_input
from pathlib import Path

def pipeline(system_description_file):
    """
    Run end to end from system description file to an analyzer result json. 

    system_description_file - file name of system description (i.e., simple_system_description_example.json)
    """

    project_root = Path(__file__).resolve().parent.parent

    system_description_path = (
         project_root / "data" / "system-description" / system_description_file
    ).resolve()

    queue_network = data_conversion.system_to_queue(str(system_description_path))

    queue_data_name = data_generator.run(queue_network)

    analyzer_json = analyzer.json_output(queue_data_name)

    return analyzer_json

# Running function with an example 
# pipeline("simple_system_description_example.json")