// TODO: XXXX-3 needs credit where credit due

#ifndef HCDS_H
#define HCDS_H

#include <vector>
#include <tuple>
#include <algorithm>
#include <cmath>
#include <execution>

#ifdef PARALLEL
constexpr auto policy = std::execution::par;
#else
constexpr auto policy = std::execution::seq;
#endif

template<typename> struct rank_t;
template<> struct rank_t<u_int8_t> {using type=u_int16_t;};
template<> struct rank_t<u_int16_t> {using type=u_int32_t;};
template<> struct rank_t<u_int32_t> {using type=u_int64_t;};

template<typename T>
struct Point{
    T x;
    T y;
};

template<typename Input_t, typename Key_t = Input_t, bool hilbert = true>
struct HCDS {
    using Rank_t = typename rank_t<Key_t>::type;
    using Point = ::Point<Input_t>;

    constexpr static auto max_number_of_bits= sizeof(Key_t) * 8;
    constexpr static Input_t W = std::numeric_limits<Key_t>::max();
    constexpr static Input_t H = std::numeric_limits<Key_t>::max();
    Input_t x_l,y_l,x_u,y_u, S;

    std::vector<Point> points;

    // Construct by associative sorting
    explicit HCDS(const std::vector<Point>& input){
        points.reserve(input.size());
        std::vector<std::pair<Rank_t,Point>> temp;
        temp.reserve(input.size());

        if constexpr (!std::is_same<Input_t, Key_t>::value){
            auto iter = input.cbegin();
            x_l = (*iter).x;
            y_l = (*iter).y;
            x_u = x_l;
            y_u = y_l;
            for(; iter != input.cend(); ++iter){
                x_l = std::min(x_l,(*iter).x);
                y_l = std::min(y_l,(*iter).y);
                x_u = std::max(x_u,(*iter).x);
                y_u = std::max(y_u,(*iter).y);
            }
            S = W/(std::max(x_u-x_l,y_u-y_l));
            if(S == 0) S = 1;
        }

        // Zip
        for (const Point& p: input) {
            temp.emplace_back(std::make_pair(getRank(transformx(p.x), transformy(p.y)),p));
            //std::cout << "Point (x,y): (" << p.x << "," << p.y << ")\n";
            //std::cout << "Rank Hilbert: " << getRank(p) << "\n";
            //std::cout << "Rank Quadtree: " << getRankQuadtree(p) << "\n";
        }

        // Sort
        std::sort(policy,temp.begin(), temp.end(),[](const std::pair<Rank_t,Point>& lhs, const std::pair<Rank_t,Point>& rhs){return lhs.first < rhs.first;});

        // Unzip
        for(const auto& e: temp){
            points.emplace_back(e.second);
        }
    }

    inline
    Key_t transformx(const Input_t& x) const {
        if constexpr (std::is_same<Input_t,Key_t>::value) return x;
        if(x < x_l) return 0;
        else if (x > x_u) return S*(x_u-x_l);
        else return S*(x-x_l);
    }
    inline
    Key_t transformy(const Input_t& y) const {
        if constexpr (std::is_same<Input_t,Key_t>::value) return y;
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


    // Compute the rank of a point (x,y,z) in the 3D quadtree
    // XXXX-2: The result of this should probably not be an RT, as we now get 3 bits per level instead of 2
    // XXXX-1: XXXX-2 is right. We should probably use 2 ints of RT rather than a type with 2*sizeof(RT) bits
    static Rank_t getRankQuadtree3D(const Key_t& x, const Key_t& y, const Key_t& z, const size_t& max_depth=max_number_of_bits) {
        Rank_t result = 0;

        for (size_t depth = 1; depth <= max_depth; ++depth) {

            Key_t xdigit = (x >> (max_number_of_bits - depth)) % 2;
            Key_t ydigit = (y >> (max_number_of_bits - depth)) % 2;
            Key_t zdigit = (z >> (max_number_of_bits - depth)) % 2;


            int suffix = 0;

            if (depth > 1)
                result = result << 3;

            if (xdigit == 0 && ydigit == 0 && zdigit == 0) {
                suffix += 0;
            }
            if (xdigit == 1 && ydigit == 0 && zdigit == 0) {
                suffix += 1;
            }
            if (xdigit == 0 && ydigit == 1 && zdigit == 0)  {
                suffix += 2;
            }
            if (xdigit == 0 && ydigit == 0 && zdigit == 1) {
                suffix += 4;
            }
            if (xdigit == 0 && ydigit == 1 && zdigit == 1) {
                suffix += 6;
            }
            if (xdigit == 1 && ydigit == 1 && zdigit == 0) {
                suffix += 3;
            }
            if (xdigit == 1 && ydigit == 0 && zdigit == 1)  {
                suffix += 5;
            }
            if (xdigit == 1 && ydigit == 1 && zdigit == 1) {
                suffix += 7;
            }
            result += suffix;
        }

        // XXXX-2: should this here indeed be 3 as well?
        result = result << (3 * (max_number_of_bits - max_depth));
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
    static Rank_t getRankHilbert(const Key_t& x, const Key_t& y, const size_t& max_depth=max_number_of_bits) {
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

    static Rank_t getRank(const Key_t& x, const Key_t& y, const size_t& max_depth=max_number_of_bits){
        if constexpr (hilbert) return getRankHilbert(x,y,max_depth);
        else return getRankQuadtree(x,y,max_depth);
    }

    // Input: a single corner (x, y) of a query square with diameter [diameter]
    // Output: the lower bound and upper bound of ranks corresponding to this corner.
    static std::pair<Rank_t,Rank_t> getQueryMinAndMax(const Key_t& x, const Key_t& y, const Key_t &diameter) {
        // consider the maximum integer s = 2^x such that s < radius
        // the integer max_depth = x
        size_t max_depth = max_number_of_bits - (((size_t) ceil((log2(diameter))))*(diameter!=0));


        // The lower bound is the coordinate of x, y if we were to stop computing after max_depth
        Rank_t first = getRank(x, y, max_depth);

        // The upper bound is the lower bound coordinate, plus 1
        Rank_t second = ((first >> (2 * (max_number_of_bits - max_depth))) + 1)
                << (2 * (max_number_of_bits - max_depth));

        return {first, second};
    }

    void
    query(const Point& p, const Point& q, auto&& output){
        const Key_t xl = transformx(p.x);
        const Key_t xr = transformx(q.x);
        const Key_t yl = transformy(p.y);
        const Key_t yr = transformy(q.y);
        const Key_t diameter = std::max(xr - xl, yr - yl);
        // We generate a report range for each corner of the rectangle
        std::vector<std::pair<Rank_t, Rank_t>> report_ranges;
        report_ranges.reserve(4);
        report_ranges.push_back(getQueryMinAndMax(xl, yl, diameter));
        report_ranges.push_back(getQueryMinAndMax(xr, yl, diameter));
        report_ranges.push_back(getQueryMinAndMax(xl, yr, diameter));
        report_ranges.push_back(getQueryMinAndMax(xr, yr, diameter));

        std::sort(report_ranges.begin(),report_ranges.end());

        Point val;
        Rank_t lowerbound, upperbound;
        auto start = points.begin();
        auto end = points.end();
        for (const auto &report_range: report_ranges) {
            lowerbound = report_range.first;
            upperbound = report_range.second;

            start = std::lower_bound(start, end, lowerbound,[](const Point& p, const Rank_t& r){return getRank(p.x,p.y) < r;});
            end = std::upper_bound(start, end, upperbound,[](const Rank_t& r, const Point& p){return r < getRank(p.x,p.y);});

            while (start != end) {
                val = *start;

                if (val.x >= p.x && val.x <= p.x + diameter && val.y >= p.y && val.y <= p.y + diameter) {
                    *output = val;
                }
                start++;
            }

            start = end;
            end = points.end(); // This can be optimised?
        }
    }

    std::vector<Point>
    query(const Point &p, const double &diameter) {
        Input_t x = p.x + diameter;
        Input_t y = p.y + diameter;
        return query(p,{x,y});
    }
};

#endif //HCDS_H
