import math

class Welford:
    """
    Implements Welford's algorithm for online calculation of mean and variance.
    This is useful for processing data points one by one without storing all of them.
    """
    def __init__(self):
        self.k = 0
        self.m = 0.0
        self.s = 0.0

    def update(self, x: float):
        """
        Update the running statistics with a new value.
        """
        self.k += 1
        old_m = self.m
        self.m += (x - old_m) / self.k
        self.s += (x - old_m) * (x - self.m)

    @property
    def mean(self) -> float:
        return self.m

    @property
    def variance(self) -> float:
        if self.k < 2:
            return 0.0
        return self.s / (self.k - 1)

    @property
    def std_dev(self) -> float:
        return math.sqrt(self.variance)

    def z_score(self, x: float) -> float:
        """
        Calculate the Z-score for a given value based on current statistics.
        """
        sd = self.std_dev
        if sd == 0:
            return 0.0
        return (x - self.mean) / sd
