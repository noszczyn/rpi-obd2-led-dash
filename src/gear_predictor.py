import time
from collections import deque

import config


def _median(values: deque[int]) -> int:
    """Median dla dowolnej długości deq (małe N, więc sortowanie jest OK)."""
    xs = sorted(values)
    return xs[len(xs) // 2]


def predict_gear_raw(rpm: float, speed: float) -> int:
    """Tylko dopasowanie RPM/speed do tabeli; -1 gdy brak pasma lub speed za niski."""
    if speed < config.MIN_SPEED_FOR_RATIO:
        return -1
    current_ratio = rpm / speed
    ratio_delta = float("inf")
    predicted_gear = -1
    for gear, gear_ratio in config.GEARS_RATIOS.items():
        if gear == 0:
            continue
        deviation = abs(current_ratio - gear_ratio)
        gear_tolerance = max(gear_ratio * config.GEAR_TOLERANCE, 1e-6)
        if deviation < gear_tolerance and deviation < ratio_delta:
            ratio_delta = deviation
            predicted_gear = gear
    return predicted_gear


def gear_deviation(rpm: float, speed: float, gear: int) -> float | None:
    if speed < config.MIN_SPEED_FOR_RATIO or gear <= 0:
        return None
    gr = config.GEARS_RATIOS.get(gear)
    if gr is None:
        return None
    return abs(rpm / speed - gr)


def apply_neutral_deadband(speed: float, stable_gear: int, raw_gear: int) -> int:
    """Histereza luzu + nie maskuj nieznanego.

    - stable_gear < 0 => unknown (nie wymuszamy 0).
    - stable_gear == 0 => neutral dopiero gdy speed < OFF (i nie gaś cyfry za wcześnie).
    - stable_gear > 0 => z biegu wracamy do 0, gdy speed <= ON.
    """
    # stable_gear == -1 => unknown (start / brak stabilnego dopasowania).
    # W tym stanie nie forsujemy od razu "0" (neutral), bo ukrywa to true unknown.
    if stable_gear < 0:
        if speed <= config.NEUTRAL_SPEED_ON:
            return -1
        return raw_gear

    if stable_gear == 0:
        if speed < config.NEUTRAL_SPEED_OFF:
            return 0
        return raw_gear

    # stable_gear > 0
    if speed <= config.NEUTRAL_SPEED_ON:
        return 0
    return raw_gear


class GearHysteresis:
    """Utrzymuj stabilny bieg; zmiana po K próbach i lepszym dopasowaniu niż próg."""

    def __init__(self) -> None:
        self.stable_gear = -1
        self._cand: int | None = None
        self._cnt = 0

    def update(self, m: int, rpm: float, speed: float) -> None:
        if m < 0:
            return
        if m == self.stable_gear:
            self._cand = None
            self._cnt = 0
            return
        if m != self._cand:
            self._cand = m
            self._cnt = 1
        else:
            self._cnt += 1
        k = config.GEAR_HYSTERESIS_K
        if self._cnt < k:
            return
        if m == 0:
            self.stable_gear = 0
        elif self.stable_gear <= 0:
            self.stable_gear = m
        elif self.stable_gear > 0 and m > 0:
            d_s = gear_deviation(rpm, speed, self.stable_gear)
            d_m = gear_deviation(rpm, speed, m)
            if (
                d_m is not None
                and d_s is not None
                and d_m + config.GEAR_HYSTERESIS_DEV_MARGIN < d_s
            ):
                self.stable_gear = m
        self._cand = None
        self._cnt = 0


class GearPipeline:
    """Median z ostatnich `GEAR_FILTER_LEN`, deadband luzu, histereza biegu, unknown hold."""

    def __init__(self) -> None:
        self._hyst = GearHysteresis()
        self._hist: deque[int] = deque(maxlen=config.GEAR_FILTER_LEN)
        self._last_valid_t = 0.0
        self._last_valid_g = -1

    def history_snapshot(self) -> list[int]:
        return list(self._hist)

    def step(
        self,
        raw_rpm: float,
        speed: float,
        last_displayed_gear: int,
        has_last_raw_rpm: bool,
        last_raw_rpm: float,
    ) -> int:
        raw = predict_gear_raw(raw_rpm, speed)
        g = apply_neutral_deadband(speed, self._hyst.stable_gear, raw)
        if (
            last_displayed_gear > 0
            and g > last_displayed_gear
            and has_last_raw_rpm
            and (raw_rpm - last_raw_rpm) > config.RPM_RISE_DOWNSHIFT_GUARD
        ):
            g = last_displayed_gear

        # Guard na fałszywy downshift przy hamowaniu bez redukcji:
        # realny downshift zwykle powoduje szybki wzrost RPM (skok w górę),
        # a podczas hamowania w tym samym biegu RPM raczej spada.
        if (
            last_displayed_gear > 0
            and g > 0
            and g < last_displayed_gear
            and has_last_raw_rpm
            and (raw_rpm - last_raw_rpm) < config.RPM_DOWN_SHIFT_CONFIRM_RISE
        ):
            g = last_displayed_gear

        self._hist.append(g)
        if len(self._hist) < self._hist.maxlen:
            return -1

        m = _median(self._hist)
        self._hyst.update(m, raw_rpm, speed)
        now_t = time.monotonic()
        sg = self._hyst.stable_gear

        if sg >= 0:
            self._last_valid_t = now_t
            self._last_valid_g = sg
            return sg
        if (
            self._last_valid_g >= 0
            and (now_t - self._last_valid_t) < config.GEAR_UNKNOWN_HOLD_SEC
        ):
            return self._last_valid_g
        return -1
