// TODO: XXXX-3 needs credit where credit due

#ifndef HCDS_H
#define HCDS_H

#include <vector>
#include <tuple>
#include <algorithm>
#include <cmath>


template<typename> struct rank_t;
template<> struct rank_t<u_int8_t> {using type=u_int16_t;};
template<> struct rank_t<u_int16_t> {using type=u_int32_t;};
template<> struct rank_t<u_int32_t> {using type=u_int64_t;};

template<typename Input_t, typename Key_t, typename Val_t, bool hilbert = true>
class HCDS {
    using Rank_t=typename rank_t<Key_t>::type;
    using Coord_t=std::remove_cvref_t<decltype(std::declval<Input_t>().x())>;

    struct Point {
        Key_t x,y;
    };
    struct Triple {
        Rank_t r;
        Point p;
        Val_t v;
    };

protected:
    constexpr static auto max_number_of_bits=sizeof(Key_t)*8;
    constexpr static Coord_t W = std::numeric_limits<Key_t>::max();
    constexpr static Coord_t H = std::numeric_limits<Key_t>::max();
    Coord_t x_l,y_l,x_u, y_u, S;
    std::vector<Rank_t> ranks;
    std::vector<Point> points;
    std::vector<Val_t> values;

public:
    HCDS() = default;

    // Construct by associative sorting
    template<typename Container>
    explicit HCDS(const Container& input){
        size_t n = input.size();
        points.reserve(n);
        ranks.reserve(n);
        values.reserve(n);
        std::vector<Triple> temp;
        temp.reserve(n);

        // Compute bounds
        auto iter = input.cbegin();
        x_l = (*iter).x();
        y_l = (*iter).y();
        x_u = x_l;
        y_u = y_l;
        for(; iter != input.cend(); ++iter){
            x_l = std::min(x_l,(*iter).x());
            y_l = std::min(y_l,(*iter).y());
            x_u = std::max(x_u,(*iter).x());
            y_u = std::max(y_u,(*iter).y());
        }
        S = W/(std::max(x_u-x_l,y_u-y_l));

        // Zip
        Val_t count = 0;
        Key_t x,y;
        for (const auto& e: input) {
            x = transformx(e.x());
            y = transformy(e.y());
            temp.emplace_back(getRank(x,y),Point{x,y},count++);
        }

        // Sort
        std::sort(temp.begin(), temp.end(), [](const Triple& lhs, const Triple& rhs){return lhs.r < rhs.r;});

        // Unzip
        for(const Triple& e: temp){
            ranks.emplace_back(e.r);
            points.emplace_back(e.p);
            values.push_back(e.v);
        }
    }

protected:
    inline
    Key_t transformx(const Coord_t& x) const {
        if constexpr (std::is_same<Key_t,Coord_t>::value) return x;
        if(x < x_l) return 0;
        else if (x > x_u) return S*(x_u-x_l);
        else return S*(x-x_l);
    }
    inline
    Key_t transformy(const Coord_t& y) const {
        if constexpr (std::is_same<Key_t,Coord_t>::value) return y;
        if(y < y_l) return 0;
        else if (y > y_u) return S*(y_u-y_l);
        else return S*(y-y_l);
    }

    // Compute the rank of a point (x,y) in the quadtree
    static Rank_t getRankQuadtree(const Key_t& x, const Key_t& y, const size_t& max_depth=max_number_of_bits) {
        Rank_t result = 0;

        for (size_t depth = 1; depth <= max_depth; ++depth) {

            Key_t xdigit = (x >> (max_number_of_bits - depth)) % 2;
            Key_t ydigit = (y >> (max_number_of_bits - depth)) % 2;


            int suffix = 0;

            if (depth > 1)
                result = result << 2;

            if (xdigit == 0 && ydigit == 0) {
                suffix += 0;
            }
            if (xdigit == 1 && ydigit == 0) {
                suffix += 1;
            }
            if (xdigit == 0 && ydigit == 1) {
                suffix += 2;
            }
            if (xdigit == 1 && ydigit == 1) {
                suffix += 3;
            }
            result += suffix;
        }

        result = result << (2 * (max_number_of_bits - max_depth));
        return result;
    }

    // Compute the rank of a point (x, y) along the Hilbert curve
    // We first consider the geometric coordinates:  00, 01, 11, 10
    //
    // We then consider one of four rotation types, which assign an integer in [0, 3] to each of these four coordinates
    //
    // 0 = ⊃ = 00, 11, 10, 01
    // 1 = Π = 00, 01, 10, 11
    // 2 = ⊂ = 10, 01, 00, 11
    // 3 = U  = 10, 11, 00, 01
    static Rank_t getRankHilbert(const Key_t& x, const Key_t& y, const size_t& max_depth=max_number_of_bits)  {
        Rank_t result = 0;
        int rotation = 1;

        for (size_t depth = 1; depth <= max_depth; ++depth) {

            Key_t xdigit = (x >> (max_number_of_bits - depth)) % 2;
            Key_t ydigit = (y >> (max_number_of_bits - depth)) % 2;

            if (depth > 1)
                result = result << 2;


            int suffix = 0;

            // We consider rotation 0
            // ⊃ = 00, 11, 10, 01
            if (rotation == 0) {

                if (xdigit == 0 && ydigit == 0) {
                    suffix += 0;
                }
                if (xdigit == 0 && ydigit == 1) {
                    suffix += 3;
                }
                if (xdigit == 1 && ydigit == 1) {
                    suffix += 2;
                }
                if (xdigit == 1 && ydigit == 0) {
                    suffix += 1;
                }
            }

            // We consider rotation 1
            // Π = 00, 01, 10, 11
            if (rotation == 1) {

                if (xdigit == 0 && ydigit == 0) {
                    suffix += 0;
                }
                if (xdigit == 0 && ydigit == 1) {
                    suffix += 1;
                }
                if (xdigit == 1 && ydigit == 1) {
                    suffix += 2;
                }
                if (xdigit == 1 && ydigit == 0) {
                    suffix += 3;
                }
            }
            // We do rotation 2
            // ⊂ = 10, 01, 00, 11
            if (rotation == 2) {
                if (xdigit == 0 && ydigit == 0) {
                    suffix += 2;
                }
                if (xdigit == 0 && ydigit == 1) {
                    suffix += 1;
                }
                if (xdigit == 1 && ydigit == 1) {
                    suffix += 0;
                }
                if (xdigit == 1 && ydigit == 0) {
                    suffix += 3;
                }
            }
            // Finally, we do rotation 3
            // U  = 10, 11, 00, 01
            if (rotation == 3) {
                if (xdigit == 0 && ydigit == 0) {
                    suffix += 2;
                }
                if (xdigit == 0 && ydigit == 1) {
                    suffix += 3;
                }
                if (xdigit == 1 && ydigit == 1) {
                    suffix += 0;
                }
                if (xdigit == 1 && ydigit == 0) {
                    suffix += 1;
                }
            }

            // Based on the current rotation, and the suffix we just added,
            // we get a new rotation number
            if ((rotation % 2 == 1 && suffix == 0) || (rotation % 2 == 0 && suffix == 3))
                rotation = (rotation + 3) % 4;
            else if ((rotation % 2 == 1 && suffix == 3) || (rotation % 2 == 0 && suffix == 0))
                rotation = (rotation + 1) % 4;
            result += suffix;
        }

        result = result << (2 * (max_number_of_bits - max_depth));
        return result;
    }

    static Rank_t getRank(const Point& p, const size_t& max_depth=max_number_of_bits) {
        return getRank(p.x,p.y,max_depth);
    }

    static Rank_t getRank(const Key_t& x, const Key_t& y, const size_t& max_depth=max_number_of_bits){
        if constexpr (hilbert) return getRankHilbert(x,y,max_depth);
        else return getRankQuadtree(x,y,max_depth);
    }

    // Input: a single corner (x, y) of a query square with diameter [diameter]
    // Output: the lower bound and upper bound of ranks corresponding to this corner.
    std::pair<Rank_t,Rank_t> getQueryMinAndMax(const Key_t& x, const key_t& y, const double &diameter) {
        // consider the maximum integer s = 2^x such that s < radius
        // the integer max_depth = x
        size_t max_depth = max_number_of_bits - ((size_t) ceil((log2(diameter))));

        // The lower bound is the coordinate of x, y if we were to stop computing after max_depth
        Rank_t first = getRank(x,y, max_depth);

        // The upper bound is the lower bound coordinate, plus 1
        Rank_t second = ((first >> (2 * (max_number_of_bits - max_depth))) + 1)
                << (2 * (max_number_of_bits - max_depth));

        return {first, second};
    }

public:
    void
    query(const Input_t& p, const double &radius, auto&& output) {
        Key_t xl = transformx(p.x() - radius);
        Key_t xr = transformx(p.x() + radius);
        Key_t yl = transformy(p.y() - radius);
        Key_t yu = transformy(p.y() + radius);
        //Key_t rad = radius;
        const double diameter = std::max(Key_t(1),Key_t(std::max(xr-xl,yu-yl)));

        // We generate a report range for each corner of the rectangle
        std::vector<std::pair<Rank_t, Rank_t>> report_ranges;
        report_ranges.reserve(4);
        report_ranges.push_back(getQueryMinAndMax(xl, yl, diameter));
        report_ranges.push_back(getQueryMinAndMax(xr, yl, diameter));
        report_ranges.push_back(getQueryMinAndMax(xl, yu, diameter));
        report_ranges.push_back(getQueryMinAndMax(xr, yu, diameter));

        std::sort(report_ranges.begin(),report_ranges.end());

        Rank_t lowerbound, upperbound;
        auto start = ranks.begin();
        auto end = ranks.end();

        size_t offset_b;
        size_t offset_e;

        for (const auto &report_range: report_ranges) {
            lowerbound = report_range.first;
            upperbound = report_range.second;

            start = std::lower_bound(start, end, lowerbound);
            end = std::upper_bound(start, end, upperbound); // TODO: Can we eliminate this?
            // TODO: Walk until prefix changes

            offset_b = start - ranks.begin();
            offset_e = end - ranks.begin();

            for(size_t i = offset_b; i<offset_e; ++i){
                // TODO: Adapt filtering to disks also
                // TODO: Adapt filtering in general
                const auto& c = points[i];
                if (c.x >= xl && c.x <= xr && c.y >= yl && c.y <= yu) {
                    *output = values[i];
                }
            }

            start = end;
            end = ranks.end(); // This can be optimised
        }
    }
};

#endif //HCDS_H
