#include <limits>
#include <cmath>
#include "GearPredictor.hpp"

int GearPredictor::gear_predict(float rpm, int speed){
    if (rpm <= 0.0f || speed <= 0) {
        return 0;
    }

    int predicted_gear = -1;
    float ratio_delta = std::numeric_limits<float>::infinity();

    if (speed < Config::NEUTRAL_SPEED_LIMIT){
        predicted_gear = 0;
    }
    else {
        float current_ratio = rpm / speed;

        for (size_t gear = 1; gear < Config::GEARS_RATIOS.size();gear++) {
            float gear_ratio = Config::GEARS_RATIOS[gear];
            float deviation = std::abs(current_ratio - gear_ratio);
            float gear_tolerance = gear_ratio * Config::GEAR_TOLERANCE;

            if (deviation < gear_tolerance && deviation < ratio_delta) {
                ratio_delta = deviation;
                predicted_gear = gear;
            }
        }
    }

    return predicted_gear;
}