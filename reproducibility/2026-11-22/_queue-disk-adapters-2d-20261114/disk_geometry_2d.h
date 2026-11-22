#pragma once

using CoordinatePair = std::array<std::uint32_t, 2>;

struct Disk2D {
    CoordinatePair center;
    std::uint64_t radius_low;
    std::uint64_t radius_high;

    Disk2D(const Point& c, Wide squared)
        : center{c[0], c[1]}, radius_low(squared), radius_high(squared >> 64) {}

    bool contains(std::uint32_t x, std::uint32_t y) const {
        // Unsigned multiplication gives the exact square since |delta| <= UINT32_MAX.
        const auto dx = std::uint64_t(x) - center[0];
        const auto dy = std::uint64_t(y) - center[1];
        const auto xx = dx * dx;
        const auto sum = xx + dy * dy;
        const std::uint64_t carry = sum < xx;
        return (carry < radius_high) | ((carry == radius_high) & (sum <= radius_low));
    }

    std::pair<CoordinatePair, CoordinatePair> bounds() const {
        const Wide squared = (Wide(radius_high) << 64) | radius_low;
        // Any radius at least UINT32_MAX spans the full coordinate range on each axis.
        if (squared >= Wide(UINT32_MAX) * UINT32_MAX)
            return {{0, 0}, {UINT32_MAX, UINT32_MAX}};
        auto r = std::uint64_t(std::sqrt(double(squared)));
        if (r * r < squared) ++r;
        if (r && (r - 1) * (r - 1) >= squared) --r;
        CoordinatePair low, high;
        for (unsigned a = 0; a < 2; ++a) {
            low[a] = r > center[a] ? 0 : center[a] - r;
            high[a] = std::min<std::uint64_t>(UINT32_MAX, center[a] + r);
        }
        return {low, high};
    }
};

inline auto compact_coordinates(const Data& data) {
    auto points = std::make_shared<std::vector<CoordinatePair>>();
    points->reserve(data.points.size());
    for (const auto& p : data.points) points->push_back({p[0], p[1]});
    return points;
}
