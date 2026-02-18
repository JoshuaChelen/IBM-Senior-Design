from program_files import config, data_conversion, user_input, data_generator, analyzer, ollama_input
from pathlib import Path

def print_new_section(title:str):
    print(f"\n"
          f"==================\n"
          f"{title}\n"
          f"==================\n"
          )

def get_files_in_directory(relative_path: str) -> list[str]:
    """
    Return a list of file names inside a directory.
    The directory path is interpreted relative to the project root
    (i.e., the directory where main.py lives).
    """
    # Project root is the directory containing THIS file (main.py)
    project_root = Path(__file__).resolve().parent

    target_dir = (project_root / relative_path).resolve()

    if not target_dir.exists():
        raise FileNotFoundError(f"Directory does not exist: {target_dir}")

    if not target_dir.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {target_dir}")

    return [f.name for f in target_dir.iterdir() if f.is_file()]

def test_config():
    print_new_section("Config")

    print("Choose a method to test\n"
          "0 - get_config()\n"
          "1 - set_config_value()\n"
    )
    method = input()

    files = get_files_in_directory("./config")
    print("Choose a config file to test\n")
    for i in range(len(files)):
        print(f"{i} - {files[i]}")

    file = input()
    cfg = config.get_config(files[int(file)])

    if method == "0":
        for section in cfg.sections():
            print(f"[{section}]")
            for key, value in cfg[section].items():
                print(f"{key} = {value}")


    elif method == "1":

        raw = input(
            "Enter section, key, and new value\n"
            "(separated by spaces; value may contain spaces):\n"
        ).strip()

        parts = raw.split(maxsplit=2)
        if len(parts) < 3:
            print("You must enter section, key, and value.")
            return

        section, key, value = parts

        config.set_config_value(files[int(file)], section, key, value)
        print(f"Edit applied - exit program and see {files[int(file)]} to view change")

    else:
        print("Invalid Input")

    input("Press ENTER to continue")

def test_data_conversion():
    print_new_section("Data Conversion")

    method = int(input("Choose a method to test\n"
          "0 - validate_json()\n"
          "1 - system_to_queue()\n"
          "2 - queue_to_system()\n"))

    project_root = Path(__file__).resolve().parent

    if method == 0:

        # ---- Choose schema (using get_files_in_directory) ----
        print("Choose a schema")
        schemas = get_files_in_directory("./data/schemas")
        for i, name in enumerate(schemas):
            print(f"{i} - {name}")

        schema_choice = int(input())
        schema_name = schemas[schema_choice]
        schema_path = (project_root / "data" / "schemas" / schema_name).resolve()

        # ---- Infer corresponding data directory from schema name ----
        # e.g. "queueing_network.schema.json" -> "queueing-network"
        schema_base = schema_name
        suffix = ".schema.json"
        if schema_base.endswith(suffix):
            schema_base = schema_base[:-len(suffix)]

        dir_name = schema_base.replace("_", "-")  # queueing_network -> queueing-network
        rel_json_dir = f"./data/{dir_name}"

        # ---- Choose JSON (using get_files_in_directory) ----
        print("Choose a json")
        try:
            json_files = get_files_in_directory(rel_json_dir)
        except FileNotFoundError:
            print(f"No data directory found for schema '{schema_name}' at {rel_json_dir}")
            return

        for i, name in enumerate(json_files):
            print(f"{i} - {name}")

        json_choice = int(input())
        json_name = json_files[json_choice]
        json_path = (project_root / rel_json_dir / json_name).resolve()

        # ---- Validate ----
        results = data_conversion.validate_json(str(json_path), str(schema_path))
        for result in results:
            print(result)

        if len(results) == 0:
            print("Valid JSON")

        input("Press ENTER to continue\n")


    elif method == 1:
        system_description = get_files_in_directory("./data/system-description")


        print("Choose a system description")
        for i in range(len(system_description)):
            print(f"{i} - {system_description[i]}")

        choice = int(input())
        system_description_name = system_description[choice]

        system_description_path = (
                project_root / "data" / "system-description" / system_description_name
        ).resolve()

        output = data_conversion.system_to_queue(str(system_description_path))
        print(f"Converted system description {system_description_name} to {output}")

    elif method == 2:
        queueing_networks = get_files_in_directory("./data/queueing-network")

        print("Choose a queueing network")
        for i in range(len(queueing_networks)):
            print(f"{i} - {queueing_networks[i]}")

        choice = int(input())
        queueing_network = queueing_networks[choice]
        queueing_network_path = (
                project_root / "data" / "queueing-network" / queueing_network
        ).resolve()

        output = data_conversion.queue_to_system(str(queueing_network_path))

        print(f"Converted queueing network {queueing_network} to {output}")
    else:
        input("Invalid Input\n"
              "Press ENTER to continue\n")
        return

def test_data_generator():
    print_new_section("Data Generator")
    data_generator.run()
    input("Press ENTER to continue")

def test_user_input():
    print_new_section("System Description (BASE)")
    user_config_settings = user_input.ask_user()
    if user_config_settings is not None:
        config.set_user_config("user_config.ini", user_config_settings)
    return None

def test_ollama_input():
    print_new_section("System Description (OLLAMA)")
    print_new_section("PLEASE RUN BEFORE CONTINUING IF YOU HAVEN'T ALREADY:\n\tollama create nlip-test-model -f model/NLIP.Modelfile")
    user_sys_desc = ollama_input.ask_sys_desc()
    print("System Description JSON Schema created in the 'data/system-description' folder!")
    print('\n')

def test_analyzer():
    print_new_section("Analyzer")

    cfg = config.get_config("dev_config.ini")
    processed_data = get_files_in_directory(cfg.get("paths","processed_data_dir"))
    for i, name in enumerate(processed_data):
        print(f"{i} - {name}")
    processed_data_choice = int(input())
    choice = processed_data[processed_data_choice]

    analyzer.run(choice)

    input("Press ENTER to continue")

def main():
    while True:
        print_new_section("IBM Stress Testing")

        inp = input("Enter a number to test a file:\n"
                    "0: exit program\n"
                    "1: config.py\n"
                    "2: data_conversion.py\n"
                    "3: data_generator.py\n"
                    "4: user_input.py\n"
                    "5: ollama_input.py\n"
                    "6: analyzer.py\n")

        if inp == "1":
            test_config()
        elif inp == "2":
            test_data_conversion()
        elif inp == "3":
            test_data_generator()
        elif inp == "4":
            test_user_input()
        elif inp == "5":
            test_ollama_input()
        elif inp == "6":
            test_analyzer()
        elif inp == "0":
            print_new_section("Exiting Program")
            break

if __name__ == '__main__':
    main()