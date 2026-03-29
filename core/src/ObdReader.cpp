#include "ObdReader.hpp"
#include <iostream>
#include <array>
#include <fcntl.h>    // O_RDWR, O_NOCTTY
#include <termios.h>  // POSIX serial configuration
#include <unistd.h>   // read, write, close, usleep
#include <cstring>
#include <sstream>
#include <algorithm>  // std::remove, std::all_of
#include <cctype>     // ::isxdigit

ObdReader::ObdReader(const std::string& device_path)
    : m_device_path(device_path), m_serial_fd(-1) {}

ObdReader::~ObdReader() {
    if (m_serial_fd >= 0) {
        close(m_serial_fd);
        std::cout << "OBD port closed (" << m_device_path << ")\n";
    }
}

bool ObdReader::connect() {
    m_serial_fd = open(m_device_path.c_str(), O_RDWR | O_NOCTTY | O_SYNC);

    if (m_serial_fd < 0){
        std::cerr << "Error: cannot open serial port " << m_device_path << " (try sudo)\n";
        return false;
    }

    struct termios tty;

    if (tcgetattr(m_serial_fd, &tty) != 0) {
        std::cerr << "Error: tcgetattr failed\n";
        close(m_serial_fd);
        m_serial_fd = -1;
        return false;
    }

    cfsetospeed(&tty, B38400);
    cfsetispeed(&tty, B38400);

    tty.c_cflag = (tty.c_cflag & ~CSIZE) | CS8; // 8 data bits
    tty.c_cflag |= (CLOCAL | CREAD);            // Enable receiver
    tty.c_cflag &= ~(PARENB | PARODD);          // No parity
    tty.c_cflag &= ~CSTOPB;                     // 1 stop bit
    tty.c_cflag &= ~CRTSCTS;                    // No hardware flow control

    // Disable line processing in the OS (raw mode)
    tty.c_iflag &= ~(IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL | IXON);
    tty.c_lflag &= ~(ECHO | ECHONL | ICANON | ISIG | IEXTEN);
    tty.c_oflag &= ~OPOST;

    // Wait up to 0.5s for serial data, then return from read().
    tty.c_cc[VMIN]  = 0;
    tty.c_cc[VTIME] = 5;

    if (tcsetattr(m_serial_fd, TCSANOW, &tty) != 0) {
        std::cerr << "Error: tcsetattr failed\n";
        close(m_serial_fd);
        m_serial_fd = -1;
        return false;
    }

    return true;
}

bool ObdReader::initialize() {
    std::cout << "Restarting ELM327 adapter...\n";

    const std::string reset_response = send_command("ATZ");
    if (reset_response.empty()) {
        std::cerr << "Error: no response to ATZ command\n";
        return false;
    }

    usleep(2000000);

    auto run_at_and_expect_ok = [this](const std::string& cmd) -> bool {
        std::string response = send_command(cmd);
        if (response.empty()) {
            std::cerr << "Error: no response to " << cmd << " command\n";
            return false;
        }

        std::transform(response.begin(), response.end(), response.begin(), [](unsigned char c) {
            return static_cast<char>(std::toupper(c));
        });

        if (response.find("OK") == std::string::npos) {
            std::cerr << "Error: unexpected response for " << cmd << ": " << response << "\n";
            return false;
        }
        return true;
    };

    if (!run_at_and_expect_ok("ATE0")) {
        return false;
    }
    if (!run_at_and_expect_ok("ATL0")) {
        return false;
    }
    if (!run_at_and_expect_ok("ATSP5")) {
        return false;
    }

    return true;
}

std::string ObdReader::send_command(const std::string& cmd) {
    if (m_serial_fd < 0) return "";

    const std::string full_cmd = cmd + "\r";

    // Drop stale bytes before sending a new request.
    tcflush(m_serial_fd, TCIFLUSH);

    size_t total_written = 0;
    while (total_written < full_cmd.size()) {
        const ssize_t written = write(
            m_serial_fd,
            full_cmd.c_str() + total_written,
            full_cmd.size() - total_written
        );
        if (written <= 0) {
            std::cerr << "Error: failed to write to serial port\n";
            return "";
        }
        total_written += static_cast<size_t>(written);
    }

    std::string response;
    response.reserve(256);
    std::array<char, 64> buf{};

    while (response.length() < 256) {
        const ssize_t bytes_read = read(m_serial_fd, buf.data(), buf.size());
        if (bytes_read <= 0) {
            break;
        }

        for (ssize_t i = 0; i < bytes_read && response.length() < 256; ++i) {
            const char c = buf[static_cast<size_t>(i)];
            if (c == '>') {
                return response;
            }
            if (c != '\r' && c != '\n') {
                response += c;
            }
        }
    }

    return response;
}

std::string ObdReader::extract_payload(const std::string& response, const std::string& expected_header) {
    std::string clean = response;
    clean.erase(std::remove(clean.begin(), clean.end(), ' '), clean.end());

    size_t pos = clean.find(expected_header);
    if (pos == std::string::npos) return "";

    return clean.substr(pos + expected_header.length());
}

int ObdReader::hex_to_int(const std::string& hex_str){
    if (hex_str.empty() || !std::all_of(hex_str.begin(), hex_str.end(), [](unsigned char c) {
        return std::isxdigit(c) != 0;
    })) {
        return -1;
    }
    
    int value;
    std::stringstream ss;
    ss << std::hex << hex_str;
    ss >> value;
    return value;
}

std::optional<float> ObdReader::get_rpm() {
    std::string resp = send_command("010C");
    std::string payload = extract_payload(resp, "410C");

    if (payload.length() >= 4) {
        int a = hex_to_int(payload.substr(0, 2));
        int b = hex_to_int(payload.substr(2, 2));

        if (a != -1 && b != -1) {
            return ((a * 256.0f) + b) / 4.0f;
        }
    }
    return std::nullopt;
}

std::optional<int> ObdReader::get_speed() {
    std::string resp = send_command("010D");
    std::string payload = extract_payload(resp, "410D");

    if (payload.length() >= 2) {
        int a = hex_to_int(payload.substr(0, 2));

        if (a != -1) {
            return a;
        }
    }
    return std::nullopt;
}