import json
import matplotlib.pyplot as plt

# Load results.json
with open("results.json", "r") as f:
    results = json.load(f)

# Retrieve data from the results dictionary
rtts = results.get("rtts", [])
delays = results.get("delays", [])
rtt_avg = results.get("rtt_avg", 0)
rtt_ci_95 = results.get("rtt_ci_95", 0)
delay_avg = results.get("delay_avg", 0)
delay_ci_95 = results.get("delay_ci_95", 0)
covert_capacity = results.get("covert_channel_capacity_bps", 0)

# Convert units for plotting:
# RTT in milliseconds, Delay in microseconds
rtts_ms = [r * 1000 for r in rtts]
delays_us = [d * 1e6 for d in delays]

# Plot 1: RTT vs. Packet Index
plt.figure(figsize=(10, 4))
plt.plot(rtts_ms, marker='o', linestyle='-', color='blue', markersize=2)
plt.title("RTT per Packet")
plt.xlabel("Packet Index")
plt.ylabel("RTT (ms)")
plt.grid(True)
plt.tight_layout()
plt.savefig("rtt_vs_index.png")
plt.close()

# Plot 2: Random Delay vs. Packet Index
plt.figure(figsize=(10, 4))
plt.plot(delays_us, marker='o', linestyle='-', color='green', markersize=2)
plt.title("Random Delay per Packet")
plt.xlabel("Packet Index")
plt.ylabel("Delay (µs)")
plt.grid(True)
plt.tight_layout()
plt.savefig("delay_vs_index.png")
plt.close()

# Plot 3: Histogram of RTT
plt.figure(figsize=(10, 4))
plt.hist(rtts_ms, bins=30, color='blue', alpha=0.7)
plt.title("Histogram of RTT")
plt.xlabel("RTT (ms)")
plt.ylabel("Frequency")
plt.grid(True)
plt.tight_layout()
plt.savefig("rtt_histogram.png")
plt.close()

# Plot 4: Histogram of Random Delays
plt.figure(figsize=(10, 4))
plt.hist(delays_us, bins=30, color='green', alpha=0.7)
plt.title("Histogram of Random Delays")
plt.xlabel("Delay (µs)")
plt.ylabel("Frequency")
plt.grid(True)
plt.tight_layout()
plt.savefig("delay_histogram.png")
plt.close()

# Print summary statistics
print("Summary Statistics:")
print(f"RTT Average: {rtt_avg * 1000:.3f} ms")
print(f"RTT 95% Confidence Interval: {rtt_ci_95 * 1000:.3f} ms")
print(f"Delay Average: {delay_avg * 1e6:.3f} µs")
print(f"Delay 95% Confidence Interval: {delay_ci_95 * 1e6:.3f} µs")
print(f"Covert Channel Capacity: {covert_capacity:.3f} bps")
