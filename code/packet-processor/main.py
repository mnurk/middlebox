import asyncio
from nats.aio.client import Client as NATS
import os
import random
from scapy.all import Ether
import time
import json

delays = []
rtts = []

async def run():
    nc = NATS()

    nats_url = os.getenv("NATS_SURVEYOR_SERVERS", "nats://nats:4222")
    try:
        await nc.connect(nats_url)
    except Exception as e:
        print(f"Failed to connect to NATS: {e}")
        return

    async def message_handler(msg):
        subject = msg.subject
        data = msg.data
        print(f"Received a message on '{subject}': {data}")
        packet = Ether(data)
        packet.show()

        receive_time = time.time()

        mean_delay = float(os.getenv("MEAN_DELAY", 5e-6))
        delay = random.expovariate(1 / mean_delay)
        delays.append(delay)
        await asyncio.sleep(delay)

        forward_time = time.time()

        rtt = forward_time - receive_time
        rtts.append(rtt)
        print(f"RTT: {rtt}")

        if subject == "inpktsec":
            await nc.publish("outpktinsec", msg.data)
        else:
            await nc.publish("outpktsec", msg.data)
   
    await nc.subscribe("inpktsec", cb=message_handler)
    await nc.subscribe("inpktinsec", cb=message_handler)

    print("Subscribed to inpktsec and inpktinsec topics")

    try:
        while True:
            await asyncio.sleep(1)
            save_results()
    except KeyboardInterrupt:
        print("Disconnecting...")
        await nc.close()
        save_results()

def save_results():
    results = {"delays": delays, "rtts": rtts}
    with open("results.json", "w") as f:
        json.dump(results, f)
    print("Results saved to results.json")

if __name__ == '__main__':
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Program interrupted by user.")
