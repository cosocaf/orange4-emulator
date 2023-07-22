import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()

    buffer = [0] * 0x100

    with open(args.input, "r") as f:
        for line in f.readlines():
            [addr, data] = line.split(":")
            addr = int(addr[1:], 16)
            for byte in data.rstrip():
                buffer[addr] = int(byte, 16)
                addr += 1

    memory = [0] * 0x80
    for i, byte in enumerate(buffer):
        if i % 2 == 0:
            memory[i // 2] |= byte << 4
        else:
            memory[i // 2] |= byte

    with open(args.output, "wb") as f:
        f.write(bytes(memory))
