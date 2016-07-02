#include <iostream>

using namespace std;

class Date {
private:
  int dt_month;
	int dt_day;
	int dt_year;
public:
  Date(int month, int day, int year);
	void Display();
};

Date::Date(int month, int day, int year)
{
  dt_month = month; dt_day = day; dt_year = year;
}

void Date::Display()
{
  cout << dt_month << "/" << dt_day << "/" << dt_year << endl;
}

int main()
{
  Date date(11,4,2001);
	date.Display();
	return 0;
}
