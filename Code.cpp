/*
Author: Ahmed Yassin
Created: 2025-11-26 11:21:54
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
	freopen("input.txt", "r", stdin);
	freopen("Output.txt", "w", stdout);
#endif // ONLINE_JUDGE
	int t = 1;
	cin >> t;
	while (t--)
	{
		int n;
		cin >> n;
		vector<ll> vc(n);
		for (int i{}; i < n; i++)
			cin >> vc[i];
		debug(vc);
		cout << (vc[0] < vc[n - 1] ? "YES\n" : "NO\n");
	}
	return 0;
}