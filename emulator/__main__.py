import argparse
from virtual_machine import VirtualMachine
from monitor import VirtualMachineMonitor

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    args = parser.parse_args()

    with open(args.input, "rb") as f:
        data = f.read()

    vm = VirtualMachine(list(data))
    monitor = VirtualMachineMonitor(vm)
    monitor.run()
