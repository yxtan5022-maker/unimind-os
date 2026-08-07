// UniMind - C++17 Topology-Aware Hardware Detection (paper, Sec. 4.1)
// License: MIT
// Detects CPU core count, total RAM, OS type, and CPU architecture using
// platform-specific APIs and serializes the result as JSON on stdout.

#include <iostream>
#include <string>
#include <thread>

#if defined(_WIN32)
#include <windows.h>
#elif defined(__APPLE__)
#include <sys/sysctl.h>
#include <unistd.h>
#elif defined(__linux__)
#include <unistd.h>
#include <fstream>
#endif

static int detect_logical_cores() {
#if defined(_WIN32)
    SYSTEM_INFO sysinfo;
    GetSystemInfo(&sysinfo);
    return static_cast<int>(sysinfo.dwNumberOfProcessors);
#elif defined(__APPLE__)
    int count = 0;
    size_t size = sizeof(count);
    sysctlbyname("hw.logicalcpu", &count, &size, nullptr, 0);
    return count > 0 ? count : 1;
#elif defined(__linux__)
    long n = sysconf(_SC_NPROCESSORS_ONLN);
    return n > 0 ? static_cast<int>(n) : 1;
#else
    return static_cast<int>(std::thread::hardware_concurrency());
#endif
}

static int detect_physical_cores() {
#if defined(_WIN32)
    SYSTEM_INFO sysinfo;
    GetSystemInfo(&sysinfo);
    DWORD mask = sysinfo.dwActiveProcessorMask;
    int count = 0;
    while (mask) {
        if (mask & 1) count++;
        mask >>= 1;
    }
    return count > 0 ? count : detect_logical_cores();
#elif defined(__APPLE__)
    int count = 0;
    size_t size = sizeof(count);
    sysctlbyname("hw.physicalcpu", &count, &size, nullptr, 0);
    return count > 0 ? count : detect_logical_cores();
#elif defined(__linux__)
    std::ifstream info("/proc/cpuinfo");
    std::string line;
    int count = 0;
    while (std::getline(info, line)) {
        if (line.rfind("cpu cores", 0) == 0) {
            std::string::size_type pos = line.find(':');
            if (pos != std::string::npos) {
                count = std::stoi(line.substr(pos + 1));
            }
        }
    }
    return count > 0 ? count : detect_logical_cores();
#else
    return detect_logical_cores();
#endif
}

static std::string detect_os_name() {
#if defined(_WIN32)
    return "Windows";
#elif defined(__APPLE__)
    return "macOS";
#elif defined(__linux__)
    return "Linux";
#else
    return "Unknown";
#endif
}

static std::string detect_architecture() {
#if defined(_WIN32)
    SYSTEM_INFO sysinfo;
    GetNativeSystemInfo(&sysinfo);
    switch (sysinfo.wProcessorArchitecture) {
        case PROCESSOR_ARCHITECTURE_AMD64: return "x86_64";
        case PROCESSOR_ARCHITECTURE_ARM64: return "arm64";
        case PROCESSOR_ARCHITECTURE_INTEL: return "x86";
        default: return "unknown";
    }
#elif defined(__x86_64__) || defined(_M_X64)
    return "x86_64";
#elif defined(__aarch64__)
    return "arm64";
#elif defined(__i386__)
    return "x86";
#else
    return "unknown";
#endif
}

static double detect_total_memory_gb() {
#if defined(_WIN32)
    MEMORYSTATUSEX mem;
    mem.dwLength = sizeof(mem);
    if (GlobalMemoryStatusEx(&mem)) {
        return static_cast<double>(mem.ullTotalPhys) / (1024.0 * 1024.0 * 1024.0);
    }
#elif defined(__linux__)
    std::ifstream meminfo("/proc/meminfo");
    std::string line;
    while (std::getline(meminfo, line)) {
        if (line.rfind("MemTotal:", 0) == 0) {
            long kb = std::stol(line.substr(10));
            return static_cast<double>(kb) / (1024.0 * 1024.0);
        }
    }
#endif
    return 0.0;
}

static std::string json_escape(const std::string& s) {
    std::string out;
    for (char c : s) {
        switch (c) {
            case '"': out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            default: out += c;
        }
    }
    return out;
}

int main() {
    std::cout << "{\n";
    std::cout << "  \"logical_cores\": " << detect_logical_cores() << ",\n";
    std::cout << "  \"physical_cores\": " << detect_physical_cores() << ",\n";
    std::cout << "  \"os\": \"" << json_escape(detect_os_name()) << "\",\n";
    std::cout << "  \"arch\": \"" << json_escape(detect_architecture()) << "\",\n";
    std::cout << "  \"total_memory_gb\": " << detect_total_memory_gb() << "\n";
    std::cout << "}\n";
    return 0;
}
