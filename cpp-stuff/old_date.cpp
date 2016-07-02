#include <iostream>

using namespace std;

// traditional C way
struct date {
 int dt_month;
 int dt_day;
 int dt_year;
};

void display_date(date &dt)
{
  cout << "Date: "<< dt.dt_month 
			 << "/" << dt.dt_day
			 << "/" << dt.dt_year << endl;
}

int main()
{
  date dt;
	dt.dt_day = 4; dt.dt_month = 11; dt.dt_year = 2016;
	display_date(dt);
	return 0;
}
