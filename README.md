# dateextractor

Basic Example is given in the `DateFinder.py` file itself!

	from DateExtractor import DateFinder

	df = DateFinder()

    # This `find_dates(text)` returns a list of datetime objects taking a string/buffer as a parameter 
    date_list = df.find_dates('<foobar> (oct 2013 to december 2014) </foobar>')

    print date_list
    # prints:  [datetime.datetime(2013, 10, 1, 0, 0), datetime.datetime(2014, 12, 1, 0, 0)]
    
    print DateFinder.get_period(date_list[0], date_list[1], in_years=True)