/*
 * Solution by Edgar Duéñez-Guzmán
 * https://youtu.be/XKu_SEDAykw?t=14m53s
 */
#include <iostream>
#include <unordered_set>
#include <vector>

using namespace std;

bool HasPairWithSum(const vector<int>& data, int sum)
{
        unordered_set<int> comp; // complements
        for (int value : data) 
        {
                if (comp.find(value) != comp.end()) return true;
                comp.insert(sum-value);
        }
        return false;
}

int main()
{
        int myints1[] = {1,2,4,9};
        vector<int> input1 (myints1, myints1 + sizeof(myints1) / sizeof(int) );
        cout << HasPairWithSum(input1, 8) << endl;

        int myints2[] = {1,2,4,4};
        vector<int> input2 (myints2, myints2 + sizeof(myints2) / sizeof(int) );
        cout << HasPairWithSum(input2, 8) << endl;

        return 0;
}
