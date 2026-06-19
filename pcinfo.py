import platform
import datetime
import os
import subprocess
import sys
from pathlib import Path

def get_cpu_info():
    cpu_info = {
        'Brand': 'N/A',
        'Cores': 'N/A',
        'Threads': 'N/A',
        'Frequency': 'N/A',
        'Type': 'Unknown'
    }
    try:
        system = platform.system()
        if system == 'Windows':
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                    r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                cpu_info['Brand'] = winreg.QueryValueEx(key, "ProcessorNameString")[0]
                winreg.CloseKey(key)
            except:
                pass
            cpu_info['Cores'] = os.environ.get('NUMBER_OF_PROCESSORS', 'N/A')
            cpu_info['Threads'] = cpu_info['Cores']
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                    r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                try:
                    freq = winreg.QueryValueEx(key, "~MHz")[0]
                    cpu_info['Frequency'] = f"{freq} MHz"
                except:
                    pass
                winreg.CloseKey(key)
            except:
                pass
        elif system == 'Linux':
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpu_data = f.read()
                import re
                model_match = re.search(r'model name\s*:\s*(.+)', cpu_data)
                if model_match:
                    cpu_info['Brand'] = model_match.group(1).strip()
                processors = re.findall(r'processor\s*:\s*(\d+)', cpu_data)
                cpu_info['Threads'] = str(len(processors))
                freq_match = re.search(r'cpu MHz\s*:\s*(\d+\.?\d*)', cpu_data)
                if freq_match:
                    cpu_info['Frequency'] = f"{float(freq_match.group(1)):.0f} MHz"
            except:
                pass
        elif system == 'Darwin':
            try:
                result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                      capture_output=True, text=True)
                cpu_info['Brand'] = result.stdout.strip()
                result = subprocess.run(['sysctl', '-n', 'hw.logicalcpu'], 
                                      capture_output=True, text=True)
                cpu_info['Threads'] = result.stdout.strip()
                result = subprocess.run(['sysctl', '-n', 'hw.physicalcpu'], 
                                      capture_output=True, text=True)
                cpu_info['Cores'] = result.stdout.strip()
            except:
                pass
    except Exception as e:
        pass
    brand = cpu_info.get('Brand', '').upper()
    if 'AMD' in brand:
        cpu_info['Type'] = 'AMD'
    elif 'INTEL' in brand:
        cpu_info['Type'] = 'Intel'
    return cpu_info

def get_memory_info():
    mem_info = {
        'Total': 'N/A',
        'Available': 'N/A',
        'Used': 'N/A',
        'Percentage': 'N/A',
        'Type': 'N/A',
        'Speed': 'N/A'
    }
    try:
        system = platform.system()
        if system == 'Windows':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]
                memoryStatus = MEMORYSTATUSEX()
                memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                if kernel32.GlobalMemoryStatusEx(ctypes.byref(memoryStatus)):
                    total = memoryStatus.ullTotalPhys
                    avail = memoryStatus.ullAvailPhys
                    mem_info['Total'] = f"{total / (1024**3):.2f} GB"
                    mem_info['Available'] = f"{avail / (1024**3):.2f} GB"
                    mem_info['Used'] = f"{(total - avail) / (1024**3):.2f} GB"
                    if total > 0:
                        mem_info['Percentage'] = f"{((total - avail) / total * 100):.1f}%"
            except:
                pass
            try:
                import wmi
                c = wmi.WMI()
                for mem in c.Win32_PhysicalMemory():
                    if mem.MemoryType:
                        type_map = {
                            20: 'DDR', 21: 'DDR2', 22: 'DDR2 FB-DIMM',
                            24: 'DDR3', 26: 'DDR4', 27: 'DDR5'
                        }
                        mem_info['Type'] = type_map.get(mem.MemoryType, 'Unknown')
                    if mem.Speed and mem.Speed > 0:
                        mem_info['Speed'] = f"{mem.Speed} MHz"
                        break
            except:
                pass
        elif system == 'Linux':
            try:
                with open('/proc/meminfo', 'r') as f:
                    mem_data = f.read()
                import re
                total_match = re.search(r'MemTotal:\s*(\d+)', mem_data)
                if total_match:
                    total_kb = int(total_match.group(1))
                    mem_info['Total'] = f"{total_kb / (1024**2):.2f} GB"
                avail_match = re.search(r'MemAvailable:\s*(\d+)', mem_data)
                if avail_match:
                    free_kb = int(avail_match.group(1))
                    mem_info['Available'] = f"{free_kb / (1024**2):.2f} GB"
                    if total_match:
                        total_kb = int(total_match.group(1))
                        used_kb = total_kb - free_kb
                        mem_info['Used'] = f"{used_kb / (1024**2):.2f} GB"
                        mem_info['Percentage'] = f"{(used_kb / total_kb * 100):.1f}%"
            except:
                pass
        elif system == 'Darwin':
            try:
                result = subprocess.run(['sysctl', '-n', 'hw.memsize'], 
                                      capture_output=True, text=True)
                total = int(result.stdout.strip())
                mem_info['Total'] = f"{total / (1024**3):.2f} GB"
            except:
                pass
    except Exception as e:
        pass
    return mem_info

def get_disk_info():
    disks = []
    try:
        system = platform.system()
        if system == 'Windows':
            try:
                import ctypes
                drives = []
                for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                    drive = f"{letter}:\\"
                    if os.path.exists(drive):
                        drives.append(drive)
                for drive in drives:
                    try:
                        free_bytes = ctypes.c_ulonglong(0)
                        total_bytes = ctypes.c_ulonglong(0)
                        total_free_bytes = ctypes.c_ulonglong(0)
                        if ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                            drive, ctypes.byref(free_bytes), 
                            ctypes.byref(total_bytes), ctypes.byref(total_free_bytes)
                        ):
                            total = total_bytes.value
                            free = free_bytes.value
                            disk_type = 'Unknown'
                            drive_letter = drive[0]
                            try:
                                result = subprocess.run(
                                    ['wmic', 'diskdrive', 'get', 'Model,InterfaceType'],
                                    capture_output=True, text=True, encoding='cp866', errors='ignore'
                                )
                                if result.stdout:
                                    for line in result.stdout.split('\n'):
                                        if 'SSD' in line or 'Solid State' in line:
                                            disk_type = 'SSD'
                                        elif 'NVMe' in line:
                                            disk_type = 'NVMe SSD'
                                        elif 'HDD' in line or 'Hard Disk' in line:
                                            disk_type = 'HDD'
                            except:
                                pass
                            disk = {
                                'Device': drive,
                                'Mount': drive,
                                'File System': 'N/A',
                                'Total': f"{total / (1024**3):.2f} GB" if total > 0 else 'N/A',
                                'Used': f"{(total - free) / (1024**3):.2f} GB" if total > 0 else 'N/A',
                                'Free': f"{free / (1024**3):.2f} GB" if free > 0 else 'N/A',
                                'Percentage': f"{((total - free) / total * 100):.1f}%" if total > 0 else 'N/A',
                                'Type': disk_type,
                                'Model': 'N/A'
                            }
                            disks.append(disk)
                    except:
                        continue
            except:
                pass
            if not disks:
                try:
                    result = subprocess.run(['systeminfo'], capture_output=True, text=True, encoding='cp866')
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'Available Physical Memory' in line or 'Total Physical Memory' in line:
                            pass
                except:
                    pass
        elif system == 'Linux':
            try:
                result = subprocess.run(['df', '-h', '--exclude-type=tmpfs', '--exclude-type=devtmpfs'], 
                                      capture_output=True, text=True)
                lines = result.stdout.strip().split('\n')[1:]
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 6:
                            disk_type = 'Unknown'
                            if 'nvme' in parts[0]:
                                disk_type = 'NVMe SSD'
                            elif 'sd' in parts[0]:
                                try:
                                    disk_name = parts[0].replace('/dev/', '')
                                    with open(f'/sys/block/{disk_name}/queue/rotational', 'r') as f:
                                        if f.read().strip() == '0':
                                            disk_type = 'SSD'
                                        else:
                                            disk_type = 'HDD'
                                except:
                                    pass
                            disk = {
                                'Device': parts[0],
                                'Mount': parts[5],
                                'File System': 'N/A',
                                'Total': parts[1],
                                'Used': parts[2],
                                'Free': parts[3],
                                'Percentage': parts[4],
                                'Type': disk_type,
                                'Model': 'N/A'
                            }
                            disks.append(disk)
            except:
                pass
        elif system == 'Darwin':
            try:
                result = subprocess.run(['df', '-h'], capture_output=True, text=True)
                lines = result.stdout.strip().split('\n')[1:]
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 9:
                            disk = {
                                'Device': parts[0],
                                'Mount': parts[8],
                                'File System': 'N/A',
                                'Total': parts[1],
                                'Used': parts[2],
                                'Free': parts[3],
                                'Percentage': parts[4],
                                'Type': 'Unknown',
                                'Model': 'N/A'
                            }
                            disks.append(disk)
            except:
                pass
    except Exception as e:
        pass
    return disks

def get_gpu_info():
    gpus = []
    try:
        system = platform.system()
        if system == 'Windows':
            try:
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                        r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}")
                    for i in range(100):
                        try:
                            subkey = winreg.EnumKey(key, i)
                            if subkey.startswith('0'):
                                subkey_path = f"SYSTEM\\CurrentControlSet\\Control\\Class\\{{4d36e968-e325-11ce-bfc1-08002be10318}}\\{subkey}"
                                subkey_full = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path)
                                try:
                                    name = winreg.QueryValueEx(subkey_full, "DriverDesc")[0]
                                    if name and 'Microsoft' not in name and 'Remote' not in name:
                                        gpu = {
                                            'Name': name,
                                            'Driver': 'N/A',
                                            'Memory Total': 'N/A',
                                            'Memory Used': 'N/A',
                                            'Memory Free': 'N/A',
                                            'GPU Load': 'N/A',
                                            'Temperature': 'N/A',
                                            'Memory Type': 'N/A'
                                        }
                                        gpus.append(gpu)
                                except:
                                    pass
                                winreg.CloseKey(subkey_full)
                        except:
                            break
                    winreg.CloseKey(key)
                except:
                    pass
            except:
                pass
        elif system == 'Linux':
            try:
                result = subprocess.run(['lspci', '|', 'grep', '-E', 'VGA|3D|Display'], 
                                      capture_output=True, text=True, shell=True)
                for line in result.stdout.split('\n'):
                    if line.strip():
                        gpu = {
                            'Name': line.strip(),
                            'Driver': 'N/A',
                            'Memory Total': 'N/A',
                            'Memory Used': 'N/A',
                            'Memory Free': 'N/A',
                            'GPU Load': 'N/A',
                            'Temperature': 'N/A',
                            'Memory Type': 'N/A'
                        }
                        gpus.append(gpu)
            except:
                pass
        elif system == 'Darwin':
            try:
                result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], 
                                      capture_output=True, text=True)
                gpu = {}
                for line in result.stdout.split('\n'):
                    if 'Chipset Model' in line:
                        gpu['Name'] = line.split(':')[1].strip()
                    elif 'VRAM' in line:
                        gpu['Memory Total'] = line.split(':')[1].strip()
                if gpu:
                    gpu.setdefault('Driver', 'N/A')
                    gpu.setdefault('Memory Total', 'N/A')
                    gpu.setdefault('Memory Used', 'N/A')
                    gpu.setdefault('Memory Free', 'N/A')
                    gpu.setdefault('GPU Load', 'N/A')
                    gpu.setdefault('Temperature', 'N/A')
                    gpu.setdefault('Memory Type', 'N/A')
                    gpus.append(gpu)
            except:
                pass
    except Exception as e:
        pass
    if not gpus:
        gpus.append({'Info': 'GPU information not available'})
    return gpus

def get_system_info():
    info = {
        'system': {
            'OS': f"{platform.system()} {platform.release()}",
            'Version': platform.version(),
            'Architecture': platform.machine(),
            'Hostname': platform.node(),
            'Processor': platform.processor()
        },
        'cpu': get_cpu_info(),
        'memory': get_memory_info(),
        'disks': get_disk_info(),
        'gpus': get_gpu_info()
    }
    return info

def format_info(info):
    lines = []
    lines.append(f"Дата и время: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    lines.append(f"Компьютер: {platform.node()}")
    lines.append("")
    lines.append("СИСТЕМА")
    for key, value in info['system'].items():
        lines.append(f"{key:15}: {value}")
    lines.append("")
    lines.append("ПРОЦЕССОР")
    for key, value in info['cpu'].items():
        lines.append(f"{key:15}: {value}")
    lines.append("")
    lines.append("ОПЕРАТИВНАЯ ПАМЯТЬ")
    for key, value in info['memory'].items():
        lines.append(f"{key:15}: {value}")
    lines.append("")
    lines.append("ДИСКИ")
    if info['disks']:
        for i, disk in enumerate(info['disks'], 1):
            lines.append(f"Диск #{i}:")
            for key, value in disk.items():
                lines.append(f"{key:13}: {value}")
            lines.append("")
    else:
        lines.append("Информация о дисках недоступна")
        lines.append("")
    lines.append("ВИДЕОКАРТЫ")
    if info['gpus']:
        for i, gpu in enumerate(info['gpus'], 1):
            if 'Info' in gpu:
                lines.append(f"{gpu['Info']}")
            else:
                lines.append(f"GPU #{i}:")
                for key, value in gpu.items():
                    lines.append(f"{key:15}: {value}")
            lines.append("")
    else:
        lines.append("Информация о видеокартах недоступна")
        lines.append("")
    return "\n".join(lines)

def sanitize_filename(filename):
    for char in '<>:"/\\|?*':
        filename = filename.replace(char, '_')
    filename = filename.strip()
    return filename if filename else "PC"

def save_to_file(info):
    safe_name = sanitize_filename(platform.node())
    filename = f"{safe_name}_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = Path(filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(format_info(info))
    return filepath

def main():
    info = get_system_info()
    filename = save_to_file(info)

if __name__ == "__main__":
    main()