/*
 * Solution by Edgar Duéñez-Guzmán
 * https://youtu.be/XKu_SEDAykw?t=14m53s
 */
#include <iostream>
#include <unordered_set>
#include <vector>

using namespace std;

bool HasPairWithSum(const vector<int>& data, int sum) {
        unordered_set<int> comp; // additive complements
        for (int value : data) {
                if (comp.find(value) != comp.end()) return true;
                comp.insert(sum-value);
        }
        return false;
}

int main() {
        cout << HasPairWithSum({1,2,4,9}, 8) << endl;
        cout << HasPairWithSum({1,2,4,4}, 8) << endl;
}
