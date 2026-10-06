#pragma once
#include <iterator>
#include <vector>
#include <sfcnn.hpp>
#include "sfc/common.hh"
namespace diskreport::sfc::app::algorithms::sfc {
class StannFR {
 public:
  using IDXT=uint32_t;
  using PointType=Point<IDXT>;
  using QueryType=Query<PointType>;
  using NativePoint=reviver::dpoint<unsigned int,2>;
  explicit StannFR(const std::vector<PointType>& points) {
    std::vector<NativePoint> input(points.size());
    for(size_t i=0;i<points.size();++i) {
      input[i][0]=points[i].x; input[i][1]=points[i].y;
    }
    index_.init_reporting(std::move(input));
  }
  template<class Output> void query(const QueryType& q, Output out) const {
    NativePoint lo,hi;
    lo[0]=q.p.x;lo[1]=q.p.y;hi[0]=q.q.x;hi[1]=q.q.y;
    index_.box_report(lo,hi,[&](const NativePoint& p) {
      *out++=PointType{p[0],p[1]};
    });
  }
 private:
  mutable sfcnn_work<NativePoint> index_;
};
}
