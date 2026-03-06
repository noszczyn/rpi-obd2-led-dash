import config

def predict_gear(rpm, speed):
    if speed < config.NEUTRAL_SPEED_LIMIT:
        predicted_gear = 0
    else:
        current_ratio = rpm / speed
        ratio_delta = float("inf")
        
        predicted_gear = -1

        for gear, gear_ratio in config.GEARS_RATIOS.items():
            deviation = abs(current_ratio - gear_ratio)
            gear_tolerance =  gear_ratio * config.GEAR_TOLERANCE # MAXIMAL ALLOWED DEVIATION 

            if deviation < gear_tolerance and deviation < ratio_delta:
                ratio_delta = deviation
                predicted_gear = gear

    return predicted_gear