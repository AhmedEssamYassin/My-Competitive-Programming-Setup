#include <bits/stdc++.h>
using namespace std;
#define ll long long int
#define ull unsigned long long
#define endl "\n"

ull fact[21];
ull C[21][21];

void precompute()
{
	fact[0] = 1;
	for (int i = 1; i <= 20; i++)
		fact[i] = fact[i - 1] * i;

	for (int i = 0; i <= 20; i++)
	{
		C[i][0] = 1;
		for (int j = 1; j <= i; ++j)
			C[i][j] = C[i - 1][j - 1] + C[i - 1][j];
	}
}
static int autoCall = (precompute(), 0);

ull cntWays(int m, int a)
{
	if (m < a)
		return 0;
	if (m > 20)
		return ULLONG_MAX;

	ull res = 0;
	for (int j = 0; j <= a; ++j)
	{
		ull term = C[a][j] * fact[m - j];
		res += (j & 1 ? -1 : 1) * term;
	}
	return res;
}

int main()
{
	ios_base::sync_with_stdio(false);
	cin.tie(nullptr);
#ifndef ONLINE_JUDGE
	// freopen("input.txt", "r", stdin);
	freopen("Output.txt", "w", stdout);
#endif //! ONLINE_JUDGE
	int t = 1;
	precompute();
	cin >> t;
	while (t--)
	{
		int n;
		ull k;
		cin >> n >> k;

		vector<int> p;
		vector<bool> used(n + 1, false);
		int mx = 21;
		if (n >= mx)
		{
			set<int> st;
			for (int i = 1; i <= n; i++)
				st.insert(i);

			for (int i = 1; i <= n - mx; i++)
			{
				auto it = st.begin();
				int x = *it;
				if (x != i)
				{
					p.push_back(x);
					used[x] = true;
					st.erase(it);
				}
				else
				{
					it++;
					int y = *it;
					p.push_back(y);
					used[y] = true;
					st.erase(it);
				}
			}
		}

		int b = (n >= mx) ? (n - mx + 1) : 1;

		for (int i = b; i <= n; i++)
		{
			int m = n - (i - 1);
			int a = 0;
			for (int x = i; x <= n; x++)
			{
				if (!used[x])
					a++;
			}

			for (int j = 1; j <= n; j++)
			{
				if (!used[j])
				{
					if (j == i)
						continue;

					int nxt = a;
					if (!used[i])
						nxt--;
					if (j > i)
						nxt--;

					ull ways = cntWays(m - 1, nxt);

					if (k <= ways)
					{
						p.push_back(j);
						used[j] = true;
						break;
					}
					else
						k -= ways;
				}
			}
		}

		for (int i = 0; i < n; i++)
			cout << p[i] << " ";
		cout << endl;
	}
	return 0;
}