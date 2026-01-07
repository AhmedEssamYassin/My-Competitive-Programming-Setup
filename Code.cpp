/*
Author: Ahmed Yassin
Created: 2026-01-07 23:36:09
*/
#include <bits/stdc++.h>
#ifndef ONLINE_JUDGE
#include "debug.cpp"
#define TIME_BLOCK(name)    \
	if (bool _once = false) \
	{                       \
	}                       \
	else                    \
		for (__DEBUG_UTIL__::LabeledTimer _t(name); !_once; _once = true)
#else
#define debug(...)
#define debugArr(...)
#define TIME_BLOCK(name) if (true)
#endif // Debugging locally
using namespace std;
#define ll long long int
#define endl "\n"

int main()
{
	ios_base::sync_with_stdio(false);
	cin.tie(nullptr);
#ifndef ONLINE_JUDGE
	// freopen("input.txt", "r", stdin);
	freopen("Output.txt", "w", stdout);
#endif // ONLINE_JUDGE
	int t = 1;
	// cin >> t;
	while (t--)
	{
		string str;
		cin >> str;
		ll cnt{}, cur{};
		vector<int> seen(3, 0);
		seen[0] = 1;
		for (int i{}; i < str.length(); i++)
		{
			(cur += str[i] - '0') %= 3;
			if (seen[cur])
				cnt++, cur = 0, fill(seen.begin(), seen.end(), 0), seen[0] = 1;
			else
				seen[cur] = 1;
		}
		cout << cnt << endl;
	}
	return 0;
}