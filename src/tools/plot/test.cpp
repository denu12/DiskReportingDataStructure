#include <iostream>
#include <map>
#include <utility>
//
std::map<std::pair<long, long>, int> x;
// std::map<std::pair<NodeType, NodeType>, CountType>
//     neighbours;  // only entries for NodeTypeA <NodeTypeB
// // lookup
// neighbours[{std::min(A, B), std::max(A, B)}]
int main() { std::cout << sizeof(x) << std::endl; }