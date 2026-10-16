"""Performance benchmarking for BharatPII package."""

import os
import platform
import time
import psutil
import torch
from bharatpii import BharatPII

def benchmark():
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / (1024 * 1024)

    t0 = time.perf_counter()
    model = BharatPII.from_pretrained("models/bharatpii-crf-v1.0")
    t1 = time.perf_counter()
    load_time = t1 - t0

    mem_after_load = process.memory_info().rss / (1024 * 1024)

    # Warmup
    model.predict("Warmup text with Rahul and PAN ABCDE1234F.")

    # Single text latency
    single_texts = [
        "Call Rahul Sharma at 9876543210 regarding PAN ABCDE1234F.",
        "Aadhaar 1234 5678 9012 registered to Priya in Bengaluru 560001.",
        "मेरा नाम राहुल शर्मा है और ईमेल rahul@example.com है।",
        "Payment received from amit@oksbi for transaction 892019482.",
        "Flat 101, Green Valley Residency, Lake View Road, Kolkata 700019.",
    ]

    latencies = []
    for _ in range(5):
        for text in single_texts:
            t_start = time.perf_counter()
            _ = model.predict(text)
            t_end = time.perf_counter()
            latencies.append((t_end - t_start) * 1000)

    avg_single_latency = sum(latencies) / len(latencies)
    min_single_latency = min(latencies)
    max_single_latency = max(latencies)

    # Batch throughput (batch size 10)
    batch_10 = single_texts * 2
    t_b0 = time.perf_counter()
    _ = model.predict_batch(batch_10)
    t_b1 = time.perf_counter()
    batch_time = t_b1 - t_b0
    throughput = len(batch_10) / batch_time

    mem_peak = process.memory_info().rss / (1024 * 1024)

    print("--- BHARATPII PERFORMANCE BENCHMARK ---")
    print(f"Platform:              {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"CPU:                   {platform.processor() or 'AMD64 Family'}")
    print(f"Python:                {platform.python_version()}")
    print(f"PyTorch:               {torch.__version__}")
    print(f"Device:                {model.device}")
    print(f"Model Load Time:       {load_time:.3f} s")
    print(f"Memory (Pre-load):     {mem_before:.1f} MB")
    print(f"Memory (Post-load):    {mem_after_load:.1f} MB (Delta: +{mem_after_load - mem_before:.1f} MB)")
    print(f"Memory (Peak):         {mem_peak:.1f} MB")
    print(f"Avg Single Latency:    {avg_single_latency:.2f} ms")
    print(f"Min Single Latency:    {min_single_latency:.2f} ms")
    print(f"Max Single Latency:    {max_single_latency:.2f} ms")
    print(f"Batch Throughput:      {throughput:.2f} texts/second (Batch size 10, total {batch_time:.3f} s)")

if __name__ == "__main__":
    benchmark()
