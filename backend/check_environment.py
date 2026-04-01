import torch
import os, multiprocessing
    
# 方法1：基础查看
print(f"CUDA是否可用: {torch.cuda.is_available()}")
print(f"当前设备: {'cuda:0' if torch.cuda.is_available() else 'cpu'}")
print(f"可用GPU数量: {torch.cuda.device_count()}")
print(f"当前设备索引: {torch.cuda.current_device()}")
print(f"设备名称: {torch.cuda.get_device_name()}")
print(f"逻辑核心数 (os): {os.cpu_count()}")
print(f"逻辑核心数 (multiprocessing): {multiprocessing.cpu_count()}")


# 方法2：详细查看所有设备
def print_gpu_info():
    if torch.cuda.is_available():
        print(f"总GPU数量: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"\nGPU {i}: {torch.cuda.get_device_name(i)}")
            prop = torch.cuda.get_device_properties(i)
            print(f"  计算能力: {prop.major}.{prop.minor}")
            print(f"  总显存: {prop.total_memory / 1024**3:.2f} GB")
            print(f"  已用显存: {torch.cuda.memory_allocated(i) / 1024**3:.2f} GB")
            print(f"  缓存显存: {torch.cuda.memory_reserved(i) / 1024**3:.2f} GB")
            print(f"  多处理器数量: {prop.multi_processor_count}")
    else:
        print("没有可用的CUDA设备")

print_gpu_info()