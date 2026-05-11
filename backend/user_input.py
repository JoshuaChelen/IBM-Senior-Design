from pydantic import BaseModel, Field, DirectoryPath, field_validator, ConfigDict, ValidationError
from typing import Annotated
from pathlib import Path
import os

class UserInput(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    # paths
    test_system_path: Annotated[DirectoryPath, Field(str_min_length=1)]
    prod_system_path: Annotated[DirectoryPath, Field(str_min_length=1)]
    test_results_path: Annotated[(DirectoryPath), Field(str_min_length=1)]
    temp_dir: Annotated[DirectoryPath, Field(str_min_length=1, default="./tmp")]


    # constraints
    max_delay_seconds: Annotated[float, Field(gt=0)]
    max_queue_utilization: Annotated[float, Field(gt=0, le=1)]
    avg_message_size_bytes: Annotated[int, Field(gt=0)]


    # test_system
    test_cpu_rate_ghz: Annotated[float, Field(gt=0)]
    test_storage_size_gb: Annotated[int, Field(gt=0)]
    test_ram_size_gb: Annotated[int, Field(gt=0)]
    test_network_bandwidth_mbps: Annotated[int, Field(gt=0)]


    # prod_system
    prod_cpu_rate_ghz: Annotated[float, Field(gt=0)]
    prod_storage_size_gb: Annotated[int, Field(gt=0)]
    prod_ram_size_gb: Annotated[int, Field(gt=0)]
    prod_network_bandwidth_mbps: Annotated[int, Field(gt=0)]

     
    @field_validator("test_system_path", "prod_system_path", "test_results_path", "temp_dir", mode="before")
    def create_dirs(cls, v):
        if v is None or v == "":
            return v
            
        path_str = str(v) if isinstance(v, (Path,)) else v
        os.makedirs(path_str, exist_ok=True)
        return v

    @classmethod
    def from_user(cls) -> "UserInput":
        """
        Interactive menu that forces required fields to be set before continuing.
        """

        # Start with a "blank" partially-filled object
        # We bypass validation for this placeholder, then validate later.
        defaults = cls.model_construct(
            test_system_path=None, prod_results_path=None, test_results_path=None, temp_dir='./tmp',
            max_delay_seconds=0.5, max_queue_utilization=0.8, avg_message_size_bytes=512,
            test_cpu_rate_ghz=2.5, test_storage_size_gb=256, test_ram_size_gb=16, test_network_bandwidth_mbps=100,
            prod_cpu_rate_ghz=3.5, prod_storage_size_gb=1024, prod_ram_size_gb=64, prod_network_bandwidth_mbps=1000
        )

        while True:
            print("\n1) Paths: ")
            print("2) Constraints: ")
            print("3) Test System: ")
            print("4) Production System: ")
            print("5) Done")
            print("6) Quit without saving\n")

            choice = input("Choose an option (1-6): \n").strip()

            if choice == "1":
                test_sys = input("\nEnter Test System Path: ").strip()
                prod_sys = input("Enter Production System Path: ").strip()
                test_res = input("Enter Test Results Path: ").strip()
                temp_dir = input("Enter Temporary Directory Path: ").strip()
                try:
                    if test_sys:
                        defaults.test_system_path = test_sys
                    if prod_sys:
                        defaults.prod_system_path = prod_sys
                    if test_res:
                        defaults.test_results_path = test_res
                    if temp_dir:
                        defaults.temp_dir = temp_dir
                except Exception as e:
                    print(f"Error: {e}")

            elif choice == "2":
                max_delay = input("\nEnter Maximum Allowed Delay (in seconds): ").strip()
                max_queue = input("Enter Maximum Allowed Queue Utilization (0-1): ").strip()
                avg_msg = input("Enter Average Message Size (in bytes): ").strip()
                try:
                    if max_delay:
                        defaults.max_delay_seconds = max_delay
                    if max_queue:
                        defaults.max_queue_utilization = max_queue
                    if avg_msg:
                        defaults.avg_message_size_bytes = avg_msg
                except Exception as e:
                    print(f"Error: {e}")

            elif choice == "3":
                cpu_rate = input("\nEnter CPU Rate (in GHz): ").strip()
                storage_size = input("Enter Storage Size (in GB): ").strip()
                ram_size = input("Enter RAM Size (in GB): ").strip()
                net_band = input("Enter Network Bandwidth (in Mbps): ").strip()
                try:
                    if cpu_rate:
                        defaults.test_cpu_rate_ghz = cpu_rate
                    if storage_size:
                        defaults.test_storage_size_gb = storage_size
                    if ram_size:
                        defaults.test_ram_size_gb = ram_size
                    if net_band:
                        defaults.test_network_bandwidtch_mbps = net_band
                except Exception as e:
                    print(f"Error: {e}")
            
            elif choice == "4":
                cpu_rate = input("\nEnter CPU Rate (in GHz): ").strip()
                storage_size = input("Enter Storage Size (in GB): ").strip()
                ram_size = input("Enter RAM Size (in GB): ").strip()
                net_band = input("Enter Network Bandwidth (in Mbps): ").strip()
                try:
                    if cpu_rate:
                        defaults.test_cpu_rate_ghz = cpu_rate
                    if storage_size:
                        defaults.test_storage_size_gb = storage_size
                    if ram_size:
                        defaults.test_ram_size_gb = ram_size
                    if net_band:
                        defaults.test_network_bandwidth_mbps = net_band
                except Exception as e:
                    print(f"Error: {e}")

            elif choice == "5":
                # Try validating required fields NOW
                try:
                    data = defaults.model_dump(exclude_none=True)
                    final_sys = cls.model_validate(data)
                    print("\nConfiguration complete.")
                    print(final_sys)
                    return final_sys
                except ValidationError as e:
                    print("\n❌ Cannot continue — missing required fields:\n")

                    for error in e.errors():
                        field = ".".join(str(x) for x in error["loc"])
                        message = error["msg"]
                        print(f" - {field}: {message}")

                    print("\nPlease fill in all required fields before selecting 'Done'.")
                    continue

            elif choice == "6":
                print("\nAborted by user")
                break

            else:
                print("Invalid choice.")

def ask_user() -> UserInput:
    user_input = UserInput.from_user()
    print("\n")
    if user_input is not None: return user_input
    return None
