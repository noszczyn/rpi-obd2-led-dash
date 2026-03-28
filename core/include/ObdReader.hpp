#pragma once

#include <string>
#include <optional>

class ObdReader {
    public:
        ObdReader(const std::string& device_path);

        ~ObdReader();

        bool connect();
        bool initialize();

        std::optional<float> get_rpm();
        std::optional<int> get_speed();
    private:
        std::string m_device_path;

        int m_serial_fd;

        std::string send_command(const std::string& cmd);
        std::string extract_payload(const std::string& response, const std::string& expected_header);

        int hex_to_int(const std::string& hex_str);
};