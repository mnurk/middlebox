import asyncio
from nats.aio.client import Client as NATS
import os
import random
from scapy.all import Ether
import matplotlib.pyplot as plt
import time

delays = []
rtts = []

async def run():
    nc = NATS()

    nats_url = os.getenv("NATS_SURVEYOR_SERVERS", "nats://nats:4222")
    await nc.connect(nats_url)

    async def message_handler(msg):
        subject = msg.subject
        data = msg.data # .decode()
        print(f"Received a message on '{subject}': {data}")
        packet = Ether(data)
        packet.show()

        # Record the time when the packet is received
        receive_time = time.time()

        # Publish the received message to outpktsec and outpktinsec
        delay = random.expovariate(1 / 5e-6)
        delays.append(delay)
        await asyncio.sleep(delay)

        # Record the time when the packet is forwarded
        forward_time = time.time()

        # Calculate RTT
        rtt = forward_time - receive_time
        rtts.append(rtt)
        print(f"RTT: {rtt}")

        if subject == "inpktsec":
            await nc.publish("outpktinsec", msg.data)
        else:
            await nc.publish("outpktsec", msg.data)
   
    # Subscribe to inpktsec and inpktinsec topics
    await nc.subscribe("inpktsec", cb=message_handler)
    await nc.subscribe("inpktinsec", cb=message_handler)

    print("Subscribed to inpktsec and inpktinsec topics")

    try:
        while True:
            await asyncio.sleep(1)
            await asyncio.sleep(60)
            print("Disconnecting...")
            await nc.close()
            plot_results()
    except KeyboardInterrupt:
        print("Disconnecting...")
        await nc.close()
        plot_results()

def plot_results():
    print(f"Delays: {delays}")
    # Calculate mean delay
    mean_delay = sum(delays) / len(delays) if delays else 0
    print(f"Mean delay: {mean_delay}")

    # Calculate average RTT
    average_rtt = sum(rtts) / len(rtts) if rtts else 0
    print(f"Average RTT: {average_rtt}")

    # Plot the mean delay
    plt.figure()
    plt.plot(range(len(delays)), delays, 'bo')
    plt.xlabel('Packet Index')
    plt.ylabel('Delay (s)')
    plt.title('Mean Delay for Packets')
    plt.grid(True)
    plt.savefig('mean_delay.png')  # Save the plot to a file
    print("Mean delay plot saved to mean_delay.png")

    # Plot the average RTT
    plt.figure()
    plt.plot(range(len(rtts)), rtts, 'ro')
    plt.xlabel('Packet Index')
    plt.ylabel('RTT (s)')
    plt.title('Average RTT for Packets')
    plt.grid(True)
    plt.savefig('average_rtt.png')  # Save the plot to a file
    print("Average RTT plot saved to average_rtt.png")

if __name__ == '__main__':
    asyncio.run(run())