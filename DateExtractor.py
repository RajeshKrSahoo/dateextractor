# coding: utf-8
import copy
import logging
import regex as re
from dateutil import tz, parser
from datetime import date
import itertools
import datetime
import math
class DateFinder(object):

    DIGITS_MODIFIER_PATTERN = '\d+st|\d+th|\d+rd|first|second|third|fourth|fifth|sixth|seventh|eighth|nineth|tenth|next|last'
    DIGITS_PATTERN = '\d+'
    DAYS_PATTERN = 'monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|tues|wed|thur|thurs|fri|sat|sun'
    MONTHS_PATTERN = 'january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec'
    DELIMITERS_PATTERN = "[/\:\-\,\’\s\_\+\@\']+"
    EXTRA_TOKENS_PATTERN = 'till date|present'

    DATES_PATTERN = """
    (
        (
            ## Grab any digits
            (?P<digits_modifier>{digits_modifier})
            |
            (?P<digits>{digits})
            |
            (?P<months>{months})
            |
            (?P<delimiters>{delimiters})
            | 
            (?P<extra_tokens>{extra_tokens})
        ){{3,}}
    )
    """
    MULTIPLE_DATE_PATTERN = """

    """
    DATES_PATTERN = DATES_PATTERN.format(
        digits=DIGITS_PATTERN,
        digits_modifier=DIGITS_MODIFIER_PATTERN,
        days=DAYS_PATTERN,
        months=MONTHS_PATTERN,
        delimiters=DELIMITERS_PATTERN,
        extra_tokens=EXTRA_TOKENS_PATTERN
    )
    REPLACEMENTS = {
        "’": "/",
        "'": "/",
        "`": "/",
        
    }
    DATE_REGEX = re.compile(DATES_PATTERN, re.IGNORECASE | re.MULTILINE | re.UNICODE | re.DOTALL | re.VERBOSE)
    STRIP_CHARS = ' \n\t:-.,_'

    def __init__(self, base_date=None):
        self.base_date = base_date

    def find_dates(self, text, source=False, index=False):
        date_list = []
        text = re.sub('present|till date', ' to '+ date.today().strftime('%d/%m/%Y'), text, flags = re.IGNORECASE)
        for date_string, indices, captures in self.extract_date_strings(text):

            as_dt = self.parse_date_string(date_string, captures)
            if as_dt is None:
                continue

            returnables = (as_dt,)
            if source:
                returnables = returnables + (date_string,)
            if index:
                returnables = returnables + (indices,)

            if len(returnables) == 1:
                returnables = returnables[0]
            date_list.append(returnables)
        return date_list

    def _find_and_replace(self, date_string, captures):
        for key, value in self.REPLACEMENTS.items():
            date_string = date_string.replace(key, value)
        # print date_string
        return date_string
    def parse_date_string(self, date_string, captures):
        try:
            as_dt = parser.parse(date_string, default=self.base_date)
        except ValueError:
            date_string = self._find_and_replace(date_string, captures)
            # print date_string

            date_string = date_string.strip(self.STRIP_CHARS)
            if len(date_string) < 3:
                return None

            try:

                as_dt = parser.parse(date_string, default=self.base_date)
            except Exception as e:
                as_dt = None
        return as_dt

    def add_period_delimiter(self, text):
        # print text
        for match in self.DATE_REGEX.finditer(text):
            match_str = match.group(0)
            indices = match.span(0)
            captures = match.capturesdict()
            digits = captures.get('digits')
            # print digits
            digits_modifiers = captures.get('digits_modifiers')
            months = captures.get('months')
            delimiters = captures.get('delimiters')
            extra_tokens = captures.get('extra_tokens')
            prev = 0
            try:
                if len(months) == 2 or len(digits) > 3 or len(digits_modifiers) > 1:

                    mid = int(math.ceil((indices[1]+indices[0]+1)/2.0))

                    # print indices ,mid
                    if len(months) == 2:
                        month_with_smallest_length = min(months, text.rindex)
                        diff = len(months[0]) - len(months[1])
                        # mid +=diff 
                        if len(months[0]) > len(months[1]):
                            mid = mid + abs(diff) - 1
                        if len(months[0]) < len(months[1]):
                            mid = mid - abs(diff) + 1
                    # print text, mid

                    for string in itertools.chain(digits, months):
                        # print string
                        curr_end_idx = text.rindex(string) + len(string)
                        if  curr_end_idx <= mid and curr_end_idx > prev:
                            prev = curr_end_idx
                    if prev == 0:
                        prev = mid
                    text = text[: prev] + ' to ' + text[prev: ]
                    # print text
            except Exception as e:
                # print e
                pass
        return text
    
    def extract_date_strings(self, text):
        # print text
        text = self.add_period_delimiter(text)
        for match in self.DATE_REGEX.finditer(text):
            match_str = match.group(0)
            indices = match.span(0)
            captures = match.capturesdict()
            digits = captures.get('digits')
            # print digits
            digits_modifiers = captures.get('digits_modifiers')
            months = captures.get('months')
            delimiters = captures.get('delimiters')
            extra_tokens = captures.get('extra_tokens')
            match_str = re.sub('[\n\t\s\xa0]+', ' ', match_str)
            match_str = match_str.strip(self.STRIP_CHARS)
            # print match_str, indices, captures
            if len(months) == 1 and len(digits) == 1 and len(str(digits[0])) == 2:
                # print match_str
                if int(digits[0]) <= date.today().year%1000:
                    match_str = match_str.replace(digits[0], str(date.today().year/100) + digits[0])
                    digits[0] = str(date.today().year/100) + digits[0]

                else:
                    # print match_str
                    match_str = match_str.replace(digits[0], str((date.today().year - 100)/100) + digits[0])
                    digits[0] = str((date.today().year - 1000)/100) + digits[0]
            # elif len(digits) == 2 and all(map(lambda x: len(str(x)) == 2)
            # print text
            # print match_str, indices, captures
            yield match_str, indices, captures
    
    @staticmethod
    def get_period(datetime1, datetime2=None, in_days = False, in_years = True):
        if not datetime2:
            return None
        diff = datetime2 - datetime1
        if in_days:
            return diff.days
        return round(diff.days/365.25, 2)


if __name__ == '__main__':

    # return date_finder.find_dates(text)

    test_cases = [
        'worked from 10 may 00 to present',
        '10/July',
        'July/99 to July/99',
        '10/2016',
        # '10/16', # this is interpreted as mm/dd
        '10-July-00',
        '10-July 00 - 1-June 02',
        'July-2017',
        '10 July, 2000',
        '10th July, 2000',
        'July, 2000',
        "July 15",
        '04 2000 02 2001',
        'April 2014',
        'Duration: May 2013 - June 2014',
        'Accenture(Oct 2012 - Present)',
        'Barclays 1/2/12 - 12/12/13',
        "Worked from June'14 to June'15",
        "June'13 - till date",
        "period Nov 2014 October 2016",
        "period : October 2012 Nov 2014",
        "worked duration may 2011  december 2012",
        "may'12 - december'13",
        "december 12 may 17",
        "<foobar> (oct 2013 to december 2014) </foobar>"

        ]

    df = DateFinder(base_date=datetime.datetime(2000, 01, 01, 0, 0))
    # print map(DateFinder(base_date=datetime.datetime(2000, 01, 01, 0, 0)).find_dates, test_cases)
    for string in test_cases:
        dates = df.find_dates(string)
        
        print string, ' : ', map(lambda x: x.strftime('%d-%m-%Y'), dates), ' : ' , DateFinder.get_period(*dates), 'years'

        

    # print DateFinder.get_period(*DateFinder(base_date=datetime.datetime(2000, 01, 01, 0, 0)).find_dates(test_cases[0]))
    # df = DateFinder(base_date=None)
    # dates = df.find_dates("worked from 22nd october 2001 to 12th may 2003")
    # print 'period(years): ', DateFinder.get_period(*dates)
    # dates = df.find_dates("worked from oct 2002 to nov 2003")
    # print 'period(years): ', DateFinder.get_period(*dates)
    # dates = df.find_dates("oct 2002 - nov 2003")
    # print 'period(years): ', DateFinder.get_period(*dates)
    # dates = df.find_dates("12/12/2002 - 12/12/2003")
    # print 'period(years): ', DateFinder.get_period(*dates)
# print map(list,map(find_dates, dates))





