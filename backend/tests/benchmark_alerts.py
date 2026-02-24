import asyncio
import time
import uuid

# This script demonstrates the performance difference between N+1 individual saves
# and a single batch save, simulating database latency.

async def simulate_db_save_individual(count, latency_sec=0.01):
    start = time.perf_counter()
    for i in range(count):
        # Simulate an asynchronous database call with latency
        await asyncio.sleep(latency_sec)
    end = time.perf_counter()
    return end - start

async def simulate_db_save_batch(count, latency_sec=0.01):
    start = time.perf_counter()
    # Simulate a single asynchronous database call for the entire batch
    await asyncio.sleep(latency_sec)
    end = time.perf_counter()
    return end - start

async def main():
    count = 20
    latency = 0.05  # 50ms latency per roundtrip

    print(f"Simulating saving {count} items with {latency*1000:.0f}ms latency per roundtrip...")

    time_indiv = await simulate_db_save_individual(count, latency)
    print(f"N+1 (Individual saves): {time_indiv:.4f}s")

    time_batch = await simulate_db_save_batch(count, latency)
    print(f"Batch save: {time_batch:.4f}s")

    improvement = (time_indiv - time_batch) / time_indiv * 100
    print(f"Performance Improvement: {improvement:.2f}%")
    print(f"Speedup: {time_indiv / time_batch:.2f}x")

if __name__ == "__main__":
    asyncio.run(main())
