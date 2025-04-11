import json
import matplotlib.pyplot as plt
import os

def plot_results():
    output_dir = "plots"
    os.makedirs(output_dir, exist_ok=True)

    with open("results.json", "r") as f:
        results = json.load(f)
        delays = results["delays"]
        rtts = results["rtts"]

    mean_delay = sum(delays) / len(delays) if delays else 0
    print(f"Mean delay: {mean_delay}")

    average_rtt = sum(rtts) / len(rtts) if rtts else 0
    print(f"Average RTT: {average_rtt}")

    plt.figure()
    plt.plot(range(len(delays)), delays, 'bo')
    plt.xlabel('Packet Index')
    plt.ylabel('Delay (s)')
    plt.title('Mean Delay for Packets')
    plt.grid(True)
    mean_delay_path = os.path.join(output_dir, 'mean_delay.png')
    plt.savefig(mean_delay_path)
    print(f"Mean delay plot saved to {mean_delay_path}")

    plt.figure()
    plt.plot(range(len(rtts)), rtts, 'ro')
    plt.xlabel('Packet Index')
    plt.ylabel('RTT (s)')
    plt.title('Average RTT for Packets')
    plt.grid(True)
    average_rtt_path = os.path.join(output_dir, 'average_rtt.png')
    plt.savefig(average_rtt_path)
    print(f"Average RTT plot saved to {average_rtt_path}")

if __name__ == "__main__":
    plot_results()
