#pragma once
// Fixed-radius reporting derived directly from Timothy Chan's sss-original.cc.
// Original: Timothy Chan, 12/05. Original source and notice remain unchanged.
// Keep qsort, random shift, midpoint-first recursion and distance-to-cell pruning.
// Changes: fixed radius, emitted IDs, inclusive bounds, widened exact arithmetic.
#include <cstdlib>

class ChanReporting {
    const Data& data;
    std::vector<const Point*> order;
    std::uint64_t shift;
    Point lower, upper;
    inline static thread_local const ChanReporting* sorting=nullptr;
    static bool less_msb(std::uint64_t x,std::uint64_t y) {return x<y && x<(x^y);}
    int compare(const Point& p,const Point& q) const {
        unsigned j=0;std::uint64_t x=0;
        for(unsigned k=0;k<data.d;++k) {
            auto y=(std::uint64_t(p[k])+shift)^(std::uint64_t(q[k])+shift);
            if(less_msb(x,y)){j=k;x=y;}
        }
        return (p[j]>q[j])-(p[j]<q[j]);
    }
    static int comparator(const void* p,const void* q) {
        return sorting->compare(**static_cast<const Point* const*>(p),**static_cast<const Point* const*>(q));
    }
    Wide distance_to_box(const Point& q,const Point& p1,const Point& p2) const {
        std::uint64_t x=0;
        for(unsigned j=0;j<data.d;++j) {
            auto y=(std::uint64_t(p1[j])+shift)^(std::uint64_t(p2[j])+shift);
            if(less_msb(x,y))x=y;
        }
        auto bits=std::bit_width(x);Wide distance=0;
        for(unsigned j=0;j<data.d;++j) {
            auto low=((std::uint64_t(p1[j])+shift)>>bits)<<bits;
            auto high=low+(std::uint64_t{1}<<bits),v=std::uint64_t(q[j])+shift;
            auto delta=v<low?low-v:v>high?v-high:0;
            distance+=Wide(delta)*delta;
        }
        return distance;
    }
    void search(std::size_t first,std::size_t n,std::size_t query,
                const Point& lo,const Point& hi,std::vector<std::size_t>& hits) const {
        if(!n)return;
        auto mid=first+n/2;auto id=std::size_t(order[mid]-data.points.data());
        if(data.contains(id,query))hits.push_back(id);
        const auto& q=data.centers[query];
        if(n==1 || distance_to_box(q,*order[first],*order[first+n-1])>data.radii[query])return;
        if(compare(q,*order[mid])<0) {
            search(first,n/2,query,lo,hi,hits);
            if(compare(hi,*order[mid])>=0)search(mid+1,n-n/2-1,query,lo,hi,hits);
        } else {
            search(mid+1,n-n/2-1,query,lo,hi,hits);
            if(compare(lo,*order[mid])<=0)search(first,n/2,query,lo,hi,hits);
        }
    }
public:
    explicit ChanReporting(const Data& d):data(d),lower(d.d),upper(d.d) {
        // Same generator and seed formula as Chan's driver.
        srand48(12121+data.points.size()+data.centers.size()+data.d);
        shift=std::uint64_t(drand48()*(1<<29));
        order.reserve(data.points.size());
        for(const auto& point:data.points)order.push_back(&point);
        sorting=this;
        std::qsort(order.data(),order.size(),sizeof(const Point*),comparator);
        sorting=nullptr;
    }
    void report(std::size_t q,std::vector<std::size_t>& hits) {
        hits.clear();
        // Keep the original sqrt-based bounds; correct rounding in integer arithmetic.
        auto r2=data.radii[q];
        auto lo=r2>=Wide(UINT64_MAX)*UINT64_MAX ? UINT64_MAX
            : std::uint64_t(std::sqrt(static_cast<long double>(r2)));
        while(lo<UINT64_MAX && Wide(lo)*lo<r2)++lo;
        while(lo && Wide(lo-1)*(lo-1)>=r2)--lo;
        for(unsigned a=0;a<data.d;++a){auto c=data.centers[q][a];lower[a]=lo>c?0:c-lo;upper[a]=lo>UINT32_MAX-c?UINT32_MAX:c+lo;}
        search(0,order.size(),q,lower,upper,hits);
    }
};
